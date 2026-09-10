import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/ai-disclosure/scripts"))
from test_tooling import load, ROOT

publisher = load("publisher", ROOT / "skills/ai-disclosure/scripts/site.py")

ARTICLE = '<article data-ai-content="article"><h1>Town news</h1><!-- ai-disclosure --><p>A new park.</p></article>'
IMAGE = '<figure class="aid-media" data-ai-content="image"><!-- ai-disclosure --><img src="park.svg" alt="An imagined park"></figure>'


class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "public"
        self.root.mkdir()
        self.manifest = self.base / "facts.json"
        self.output = self.base / "published"
        self.write(ARTICLE)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, body):
        (self.root / "index.html").write_text('<!doctype html><html><head><title>Example</title></head><body>' + body + '</body></html>')

    def facts(self, overrides=None):
        records = publisher.inventory(self.root)[1]["records"]
        items = [{"id": r["id"], "revision": r["revision"], "kind": "text" if r["tag"] == "article" else "image",
                  "origin": "ai_generated", "applicable": True, "evidence": "Generation hook and publisher context",
                  "public_interest": True, "deepfake": True} for r in records]
        if overrides:
            items[0].update(overrides)
        data = {"version": 1, "role": "publisher", "items": items}
        self.manifest.write_text(json.dumps(data))
        return data

    def test_build_renders_local_labels_and_keeps_evidence_private(self):
        self.write(ARTICLE + IMAGE)
        self.facts()
        before = (self.root / "index.html").read_bytes()
        result = publisher.build(self.root, self.manifest, self.output)
        self.assertTrue(result["ready_to_render"])
        self.assertFalse(result["implementation_verified"])
        rendered = (self.output / "index.html").read_text()
        self.assertEqual(rendered.count('class="aid-notice"'), 2)
        self.assertNotIn("<!-- ai-disclosure -->", rendered)
        self.assertNotIn("Generation hook", rendered)
        self.assertTrue((self.output / "ai-disclosure.css").is_file())
        self.assertFalse((self.output / "facts.json").exists())
        self.assertEqual((self.root / "index.html").read_bytes(), before)

    def test_current_review_omits_label_but_content_change_blocks(self):
        data = self.facts()
        item = data["items"][0]
        item["review"] = {"revision": item["revision"], "substantive_human_review": True, "responsible_entity": "Publisher"}
        self.manifest.write_text(json.dumps(data))
        report, edits = publisher.plan(self.root, self.manifest)
        self.assertEqual(report["results"][0]["status"], "exception_declared")
        self.assertNotIn('class="aid-notice"', edits["index.html"])
        self.write(ARTICLE.replace("A new park.", "An unreviewed claim."))
        result = publisher.build(self.root, self.manifest, self.output)
        self.assertFalse(result["ready_to_render"])
        self.assertEqual(result["results"][0]["status"], "disclose")
        self.assertFalse(self.output.exists())

    def test_unknown_facts_do_not_publish(self):
        self.facts({"origin": "unknown"})
        self.assertFalse(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])
        self.assertFalse(self.output.exists())

    def test_unbound_media_inside_article_is_detected(self):
        self.write(ARTICLE.replace('</article>', '<img src="fake.jpg" alt="News photo"></article>'))
        found = publisher.inventory(self.root)[1]
        self.assertEqual(found["gaps"][0]["tag"], "img")

    def test_decorative_exclusion_is_explicit(self):
        self.write(ARTICLE + '<img src="icon.svg" alt="" data-ai-ignore="decorative">')
        found = publisher.inventory(self.root)[1]
        self.assertFalse(found["gaps"])
        self.assertEqual(len(found["exclusions"]), 1)

    def test_late_and_duplicate_slots_block_publication(self):
        for body in (ARTICLE.replace('<!-- ai-disclosure -->', '') + '<!-- ai-disclosure -->',
                     ARTICLE.replace('<!-- ai-disclosure -->', '<!-- ai-disclosure --><!-- ai-disclosure -->'),
                     ARTICLE.replace('<!-- ai-disclosure --><p>A new park.</p>', '<p>A new park.</p><!-- ai-disclosure -->')):
            with self.subTest(body=body):
                self.write(body)
                self.facts()
                self.assertFalse(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])
                self.assertFalse(self.output.exists())

    def test_existing_output_is_preserved(self):
        self.facts()
        self.output.mkdir()
        (self.output / "keep.txt").write_text("Existing deployment")
        with self.assertRaises(ValueError):
            publisher.build(self.root, self.manifest, self.output)
        self.assertEqual((self.output / "keep.txt").read_text(), "Existing deployment")

    def test_output_inside_source_rejected(self):
        self.facts()
        with self.assertRaises(ValueError):
            publisher.build(self.root, self.manifest, self.root / "nested")

    def test_source_symlink_rejected(self):
        (self.root / "external.html").symlink_to(self.base / "private.html")
        with self.assertRaises(ValueError):
            publisher.inventory(self.root)

    def test_id_with_html_payload_rejected(self):
        self.write(ARTICLE.replace('data-ai-content="article"', 'data-ai-content="bad&amp;quot;id"'))
        with self.assertRaises(ValueError):
            publisher.inventory(self.root)

    def test_nested_page_gets_correct_stylesheet_path(self):
        self.facts()
        nested = self.root / "news"
        nested.mkdir()
        (self.root / "index.html").rename(nested / "index.html")
        report = publisher.build(self.root, self.manifest, self.output)
        self.assertTrue(report["ready_to_render"])
        self.assertIn('href="../ai-disclosure.css"', (self.output / "news/index.html").read_text())

    def test_generation_hook_refreshes_revision_without_inheriting_review(self):
        data = self.facts()
        item = data["items"][0]
        item["review"] = {"revision": item["revision"], "substantive_human_review": True, "responsible_entity": "Publisher"}
        self.manifest.write_text(json.dumps(data))
        self.write(ARTICLE.replace("A new park.", "A changed article."))
        facts_path = self.base / "new-facts.json"
        facts = {k: v for k, v in item.items() if k not in {"revision", "review"}}
        facts_path.write_text(json.dumps(facts))
        update = publisher.record(self.root, self.manifest, facts_path)
        self.assertTrue(update["changed"])
        stored = json.loads(self.manifest.read_text())["items"][0]
        self.assertNotIn("review", stored)
        self.assertNotEqual(stored["revision"], item["revision"])
        self.assertFalse(publisher.record(self.root, self.manifest, facts_path)["changed"])
        self.assertTrue(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])

    def test_record_cannot_put_private_facts_in_public_input(self):
        facts_path = self.base / "input.json"
        facts_path.write_text('{}')
        with self.assertRaises(ValueError):
            publisher.record(self.root, self.root / "facts.json", facts_path)


if __name__ == "__main__":
    unittest.main()
