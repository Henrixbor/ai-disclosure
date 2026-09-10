#!/usr/bin/env python3
"""Plan or apply evidence-backed WordPress assessments; never infer content origin."""
import argparse
import base64
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('aid_migration_policy', ROOT / 'skills/ai-disclosure/scripts/assess.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)
LIMIT = 1024 * 1024
REVISION = re.compile(r'sha256:[a-f0-9]{64}\Z')
RECORD = re.compile(r'[a-f0-9]{64}\Z')
DECISIONS = {'disclose', 'exception_declared', 'no_publisher_label', 'outside_declared_scope'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def read_batch(path):
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('Batch exceeds 1 MiB')
    data = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(data, dict) or set(data) != {'version', 'role', 'items'}:
        raise ValueError('Expected version, role and items')
    if type(data['version']) is not int or data['version'] != 1 or data['role'] != 'publisher':
        raise ValueError('Version 1 and an explicitly established publisher role are required')
    if not isinstance(data['items'], list) or not 1 <= len(data['items']) <= 100:
        raise ValueError('Supply 1 to 100 items per batch')
    seen = set()
    for item in data['items']:
        if not isinstance(item, dict) or set(item) != {'id', 'revision', 'facts'}:
            raise ValueError('Each item requires id, revision and facts only')
        if type(item['id']) is not int or not 1 <= item['id'] <= 9223372036854775807 or item['id'] in seen:
            raise ValueError('Post IDs must be unique positive signed 64-bit integers')
        seen.add(item['id'])
        if not isinstance(item['revision'], str) or not REVISION.fullmatch(item['revision']):
            raise ValueError('Each item needs its inspected SHA-256 revision')
        facts = item['facts']
        if not isinstance(facts, dict) or set(facts) - {'origin', 'applicable', 'public_interest', 'evidence', 'review'}:
            raise ValueError('Unsupported publisher facts')
        policy.validate({'version': 1, 'role': 'publisher', 'items': [policy_item(item)]})
    return data['items']


def policy_item(item):
    return {**item['facts'], 'id': 'wp-' + str(item['id']), 'kind': 'text', 'revision': item['revision']}


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, api_url, username, password, allow_loopback_http=False):
        url = urllib.parse.urlsplit(api_url)
        if url.username or url.password or url.query or url.fragment or not url.hostname:
            raise ValueError('API URL must have a host and no credentials, query or fragment')
        try:
            local = ipaddress.ip_address(url.hostname).is_loopback
        except ValueError:
            local = False
        if url.scheme != 'https' and not (allow_loopback_http and url.scheme == 'http' and local):
            raise ValueError('HTTPS is required; HTTP is only allowed explicitly for literal loopback test addresses')
        if not url.path.rstrip('/').endswith('/wp-json'):
            raise ValueError('Supply the site REST base ending in /wp-json')
        if not username or ':' in username or not password:
            raise ValueError('Set AI_DISCLOSURE_WP_USER and AI_DISCLOSURE_WP_PASSWORD')
        self.base = api_url.rstrip('/')
        self.auth = 'Basic ' + base64.b64encode((username + ':' + password).encode()).decode()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirects())

    def request(self, method, post_id, body=None):
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        request = urllib.request.Request(self.base + '/ai-disclosure/v1/posts/' + str(post_id) + '/assessment',
            data=data, method=method, headers={'Authorization': self.auth, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            with self.opener.open(request, timeout=30) as response:
                raw = response.read(2 * LIMIT + 1)
                if len(raw) > 2 * LIMIT:
                    raise ValueError('Oversized response')
                return response.status, json.loads(raw, object_pairs_hook=unique_object)
        except urllib.error.HTTPError as error:
            # Error bodies can echo credentials/evidence; never include them in reports.
            status = error.code
            error.close()
            return status, None


def migrate(items, client, apply=False):
    results = []
    for item in items:
        row = {'id': item['id'], 'revision': item['revision']}
        results.append(row)
        writing = False
        try:
            expected = policy_item(item)
            decision = policy.decide(expected)['status']
            if decision not in DECISIONS:
                row['status'] = 'needs_review'
                continue
            status, current = client.request('GET', item['id'])
            if status != 200:
                row.update(status='inspection_failed', http_status=status)
                continue
            if not isinstance(current, dict) or current.get('policy') != policy.POLICY:
                row['status'] = 'policy_mismatch'
                continue
            if current.get('revision') != item['revision']:
                row['status'] = 'revision_conflict'
                continue
            if current.get('supported_text') is not True:
                row['status'] = 'unsupported_surface'
                continue
            if not isinstance(current.get('recorded'), bool) or 'assessment' not in current:
                row['status'] = 'invalid_response'
                continue
            existing = current['assessment']
            if current['recorded'] != (existing is not None):
                row['status'] = 'invalid_response'
                continue
            if existing is not None:
                if (isinstance(existing, dict) and existing.get('facts') == expected
                    and existing.get('policy') == policy.POLICY
                    and existing.get('decision') == decision and isinstance(existing.get('record_id'), str)
                    and RECORD.fullmatch(existing['record_id'])):
                    row.update(status='already_recorded', record_id=existing['record_id'], decision=decision)
                else:
                    row['status'] = 'assessment_conflict'
                continue
            row['decision'] = decision
            if not apply:
                row['status'] = 'ready_to_submit'
                continue
            writing = True
            status, response = client.request('POST', item['id'], {'role': 'publisher', 'expected_revision': item['revision'], 'facts': item['facts']})
            if status != 200:
                row.update(status='uncertain' if status >= 500 else 'rejected', http_status=status)
                continue
            if (not isinstance(response, dict) or response.get('revision') != item['revision']
                or response.get('policy') != policy.POLICY or response.get('decision') != decision
                or not isinstance(response.get('record_id'), str) or not RECORD.fullmatch(response['record_id'])):
                row['status'] = 'uncertain'
                continue
            row.update(status='recorded', record_id=response['record_id'])
        except (OSError, ValueError, TypeError, KeyError, urllib.error.URLError):
            row['status'] = 'uncertain' if writing else 'inspection_failed'
    return {'mode': 'apply' if apply else 'plan', 'policy': policy.POLICY,
        'basis': 'declared facts only; public rendering not verified', 'results': results,
        'complete': all(row['status'] in {'ready_to_submit', 'already_recorded', 'recorded'} for row in results)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    parser.add_argument('--api-url', required=True)
    parser.add_argument('--apply', action='store_true', help='Record eligible assessments; does not publish or rewrite content')
    parser.add_argument('--allow-loopback-http', action='store_true', help='Disposable local test sites only')
    args = parser.parse_args()
    try:
        items = read_batch(args.batch)
        client = Client(args.api_url, os.environ.get('AI_DISCLOSURE_WP_USER', ''), os.environ.get('AI_DISCLOSURE_WP_PASSWORD', ''), args.allow_loopback_http)
        report = migrate(items, client, args.apply)
        print(json.dumps(report, indent=2))
        return 0 if report['complete'] else 1
    except (OSError, ValueError, TypeError, KeyError):
        print('Migration input or configuration is invalid. Check the documented format and credential environment variables.', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('Interrupted. Inspect recorded state before retrying; completed writes are not rolled back.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
