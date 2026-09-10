#!/usr/bin/env python3
"""Build the product demo through the actual disclosure adapter."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/ai-disclosure/scripts"))
spec = importlib.util.spec_from_file_location("publishing", ROOT / "skills/ai-disclosure/scripts/site.py")
publishing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publishing)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    # This build hook attests only the known AI-authored demonstration source.
    # It is not a generic origin inference or a substitute for customer evidence.
    with tempfile.TemporaryDirectory() as temporary:
        manifest = Path(temporary) / "manifest.json"
        records = publishing.inventory(ROOT / "web")[1]["records"]
        manifest.write_text(json.dumps({"version": 1, "role": "publisher", "items": [
            {"id": record["id"], "revision": record["revision"], "kind": "text",
             "origin": "ai_generated", "applicable": True, "public_interest": True,
             "evidence": "Known AI-authored website documentation and fictional demonstration text; disclosed conservatively."}
            for record in records
        ]}))
        result = publishing.build(ROOT / "web", manifest, args.output)
        print(json.dumps(result, indent=2))
        return int(not result["ready_to_render"])


if __name__ == "__main__":
    sys.exit(main())
