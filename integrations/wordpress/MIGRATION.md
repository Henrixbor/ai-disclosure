# Migrate established content facts

The repository's Python client records evidence-backed assessments for existing WordPress posts/pages. It does not infer AI origin, modify post content, publish drafts, override conflicting assessments or discover every rendered surface. The WordPress plugin remains responsible for its supported notices and publishing gates.

Use an isolated site copy first. Install the current development ZIP and configure its publishing/cache integrations. The client requires Python 3.9+ in the checkout and the current matching policy on the WordPress host. No Python is installed on WordPress.

## Discover existing records

Configure the application-password environment variables described below, then run:

```sh
python3 scripts/wordpress_migrate.py --discover \
  --api-url https://example.com/wp-json
```

Discovery reads up to 10 pages of 100 records by default. Use `--page-size` (1–100) and `--max-pages` (1–100) to bound a run. It returns IDs, saved revisions, publication status, supported-text flags and assessment decisions. It omits title excerpts and evidence and never creates facts or assessments. Keep this report private because it can identify unpublished content.

If `traversal_complete` is false and there is no error, continue with both returned cursor values:

```sh
python3 scripts/wordpress_migrate.py --discover \
  --api-url https://example.com/wp-json --after 120 --through-id 980
```

Replace those illustrative numbers with `next_after` and `through_id` from your report. Preserve each report and combine its records with subsequent pages. On an error, resolve it before continuing from the last validated cursor. Exit 0 means the bounded traversal finished; exit 1 means it is incomplete or failed; exit 2 means invalid configuration or interruption.

The initial upper ID stays fixed across pages, excluding later-created posts. This is not an immutable snapshot: edits, deletions and permission changes can occur during scanning. Only accessible post/page source records are covered; templates, media, embedded services and rendered surfaces need separate inspection. A completed traversal does not mean all site content has been assessed or is legally compliant.

## Prepare a private batch

Use the authenticated inventory and assessment inspection endpoints to select items and obtain their exact revisions. Establish the origin/context facts from real creation and review records. Keep unknown facts unresolved. Save a UTF-8 JSON file with this shape, replacing the illustrative values with actual inspected data:

```json
{
  "version": 1,
  "role": "publisher",
  "items": [
    {
      "id": 42,
      "revision": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "facts": {
        "origin": "ai_generated",
        "applicable": true,
        "public_interest": true,
        "evidence": "Reference to the actual creation and scope evidence"
      }
    }
  ]
}
```

Supply 1–100 unique positive signed 64-bit post IDs and at most 1 MiB per batch. These are publisher/deployer text assessments; other roles and unsupported media require a separate workflow. Editorial review, when established, uses the same `review` object documented in the assessment API. The client never assumes a review exemption.

Treat the batch as private: it contains evidence and may name reviewers. Keep it outside public build output and version control, with restricted file permissions. A batch is not a discovery report or proof that the site's entire archive has been assessed.

## Plan, then apply

Create a WordPress application password for a user with the required edit and publication capabilities. Supply the username through `AI_DISCLOSURE_WP_USER` and the application password through `AI_DISCLOSURE_WP_PASSWORD`, using your normal secret manager or private environment setup. Do not put passwords in command arguments, repository files or public scripts.

```sh
python3 scripts/wordpress_migrate.py /private/batch.json \
  --api-url https://example.com/wp-json
```

The default plan only reads WordPress. It checks the declared facts with the local policy, verifies the server policy and exact saved revision, and compares any existing assessment. A `ready_to_submit` result means the request is eligible for submission; it does not mean the public notice is already present or legally sufficient.

```sh
python3 scripts/wordpress_migrate.py /private/batch.json \
  --api-url https://example.com/wp-json --apply
```

Apply records eligible items independently using their original `expected_revision`. A later edit is rejected by the server. No batch-wide rollback is attempted: earlier successful items remain recorded if another item fails. An identical existing assessment is reused without another POST. Conflicting or withdrawn assessments require explicit inspection/amendment through the existing API/editor; the importer does not overwrite them.

HTTPS with normal certificate verification is required. The REST base must end in `/wp-json` (a site subdirectory is supported). Redirects are refused, and proxy environment settings are not used, so credentials are not forwarded through an unexpected redirect or environment proxy. `--allow-loopback-http` is solely for explicit disposable tests at literal loopback addresses. It does not enable application passwords over HTTP on a production WordPress site.

## Interpret the report

The JSON report contains IDs, revisions, decisions and record IDs, without private evidence, passwords or raw server error bodies. Exit 0 means all supplied items were eligible in plan mode or recorded/reused in apply mode. Exit 1 means at least one item was held or failed. Exit 2 means input/configuration was invalid or the run was interrupted. `complete` refers only to the supplied batch and mode; it is not a site-coverage or legal-compliance verdict.

| Status | Next step |
| --- | --- |
| `ready_to_submit` | Review the plan and apply when authorized. |
| `recorded`, `already_recorded` | Verify the rendered publication and applicable caches/exports. |
| `needs_review` | Establish missing facts; do not invent an origin or exemption. |
| `revision_conflict` | Inspect changed content and reassess its evidence. Never just substitute the new revision. |
| `assessment_conflict` | Review the current record and explicitly amend if warranted. |
| `policy_mismatch` | Reconcile the maintained client/plugin policy versions before proceeding. |
| `unsupported_surface` | Integrate that surface separately. |
| `inspection_failed`, `invalid_response` | Resolve access, transport or response issues, then inspect again. |
| `rejected` | Read the HTTP status and inspect the current state; no automatic retry occurs. |
| `uncertain` | A POST may have committed. Inspect or rerun the same batch: an exact existing record is reused. Do not assume rollback. |

Requests have 30-second transport timeouts and responses are limited to 2 MiB. Interrupted runs may have committed earlier items. Review the report and actual state before continuing. Revoke the application password when the migration is finished if it is not needed for the integrated publishing workflow.

After applying, check representative direct links, templates, archives, feeds and exports. Recording an assessment can change the notice on already-public content without rewriting it. Other caches/CDNs and unsupported surfaces still require their own integration. Future content requires generation/publishing hooks; running this importer once does not install an ongoing process.

## Verification scope

Unit tests cover read-only planning, guarded apply, policy/content conflicts, exact-record reuse, malformed batches, redirect refusal and recovery after a lost write response. The MySQL suite runs the real CLI with a disposable WordPress application password, proving a no-write plan, legacy-article notice, held stale/unknown items, idempotent retry and private reports. Its local HTTP allowance is isolated to that disposable fixture. Production TLS, hosting authentication and customer evidence remain deployment-specific checks.
