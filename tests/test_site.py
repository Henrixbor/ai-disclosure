import json
import base64
import re
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

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
        (self.root / "park.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><title>Test artwork</title></svg>')
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
        self.assertTrue(any(gap.get("tag") == "img" for gap in found["gaps"]))

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

    def test_content_changed_during_staging_is_not_published(self):
        self.facts()
        copytree = publisher.shutil.copytree
        def changed_copy(*args, **kwargs):
            self.write(ARTICLE.replace("A new park.", "Changed during copy."))
            return copytree(*args, **kwargs)
        with patch.object(publisher.shutil, "copytree", side_effect=changed_copy):
            self.assertFalse(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.base.glob(".ai-disclosure-*")))

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

    def test_replaced_media_bytes_invalidate_unchanged_html(self):
        self.write(IMAGE)
        self.facts()
        before = (self.root / "index.html").read_bytes()
        (self.root / "park.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><title>Different picture</title></svg>')
        result = publisher.build(self.root, self.manifest, self.output)
        self.assertEqual((self.root / "index.html").read_bytes(), before)
        self.assertFalse(result["ready_to_render"])
        self.assertFalse(self.output.exists())

    def test_external_and_missing_media_do_not_get_verified_revisions(self):
        for url in ('https://example.com/park.svg', '../private.svg', 'missing.svg'):
            with self.subTest(url=url):
                self.write(IMAGE.replace('park.svg', url))
                self.assertTrue(publisher.inventory(self.root)[1]["gaps"])

    def fragment_facts(self, source, kind="text", **facts):
        records = publisher.fragment_inventory(self.root, source)[1]["records"]
        return {"version": 1, "role": "publisher", "items": [
            {"id": r["id"], "revision": r["revision"], "kind": kind, "origin": "ai_generated",
             "applicable": True, "public_interest": True, "evidence": "CMS generation transaction", **facts}
            for r in records]}

    def test_fragment_render_is_pure_and_preserves_declared_input(self):
        facts = self.fragment_facts(ARTICLE)
        before = json.dumps(facts, sort_keys=True)
        files = sorted(str(p) for p in self.root.rglob("*"))
        rendered = publisher.render_fragment(self.root, ARTICLE, facts)
        self.assertIn('class="aid-notice"', rendered["html"])
        self.assertNotIn('<head>', rendered["html"])
        self.assertNotIn('CMS generation transaction', rendered["html"])
        self.assertEqual(json.dumps(facts, sort_keys=True), before)
        self.assertEqual(sorted(str(p) for p in self.root.rglob("*")), files)
        self.assertEqual(rendered["assets"]["ai-disclosure.css"], publisher.STYLE)

    def test_stale_fragment_or_missing_facts_returns_no_publishable_html(self):
        facts = self.fragment_facts(ARTICLE)
        changed = ARTICLE.replace("A new park.", "New claim.")
        result = publisher.render_fragment(self.root, changed, facts)
        self.assertIsNone(result["html"])
        self.assertFalse(result["assets"])
        facts["items"][0]["origin"] = "unknown"
        self.assertIsNone(publisher.render_fragment(self.root, ARTICLE, facts)["html"])

    def test_refreshed_fragment_requires_new_review_for_exemption(self):
        facts = self.fragment_facts(ARTICLE)
        facts["items"][0]["review"] = {"revision": facts["items"][0]["revision"],
            "substantive_human_review": True, "responsible_entity": "Editor"}
        changed = ARTICLE.replace("A new park.", "New claim.")
        fresh = self.fragment_facts(changed)
        fresh["items"][0]["review"] = facts["items"][0]["review"]
        result = publisher.render_fragment(self.root, changed, fresh)
        self.assertEqual(result["report"]["results"][0]["status"], "disclose")
        self.assertIn('class="aid-notice"', result["html"])

    def test_document_export_embeds_unchanged_image_and_local_notices(self):
        image = IMAGE.replace('park.svg', 'green.png')
        original = (ROOT / "tests/fixtures/green.png").read_bytes()
        (self.root / "green.png").write_bytes(original)
        facts = self.fragment_facts(image, "image", deepfake=True)
        result = publisher.export_document(self.root, image, facts, "Example export", "en")
        self.assertIn('<title>Example export</title>', result["html"])
        self.assertIn('class="aid-notice"', result["html"])
        encoded = re.search(r'src="data:image/png;base64,([^"]+)"', result["html"]).group(1)
        self.assertEqual(base64.b64decode(encoded), original)
        self.assertEqual((self.root / "green.png").read_bytes(), original)
        self.assertNotIn('<script', result["html"])
        self.assertNotIn('<link', result["html"])
        self.assertNotIn('CMS generation transaction', result["html"])

    def test_image_changed_during_export_is_rejected(self):
        image = IMAGE.replace('park.svg', 'green.png')
        target = self.root / "green.png"
        target.write_bytes((ROOT / "tests/fixtures/green.png").read_bytes())
        facts = self.fragment_facts(image, "image", deepfake=True)
        render = publisher.render_document
        def changed_render(*args):
            target.write_bytes(target.read_bytes() + b"changed")
            return render(*args)
        with patch.object(publisher, "render_document", side_effect=changed_render):
            with self.assertRaisesRegex(ValueError, "changed during export"):
                publisher.export_document(self.root, image, facts, "Title", "en")

    def test_document_export_holds_stale_facts(self):
        facts = self.fragment_facts(ARTICLE)
        result = publisher.export_document(self.root, ARTICLE.replace("A new park.", "Changed."), facts, "Title", "en")
        self.assertIsNone(result["html"])

    def test_document_export_rejects_active_hidden_and_unsupported_content(self):
        for addition in ('<script>alert(1)</script>', '<iframe src="https://example.com"></iframe>',
                         '<p hidden>Hidden text</p>', '<p style="display:none">Hidden text</p>'):
            source = ARTICLE.replace('</article>', addition+'</article>')
            facts = self.fragment_facts(source)
            try:
                result = publisher.export_document(self.root, source, facts, "Title", "en")
                self.assertIsNone(result["html"])
            except ValueError:
                pass
        source = ARTICLE.replace('<p>', '<p onclick="alert(1)">')
        result = publisher.export_document(self.root, source, self.fragment_facts(source), "<Title>", "en")
        self.assertNotIn('onclick', result["html"])
        self.assertIn('&lt;Title&gt;', result["html"])

    def test_document_export_does_not_reuse_interaction_notice_for_transcript(self):
        source = '<section class="aid-chat" data-ai-content="chat"><!-- ai-disclosure --><p>Conversation</p></section>'
        facts = self.fragment_facts(source, "chatbot", direct_ai_interaction=True)
        with self.assertRaises(ValueError):
            publisher.export_document(self.root, source, facts, "Transcript", "en")

    def test_fragment_cli_success_and_stale_exit_codes(self):
        source = self.base / "component.html"
        source.write_text(ARTICLE)
        self.manifest.write_text(json.dumps(self.fragment_facts(ARTICLE)))
        command = [sys.executable, str(ROOT / "skills/ai-disclosure/scripts/site.py"),
                   "render-fragment", "--root", str(self.root), "--html", str(source),
                   "--manifest", str(self.manifest)]
        good = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertIn('class="aid-notice"', json.loads(good.stdout)["html"])
        source.write_text(ARTICLE.replace("A new park.", "Changed claim."))
        stale = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(stale.returncode, 1, stale.stderr)
        self.assertIsNone(json.loads(stale.stdout)["html"])

    def test_fragment_asset_change_and_invalid_boundaries(self):
        facts = self.fragment_facts(IMAGE, "image", deepfake=True)
        (self.root / "park.svg").write_text("Changed asset")
        self.assertIsNone(publisher.render_fragment(self.root, IMAGE, facts)["html"])
        for source in (ARTICLE + ARTICLE, "unbound" + ARTICLE, '<div>Unbound</div>'):
            with self.assertRaises(ValueError):
                publisher.fragment_inventory(self.root, source)
        for page in ('../private.html', '/index.html', 'https://example.com/index.html'):
            with self.assertRaises(ValueError):
                publisher.fragment_inventory(self.root, ARTICLE, page)

    def test_chat_notice_precedes_conversation_without_javascript(self):
        self.write('<section class="aid-chat" data-ai-content="chat"><h2>Support</h2><!-- ai-disclosure -->'
                   '<div role="log">Conversation</div><form><label>Message<textarea></textarea></label></form></section>')
        self.facts({"kind": "chatbot", "direct_ai_interaction": True})
        self.assertTrue(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])
        rendered = (self.output / "index.html").read_text()
        self.assertIn("You are interacting with AI.", rendered)
        self.assertLess(rendered.index("You are interacting"), rendered.index('role="log"'))
        self.assertNotIn('<script', rendered)

    def test_chat_notice_after_composer_is_rejected(self):
        self.write('<section class="aid-chat" data-ai-content="chat"><textarea></textarea><!-- ai-disclosure --></section>')
        self.facts({"kind": "chatbot", "direct_ai_interaction": True})
        self.assertFalse(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])
        self.assertFalse(self.output.exists())

    def media_fixture(self, kind="audio", notice=True):
        (self.root / "recording.wav").write_bytes(b"test recording")
        (self.root / "notice.wav").write_bytes(b"test notice")
        attr = ' data-ai-notice-src="notice.wav"' if notice else ''
        self.write('<figure class="aid-media" data-ai-content="recording"><!-- ai-disclosure -->'
                   + '<' + kind + ' src="recording.wav"' + attr + '></' + kind + '></figure>')
        self.facts({"kind": kind, "audio_deepfake": True})

    def test_audio_build_defers_content_until_runtime_disclosure(self):
        self.media_fixture()
        result = publisher.build(self.root, self.manifest, self.output)
        self.assertTrue(result["ready_to_render"])
        rendered = (self.output / "index.html").read_text()
        self.assertIn('data-source="recording.wav"', rendered)
        self.assertIn('data-notice="notice.wav"', rendered)
        self.assertNotIn('<audio src=', rendered)
        self.assertIn('<noscript>', rendered)
        self.assertTrue((self.output / "ai-disclosure-players.js").is_file())

    def test_caption_tracks_preserved_and_versioned(self):
        self.media_fixture()
        (self.root / "captions.vtt").write_text("WEBVTT\n\n00:00.000 --> 00:01.000\nCaption\n")
        source = (self.root / "index.html").read_text().replace('</audio>',
                  '<track kind="captions" src="captions.vtt" srclang="en" label="English" default></audio>')
        (self.root / "index.html").write_text(source)
        self.facts({"kind": "audio"})
        result = publisher.build(self.root, self.manifest, self.output)
        self.assertTrue(result["ready_to_render"])
        rendered = (self.output / "index.html").read_text()
        self.assertIn('src="captions.vtt"', rendered)
        self.assertIn('data-aid-captions', rendered)
        (self.root / "captions.vtt").write_text("WEBVTT\n\n00:00.000 --> 00:01.000\nChanged caption\n")
        self.assertFalse(publisher.plan(self.root, self.manifest)[0]["ready_to_render"])

    def test_unsupported_track_is_reported_instead_of_stripped(self):
        self.media_fixture()
        (self.root / "captions.vtt").write_text("WEBVTT\n")
        path = self.root / "index.html"
        path.write_text(path.read_text().replace('</audio>',
            '<track kind="descriptions" src="captions.vtt" srclang="en" label="Description"></audio>'))
        self.facts({"kind": "audio"})
        self.assertFalse(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])
        self.assertFalse(self.output.exists())

    def test_required_spoken_notice_missing_blocks_build(self):
        for kind in ("audio", "video"):
            with self.subTest(kind=kind):
                self.media_fixture(kind, notice=False)
                self.assertFalse(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])
                self.assertFalse(self.output.exists())

    def test_video_audio_context_must_be_declared(self):
        self.media_fixture("video")
        data = json.loads(self.manifest.read_text())
        del data["items"][0]["audio_deepfake"]
        self.manifest.write_text(json.dumps(data))
        self.assertFalse(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])

    def test_replacing_spoken_notice_invalidates_revision(self):
        self.media_fixture()
        (self.root / "notice.wav").write_bytes(b"different notice")
        self.assertFalse(publisher.build(self.root, self.manifest, self.output)["ready_to_render"])


if __name__ == "__main__":
    unittest.main()
