#!/usr/bin/env python3
"""Build reproducible skill, agent-plugin or WordPress archives without development files."""
import argparse
import hashlib
import io
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills/ai-disclosure"


def package(source=SOURCE, kind="skill", repository=ROOT):
    if kind == "wordpress":
        source = repository / "integrations/wordpress"
        required = {"ai-disclosure.php", "policy.php", "editor.php", "withdrawal.php",
                    "inventory.php", "publication.php", "cache.php", "editor.js",
                    "editor.css", "notice.css", "LICENSE", "readme.txt"}
        if source.parent.is_symlink() or source.is_symlink() or any(p.is_symlink() for p in source.rglob("*")):
            raise ValueError("WordPress packages must not contain symlinks")
        for name in required:
            if not (source / name).is_file():
                raise ValueError("Missing required WordPress file: " + name)
        return archive_files({"ai-disclosure/" + name: source / name for name in required})
    if kind not in {"skill", "plugin"}:
        raise ValueError("Unknown package format")
    required = {"SKILL.md", "LICENSE", "references/rules.md", "references/manifest.md",
                "references/publishing.md", "scripts/assess.py", "scripts/site.py", "assets/players.js", "scripts/exports.py",
                "scripts/bridge.py", "scripts/node.cjs"}
    if any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("Skill packages must not contain symlinks")
    for name in required:
        if not (source / name).is_file():
            raise ValueError("Missing required skill file: " + name)
    prefix = "ai-disclosure/" if kind == "skill" else "ai-disclosure/skills/ai-disclosure/"
    files = {prefix + name: source / name for name in required}
    if kind == "plugin":
        for path, target in {".codex-plugin/plugin.json": ".codex-plugin/plugin.json",
                             ".claude-plugin/plugin.json": ".claude-plugin/plugin.json",
                             "LICENSE": "LICENSE", "docs/plugin-readme.md": "README.md"}.items():
            source_path = repository / path
            if not source_path.is_file() or source_path.is_symlink():
                raise ValueError("Missing or symlinked plugin file: " + path)
            files["ai-disclosure/" + target] = source_path
    return archive_files(files)


def archive_files(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name].read_bytes())
    payload = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive CRC verification failed")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["skill", "plugin", "wordpress"], default="skill")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if any(source.resolve() in args.output.resolve().parents for source in
               [SOURCE, ROOT / "integrations/wordpress"]):
            raise ValueError("Do not write release archives into package source directories")
        if args.output.is_symlink():
            raise ValueError("Output must not be a symlink")
        payload = package(kind=args.format)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists() and args.output.read_bytes() != payload:
            raise ValueError("Existing archive differs; choose a new output path")
        args.output.write_bytes(payload)
        print(hashlib.sha256(payload).hexdigest() + "  " + args.output.name)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
