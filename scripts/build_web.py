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


def build_showcase_outputs(output):
    """Precompute honest demo transactions and a real portable HTML export."""
    source = '<article data-ai-content="publishing-example"><h3>A fictional waterfront update.</h3><!-- ai-disclosure --><p>The garden opens for a fictional preview on Saturday.</p></article>'
    def facts(fragment):
        return {"version": 1, "role": "publisher", "items": [
            {"id": row["id"], "revision": row["revision"], "kind": "image" if row["tag"] == "figure" else "text",
             "origin": "ai_generated", "applicable": True, "public_interest": True, "deepfake": False,
             "evidence": "Known AI-authored fictional showcase; generated image voluntarily labeled; text conservatively disclosed"}
            for row in publishing.fragment_inventory(ROOT / "web", fragment)[1]["records"]]}
    changed = source.replace("on Saturday", "on Sunday, with an extended afternoon session")
    recorded = publishing.render_fragment(ROOT / "web", changed, facts(changed))
    stale = publishing.render_fragment(ROOT / "web", changed, facts(source))
    assert recorded["html"] is not None and stale["html"] is None
    (output / "publishing-demo.json").write_text(json.dumps({
        "recorded": {"html": recorded["html"]}, "stale": {"html": stale["html"]}}))
    document = '<article data-ai-content="field-note"><h1>A place that exists only in imagination.</h1><!-- ai-disclosure --><p>This fictional field note and its illustration were created with AI. The pavilion is not a real destination.</p><figure class="aid-media" data-ai-content="field-image"><!-- ai-disclosure --><figcaption>AI-generated image — fictional coastal pavilion. Voluntary origin notice.</figcaption><img src="assets/pavilion.png" alt="AI-generated fictional limestone pavilion beside a blue sea"></figure><p>The image, notices and styling are embedded in this HTML document. Save it and open it offline to inspect the result.</p></article>'
    exported = publishing.export_document(ROOT / "web", document, facts(document), "AI Disclosure — portable field note", "en")
    assert exported["html"] is not None
    (output / "field-note.html").write_text(exported["html"], encoding="utf-8")


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
        if result["ready_to_render"]:
            build_showcase_outputs(args.output)
        print(json.dumps(result, indent=2))
        return int(not result["ready_to_render"])


if __name__ == "__main__":
    sys.exit(main())
