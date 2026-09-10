#!/usr/bin/env python3
"""Install the portable AI disclosure skill into a project's agent skill folders."""
import argparse
import shutil
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "skills" / "ai-disclosure"


def files(path):
    return {p.relative_to(path): p.read_bytes() for p in path.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def install(project, agent):
    if not project.is_dir():
        raise ValueError("Project must be an existing directory")
    project = project.resolve()
    roots = {"codex": ".agents", "claude": ".claude"}
    selected = roots if agent == "both" else {agent: roots[agent]}
    targets = [project / root / "skills" / "ai-disclosure" for root in selected.values()]
    expected = files(SOURCE)
    # Preflight all destinations before writing any, preserving local customisations.
    for target in targets:
        if any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError("Refusing a symlinked installation path: " + str(target))
        if target.exists() and (not target.is_dir() or files(target) != expected):
            raise ValueError("Existing skill differs; review it before updating: " + str(target))
    for target in targets:
        if not target.exists():
            shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--agent", choices=("codex", "claude", "both"), default="both")
    args = parser.parse_args()
    try:
        for target in install(args.project.absolute(), args.agent):
            print("Installed or already identical: " + str(target))
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
