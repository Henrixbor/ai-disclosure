import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSESS = ROOT / "skills/ai-disclosure/scripts/assess.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


policy = load("policy", ASSESS)
installer = load("installer", ROOT / "scripts/install.py")


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.item = {"id": "/article", "revision": "v2", "kind": "text",
                     "origin": "ai_generated", "applicable": True,
                     "public_interest": True, "evidence": "Publisher's CMS record"}

    def assess(self, **updates):
        item = copy.deepcopy(self.item)
        item.update(updates)
        result = policy.assess({"version": 1, "role": "publisher", "items": [item]})
        self.assertFalse(result["implementation_verified"])
        self.assertFalse(result["inventory_completeness_verified"])
        return result["results"][0]

    def test_public_interest_text_gets_publication_label(self):
        self.assertEqual(self.assess()["status"], "disclose")

    def test_human_text_does_not_inherit_code_authorship(self):
        self.assertEqual(self.assess(origin="human")["status"], "no_publisher_label")
        self.assertEqual(self.assess(kind="code")["status"], "no_publisher_label")

    def test_unknown_facts_remain_unresolved(self):
        for update in ({"origin": "unknown"}, {"applicable": None}, {"public_interest": None}):
            with self.subTest(update=update):
                self.assertEqual(self.assess(**update)["status"], "needs_review")

    def test_scope_exemption_requires_evidence(self):
        item = dict(self.item, applicable=False)
        del item["evidence"]
        self.assertEqual(policy.decide(item)["status"], "needs_review")
        self.assertEqual(self.assess(applicable=False)["status"], "outside_declared_scope")

    def test_review_is_bound_to_current_version(self):
        review = {"revision": "v2", "substantive_human_review": True,
                  "responsible_entity": "Publisher"}
        self.assertEqual(self.assess(review=review)["status"], "exception_declared")
        self.assertEqual(self.assess(review=review, revision="v3")["status"], "disclose")
        review["substantive_human_review"] = False
        self.assertEqual(self.assess(review=review)["status"], "disclose")

    def test_non_public_interest_text(self):
        self.assertEqual(self.assess(public_interest=False)["status"], "no_publisher_label")

    def test_media_modalities_and_creative_work_still_disclose(self):
        for kind in ("image", "audio", "video"):
            for creative in (False, True):
                with self.subTest(kind=kind, creative=creative):
                    self.assertEqual(self.assess(kind=kind, deepfake=True,
                                                creative_work=creative)["status"], "disclose")
        self.assertEqual(self.assess(kind="image")["status"], "needs_review")
        self.assertEqual(self.assess(kind="image", deepfake=False)["status"], "no_publisher_label")

    def test_unsupported_and_chatbot_require_separate_assessment(self):
        for kind in ("other", "chatbot"):
            self.assertEqual(self.assess(kind=kind)["status"], "needs_review")

    def test_chat_interaction_requires_explicit_evidence_and_scope(self):
        self.assertEqual(self.assess(kind="chatbot", direct_ai_interaction=True)["status"], "disclose")
        for facts in ({"direct_ai_interaction": False}, {"direct_ai_interaction": None},
                      {"direct_ai_interaction": True, "applicable": None}):
            self.assertEqual(self.assess(kind="chatbot", **facts)["status"], "needs_review")
        with self.assertRaises(ValueError):
            self.assess(kind="chatbot", direct_ai_interaction="true")

    def test_provider_role_never_looks_complete(self):
        for role in ("provider", "both", "unknown"):
            result = policy.assess({"version": 1, "role": role, "items": [self.item]})
            self.assertTrue(result["role_gaps"])

    def test_invalid_inputs_fail(self):
        base = {"version": 1, "role": "publisher", "items": [self.item]}
        invalid = [dict(base, items=[]), dict(base, version=True),
                   dict(base, items=[self.item, self.item]),
                   dict(base, items=[dict(self.item, applicable="false")]),
                   dict(base, items=[dict(self.item, public_interst=False)]),
                   dict(base, items=[dict(self.item, evidence=" ")])]
        for data in invalid:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    policy.assess(data)

    def test_cli_exit_codes_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            cases = [(self.item, 0), (dict(self.item, origin="unknown"), 1),
                     (dict(self.item, applicable="false"), 2)]
            for item, code in cases:
                path.write_text(json.dumps({"version": 1, "role": "publisher", "items": [item]}))
                before = path.read_bytes()
                proc = subprocess.run([sys.executable, str(ASSESS), str(path)], capture_output=True, text=True)
                self.assertEqual(proc.returncode, code, proc.stderr)
                json.loads(proc.stderr if code == 2 else proc.stdout)
                self.assertEqual(path.read_bytes(), before)


class InstallationTests(unittest.TestCase):
    def test_both_hosts_and_repeated_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            targets = installer.install(root, "both")
            self.assertEqual(len(targets), 2)
            expected = installer.files(installer.SOURCE)
            for target in targets:
                self.assertEqual(installer.files(target), expected)
            self.assertEqual(installer.install(root, "both"), targets)
            # Run the copied tool without relying on the source repository.
            proc = subprocess.run([sys.executable, str(targets[0] / "scripts/assess.py"), "--help"],
                                  capture_output=True)
            self.assertEqual(proc.returncode, 0)

    def test_custom_skill_is_not_overwritten_and_other_host_not_partially_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = installer.install(root, "claude")[0]
            (target / "SKILL.md").write_text("Local customisation")
            with self.assertRaises(ValueError):
                installer.install(root, "both")
            self.assertEqual((target / "SKILL.md").read_text(), "Local customisation")
            self.assertFalse((root / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
