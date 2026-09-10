#!/usr/bin/env python3
"""Check maintained PDF fingerprints. Does not assess legal changes or update rules."""
import argparse
import hashlib
import json
import re
from datetime import date
from urllib.parse import urlsplit
from pathlib import Path
import urllib.request

DEFAULT = Path(__file__).resolve().parents[1] / 'research/policy-sources.json'
LIMIT = 25 * 1024 * 1024


def download(url):
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = response.read(LIMIT + 1)
    if len(payload) > LIMIT or not payload.startswith(b'%PDF'):
        raise ValueError('Expected a PDF of at most 25 MiB')
    return payload


def check(registry, fetch=download):
    if not isinstance(registry, dict) or not isinstance(registry.get('sources'), list) or not registry['sources']:
        raise ValueError('A nonempty source registry is required')
    date.fromisoformat(registry['checked_on'])
    seen = set()
    for source in registry['sources']:
        if not isinstance(source, dict) or not isinstance(source.get('id'), str) or not source['id'] or source['id'] in seen:
            raise ValueError('Source IDs must be nonempty and unique')
        seen.add(source['id'])
        url = urlsplit(source['url'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Source URLs must be public HTTPS URLs without credentials')
        if not isinstance(source.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', source['sha256']):
            raise ValueError('Source fingerprint must be a SHA-256 hex string')
    results = []
    for source in registry['sources']:
        result = {'id': source['id'], 'url': source['url'], 'expected_sha256': source['sha256']}
        try:
            actual = hashlib.sha256(fetch(source['url'])).hexdigest()
            result.update(actual_sha256=actual, status='unchanged' if actual == source['sha256'] else 'changed')
        except Exception as error:
            result.update(status='unavailable', error=str(error))
        results.append(result)
    return {'basis': 'Document bytes only; unchanged documents do not prove current legal compliance',
            'baseline_checked_on': registry['checked_on'], 'sources': results,
            'unverified': registry.get('unverified', [])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, default=DEFAULT)
    args = parser.parse_args()
    try:
        report = check(json.loads(args.registry.read_text(encoding='utf-8')))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, str(error) + '\n')
    print(json.dumps(report, indent=2))
    states = {row['status'] for row in report['sources']}
    return 2 if 'unavailable' in states else 1 if 'changed' in states else 0


if __name__ == '__main__':
    raise SystemExit(main())
