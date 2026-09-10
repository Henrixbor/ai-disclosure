#!/usr/bin/env python3
"""Build a reproducible standalone Agent Skill archive, excluding development files."""
import argparse
import hashlib
import io
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills/ai-disclosure"


def package(source=SOURCE):
    required = {"SKILL.md", "LICENSE", "references/rules.md", "references/manifest.md",
                "references/publishing.md", "scripts/assess.py", "scripts/site.py", "assets/players.js"}
    if any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("Skill packages must not contain symlinks")
    for name in required:
        if not (source / name).is_file():
            raise ValueError("Missing required skill file: " + name)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(required):
            info = zipfile.ZipInfo("ai-disclosure/" + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (source / name).read_bytes())
    payload = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive CRC verification failed")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if SOURCE.resolve() in args.output.resolve().parents:
            raise ValueError("Do not write release archives into the skill source")
        payload = package()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists() and args.output.read_bytes() != payload:
            raise ValueError("Existing archive differs; choose a new output path")
        args.output.write_bytes(payload)
        print(hashlib.sha256(payload).hexdigest() + "  " + args.output.name)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
