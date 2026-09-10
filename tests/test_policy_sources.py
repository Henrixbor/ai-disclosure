import copy
import hashlib
import unittest
from test_tooling import load, ROOT

checker = load('source_checker', ROOT / 'scripts/check_policy_sources.py')


class PolicySourceTests(unittest.TestCase):
    def test_changed_document_requires_review_without_rewriting_baseline(self):
        known = b'%PDF known policy'
        registry = {'checked_on': '2026-09-10', 'sources': [
            {'id': 'source', 'url': 'https://example.invalid/policy', 'sha256': hashlib.sha256(known).hexdigest()}],
            'unverified': [{'url': 'https://example.invalid/law', 'reason': 'Not retrieved'}]}
        before = copy.deepcopy(registry)
        self.assertEqual(checker.check(registry, lambda url: known)['sources'][0]['status'], 'unchanged')
        changed = checker.check(registry, lambda url: b'%PDF changed policy')
        self.assertEqual(changed['sources'][0]['status'], 'changed')
        self.assertEqual(changed['unverified'], registry['unverified'])
        self.assertEqual(registry, before)

    def test_unavailable_source_is_not_reported_unchanged(self):
        def failed(url):
            raise TimeoutError('Source unavailable')
        registry = {'checked_on': '2026-09-10', 'sources': [{'id': 'source', 'url': 'https://example.invalid', 'sha256': '0' * 64}]}
        self.assertEqual(checker.check(registry, failed)['sources'][0]['status'], 'unavailable')

    def test_empty_registry_cannot_pass(self):
        with self.assertRaises(ValueError):
            checker.check({'checked_on': '2026-09-10', 'sources': []})
