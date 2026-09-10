import copy
import json
from pathlib import Path
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest

from test_tooling import load, ROOT

migration = load('wp_migration', ROOT / 'scripts/wordpress_migrate.py')
REV = 'sha256:' + 'a' * 64
ITEM = {'id': 7, 'revision': REV, 'facts': {'origin': 'ai_generated', 'applicable': True,
        'public_interest': True, 'evidence': 'PRIVATE_MIGRATION_EVIDENCE'}}


class FakeClient:
    def __init__(self, current=None, post=None):
        self.calls = []
        self.current = current or {'revision': REV, 'policy': migration.policy.POLICY,
                                  'supported_text': True, 'recorded': False, 'assessment': None}
        self.post = post or (200, {'revision': REV, 'policy': migration.policy.POLICY,
                                  'decision': 'disclose', 'record_id': 'b' * 64})

    def request(self, method, post_id, body=None):
        self.calls.append((method, post_id, body))
        return (200, self.current) if method == 'GET' else self.post


class MigrationTests(unittest.TestCase):
    def inventory_client(self, pages):
        class InventoryClient:
            def __init__(self):
                self.calls = []
            def inventory(self, after, limit, through_id):
                self.calls.append((after, limit, through_id))
                return pages[len(self.calls) - 1]
        return InventoryClient()

    def inventory_page(self, items, next_after=None, boundary=7):
        return 200, {'policy': migration.policy.POLICY, 'coverage': 'post-page-source-only',
                     'items': items, 'next_after': next_after, 'through_id': boundary}

    def inventory_item(self, post_id=7):
        return {'id': post_id, 'type': 'post', 'status': 'draft', 'revision': REV,
                'supported_text': True, 'decision': 'unassessed', 'title_excerpt': 'PRIVATE_TITLE'}

    def test_discovery_follows_empty_permission_page_and_keeps_boundary(self):
        client = self.inventory_client([self.inventory_page([], 3), self.inventory_page([self.inventory_item()])])
        report = migration.discover(client, page_size=2)
        self.assertTrue(report['traversal_complete'])
        self.assertEqual(client.calls, [(0, 2, None), (3, 2, 7)])
        self.assertEqual([r['id'] for r in report['records']], [7])
        self.assertNotIn('PRIVATE_TITLE', json.dumps(report))
        self.assertNotIn('facts', report['records'][0])

    def test_discovery_budget_returns_a_resumable_cursor(self):
        client = self.inventory_client([self.inventory_page([self.inventory_item(2)], 3)])
        report = migration.discover(client, page_size=2, max_pages=1)
        self.assertFalse(report['traversal_complete'])
        self.assertEqual((report['next_after'], report['through_id']), (3, 7))
        resumed = self.inventory_client([self.inventory_page([self.inventory_item()])])
        self.assertTrue(migration.discover(resumed, after=3, through_id=7)['traversal_complete'])
        self.assertEqual(resumed.calls[0], (3, 100, 7))

    def test_discovery_rejects_unstable_boundaries_and_invalid_pages(self):
        bad_pages = [self.inventory_page([], 0), self.inventory_page([], 8),
                     self.inventory_page([self.inventory_item(), self.inventory_item()]),
                     self.inventory_page([{**self.inventory_item(), 'revision': 'wrong'}])]
        for page in bad_pages:
            report = migration.discover(self.inventory_client([page]))
            self.assertEqual(report['error'], 'invalid_or_unavailable_page')
            self.assertEqual(report['records'], [])
            self.assertEqual(report['next_after'], 0)
        client = self.inventory_client([self.inventory_page([], 3), self.inventory_page([], boundary=8)])
        report = migration.discover(client)
        self.assertEqual(report['error'], 'invalid_or_unavailable_page')
        self.assertEqual((report['next_after'], report['through_id']), (3, 7))

    def test_discovery_retains_valid_pages_when_a_later_page_fails(self):
        client = self.inventory_client([self.inventory_page([self.inventory_item(2)], 3), (503, None)])
        report = migration.discover(client)
        self.assertEqual(report['error'], 'inventory_failed')
        self.assertEqual([r['id'] for r in report['records']], [2])
        self.assertEqual(report['next_after'], 3)
        self.assertFalse(report['traversal_complete'])

    def test_plan_reads_only_and_apply_binds_original_revision(self):
        client = FakeClient()
        result = migration.migrate([ITEM], client)
        self.assertEqual(result['results'][0]['status'], 'ready_to_submit')
        self.assertEqual([c[0] for c in client.calls], ['GET'])
        result = migration.migrate([ITEM], client, apply=True)
        self.assertEqual(result['results'][0]['status'], 'recorded')
        self.assertEqual(client.calls[-1][2], {'role': 'publisher', 'expected_revision': REV, 'facts': ITEM['facts']})
        self.assertNotIn('PRIVATE_MIGRATION_EVIDENCE', json.dumps(result))

    def test_unknown_stale_policy_and_unsupported_content_never_write(self):
        unknown = copy.deepcopy(ITEM)
        unknown['facts']['origin'] = 'unknown'
        client = FakeClient()
        self.assertEqual(migration.migrate([unknown], client, True)['results'][0]['status'], 'needs_review')
        self.assertEqual(client.calls, [])
        for change, expected in [({'revision': 'sha256:' + 'c' * 64}, 'revision_conflict'),
                                 ({'policy': 'other'}, 'policy_mismatch'),
                                 ({'supported_text': False}, 'unsupported_surface')]:
            client = FakeClient()
            client.current.update(change)
            self.assertEqual(migration.migrate([ITEM], client, True)['results'][0]['status'], expected)
            self.assertEqual([c[0] for c in client.calls], ['GET'])

    def test_existing_exact_record_is_reused_but_conflicts_require_review(self):
        client = FakeClient()
        client.current.update(recorded=True, assessment={'facts': migration.policy_item(ITEM),
                              'decision': 'disclose', 'policy': migration.policy.POLICY, 'record_id': 'c' * 64})
        result = migration.migrate([ITEM], client, True)
        self.assertEqual(result['results'][0]['status'], 'already_recorded')
        client.current['assessment']['decision'] = 'withdrawn'
        self.assertEqual(migration.migrate([ITEM], client, True)['results'][0]['status'], 'assessment_conflict')
        self.assertTrue(all(c[0] == 'GET' for c in client.calls))

    def test_late_conflict_and_uncertain_commit_are_not_retried(self):
        for response, expected in [((409, None), 'rejected'), ((503, None), 'uncertain'),
                                   ((200, {'revision': REV}), 'uncertain')]:
            client = FakeClient(post=response)
            report = migration.migrate([ITEM], client, True)
            self.assertEqual(report['results'][0]['status'], expected)
            self.assertFalse(report['complete'])
            self.assertEqual([c[0] for c in client.calls], ['GET', 'POST'])

    def test_inconsistent_inspection_does_not_authorize_a_write(self):
        client = FakeClient()
        client.current['recorded'] = True
        report = migration.migrate([ITEM], client, True)
        self.assertEqual(report['results'][0]['status'], 'invalid_response')
        self.assertEqual([c[0] for c in client.calls], ['GET'])

    def test_lost_commit_response_is_reconciled_by_a_later_read(self):
        class LostResponse(FakeClient):
            def request(self, method, post_id, body=None):
                response = super().request(method, post_id, body)
                if method == 'POST':
                    self.current.update(recorded=True, assessment={'facts': migration.policy_item(ITEM),
                        'decision': 'disclose', 'policy': migration.policy.POLICY, 'record_id': 'd' * 64})
                    raise OSError('PRIVATE_MIGRATION_EVIDENCE PRIVATE_PASSWORD')
                return response
        client = LostResponse()
        uncertain = migration.migrate([ITEM], client, True)
        self.assertEqual(uncertain['results'][0]['status'], 'uncertain')
        self.assertNotIn('PRIVATE_', json.dumps(uncertain))
        retry = migration.migrate([ITEM], client, True)
        self.assertEqual(retry['results'][0]['status'], 'already_recorded')
        self.assertEqual([c[0] for c in client.calls], ['GET', 'POST', 'GET'])

    def test_batch_validation_precedes_any_requests(self):
        good = {'version': 1, 'role': 'publisher', 'items': [ITEM]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'batch.json'
            path.write_text(json.dumps(good))
            self.assertEqual(migration.read_batch(path), [ITEM])
            for bad in [{**good, 'role': 'unknown'}, {**good, 'items': []},
                        {**good, 'items': [ITEM] * 101}, {**good, 'items': [ITEM, ITEM]},
                        {**good, 'items': [{**ITEM, 'id': True}]},
                        {**good, 'items': [{**ITEM, 'id': 2 ** 63}]},
                        {**good, 'items': [{**ITEM, 'revision': REV + '\n'}]},
                        {**good, 'items': [{**ITEM, 'content': 'not allowed'}]}]:
                path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):
                    migration.read_batch(path)
            path.write_text('{"version":1,"version":1}')
            with self.assertRaises(ValueError):
                migration.read_batch(path)

    def test_transport_requires_https_and_refuses_redirects(self):
        for url in ['http://example.com/wp-json', 'https://user:pass@example.com/wp-json',
                    'https://example.com/wp-json?token=x', 'https://example.com/wp-json#fragment']:
            with self.assertRaises(ValueError):
                migration.Client(url, 'admin', 'PRIVATE_PASSWORD', True)
        with self.assertRaises(ValueError):
            migration.Client('http://127.0.0.1/wp-json', 'admin', 'PRIVATE_PASSWORD')
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_response(302)
                self.send_header('Location', '/credential-leak-target')
                self.end_headers()
            def log_message(self, *_):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = migration.Client('http://127.0.0.1:' + str(server.server_port) + '/wp-json', 'admin', 'PRIVATE_PASSWORD', True)
            status, data = client.request('GET', 7)
            self.assertEqual(status, 302)
            self.assertIsNone(data)
            self.assertEqual(requests, ['/wp-json/ai-disclosure/v1/posts/7/assessment'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
