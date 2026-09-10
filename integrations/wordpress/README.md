# WordPress adapter development

This directory contains an **experimental text publishing plugin** and native PHP assessment engine. WordPress 7.1/PHP 8.3 tests cover REST/native updates, editor controls, explicit amendments, stale-writer rejection, superseded-policy scheduling checks, public content/excerpts/feeds and private evidence. It is not a production compliance plugin: broader surfaces, historical migration and legal review remain open.

Activation adds publication gates for ordinary posts and pages. New publication and edits to published content through the supported routes need evidence recorded first. Unsupported body media, dynamic blocks and shortcodes are held. Test on an isolated copy before activation on an existing site; this can interrupt workflows that have not been integrated. Activation does not retroactively classify or rewrite historical posts.

## Install in a test site

Build an installable archive from the repository root:

```sh
python3 scripts/package_skill.py --format wordpress --output dist/ai-disclosure-wordpress.zip
```

The command prints its SHA-256. It uses a fixed allowlist, deterministic timestamps and file permissions, rejects symlinks/missing runtime files, and refuses to overwrite a different archive. Choose a new output path for a changed build. The ZIP contains one `ai-disclosure` folder with PHP, CSS, editor JavaScript, licence and a short readme; it excludes tests, development dependencies and private records.

In a WordPress 7.1/PHP 8.3 test site, use **Plugins → Add New Plugin → Upload Plugin**, select the ZIP and activate **AI Disclosure (Development)**. You can alternatively copy this directory to `wp-content/plugins/ai-disclosure`. The entrypoint is `ai-disclosure.php`. No Python, shell execution, model SDK, npm dependency or remote disclosure service is needed on the WordPress host. Python and the repository's Playground dependency are used only to build and verify the archive locally. This packaging does not constitute a stable release or WordPress.org listing.

The plugin declares this repository as its `Update URI`. WordPress documents this header as protection against accidentally replacing a third-party plugin with a similarly named WordPress.org plugin. It does not install a GitHub updater, verify archive signatures or prevent other privileged plugins from changing update responses. This development build is updated through the verified ZIP workflow; it does not automatically fetch new code or policy rules. See [WordPress's Update URI specification](https://make.wordpress.org/core/2021/06/29/introducing-update-uri-plugin-header-in-wordpress-5-8/).

Use the editor panel below or WordPress's existing authenticated REST access: cookie authentication with `X-WP-Nonce` for same-site editor clients, or an application password over HTTPS for an external publishing integration. Never put credentials in public scripts or commit them. The caller must have both permission to edit the target post and the post type's publication capability.

### Replace an existing test installation

Back up the database and plugin files, then upload the verified ZIP through **Plugins → Add New Plugin → Upload Plugin**. WordPress shows the installed/uploaded versions before offering **Replace current with uploaded**. Check the result, activation, recorded assessments and public notices before resuming publication. Do not deactivate the plugin as an update workaround: that removes its gates and dynamic notices. Keep private assessment records in the database backup, not in a public export.

The MySQL browser suite now exercises the actual authenticated upload and replacement confirmation. It proves that an invalid ZIP and an unwritable staging directory leave activation, all private assessment bytes and installed files unchanged. A successful same-version replacement removes an obsolete fixture file, preserves all assessment/history records and the published version, retains its visible notice and continues to reject an unassessed edit. The fixture models writable hosting after explicitly correcting directories created by the initial CLI installer. These checks do not prove version-changing migrations, interruption recovery, uninterrupted serving during replacement, HTTPS hosting configuration or every filesystem failure. Resolve ownership errors through the site's normal hosting process; do not make plugin directories world-writable.

## In the post editor

Open **AI disclosure** below the editing area. In the block editor, open WordPress's **Meta Boxes** area first; its toggle also supports keyboard focus and Enter. The panel is available to users who can edit and publish the post.

1. Choose **Load current text**. This reads the current title, body and excerpt from the editor, including unsaved changes. Known facts for that exact version are loaded; otherwise fields remain unknown.
2. Supply established source/context facts and evidence. Declare human review only if it actually covers the loaded text, and name the person or organisation with editorial responsibility.
3. Choose **Record assessment**. If changing a recorded assessment, provide a reason. Then use WordPress's normal Publish/Update control.

The panel does not save or publish the article itself. If the text changes after loading, it requires a fresh load and does not carry review into the new version. If another assessment has been recorded, it requires reading that assessment before changes. It never replaces unknown origin with an AI guess. Evidence fields use authenticated requests and stay out of public content. No additional frontend script is installed for visitors.

The proposed-text endpoint is `POST /wp-json/ai-disclosure/v1/posts/{id}/inspection` with optional string `title`, `content` and `excerpt` fields. It returns the revision, supported-text flag, policy and any private matching assessment without saving anything. It has the same capabilities, 1 MiB request limit and private/no-store headers as assessment recording. This also gives agents a way to bind a review to proposed text before publication.

When recording facts, send that inspection's revision as `expected_revision` on the assessment request. The server compares it with the exact title/content/excerpt after applying any proposed text fields. A stale revision returns HTTP 409 with code `ai_disclosure_revision` before writing an assessment; malformed revisions return 400. Inspect again and reassess the evidence after a conflict. Do not silently substitute the newer revision. The editor sends this field automatically. It is additive and optional for existing API clients, but agents migrating saved content should always supply it. It is a content-version precondition, not a lock on publication or a replacement for the existing assessment ID/amendment checks.

## Inventory existing content

Once real evidence and inspected revisions are available, use the [batch migration client](MIGRATION.md) to plan and apply assessments. Planning is read-only by default; apply preserves unresolved items and uses content-version preconditions.

Agents can read `GET /wp-json/ai-disclosure/v1/inventory?limit=25`. The endpoint requires publication capability, then checks edit and publication permissions on every item. It scans posts and pages in all statuses, including unpublished, auto-draft and trash records. It returns ID, type, status, a short title excerpt, exact text revision, `supported_text` and `decision`. It returns no evidence or article body and makes no changes.

Continue with `after=<next_after>&through_id=<through_id>&limit=25`, keeping the first response's `through_id`. Stop only when `next_after` is null: an empty authorized page can still have more candidates. The default limit is 25, maximum 100. The limit bounds scanned database IDs, so fewer items may be returned after permission filtering. IDs created above the initial boundary belong to a later scan. Numeric cursors are traversal positions, not credentials or proof that omitted content does not exist.

Use the inventory as a migration queue:

1. Prioritize public and scheduled records whose decision is `unassessed` or `withdrawn`, and any record with `supported_text: false`.
2. Retrieve the content through WordPress's authorized editor/REST access. Establish its actual source and context from creation records or the responsible publisher. Unknown origin remains unresolved; do not bulk-declare the archive AI-generated.
3. Reinspect the current text revision before recording facts. Use the assessment/amendment endpoints for supported content. Preserve unresolved content as an explicit coverage gap; unsupported media needs its own integration.
4. Verify the actual public view and cache invalidation after any new notice, and rescan after migration. Recording facts for an already-published supported version can add its notice without rewriting the article.

This scan covers stored post/page text, not custom post types, featured media, metadata, widgets, independent assets or rendered theme output. The ID boundary does not freeze edits, deletions, permissions or assessment changes. Recheck every selected version before acting; a finished traversal is not a complete-site compliance report. Responses are private/no-store. Incorrect ranges return 400, authorization failures 401/403 and database failures 503.

## Publication transaction

1. Create/save a draft using WordPress's normal endpoint. Obtain its post ID.
2. Read `GET /wp-json/ai-disclosure/v1/posts/{id}/assessment` for its actual revision and supported-text status.
3. Send `POST` to the same endpoint with `role` and evidenced `facts`. Optional `title`, `content` and `excerpt` describe a proposed update; omitted fields use the current post. The adapter computes ID, kind and revision. Recording an assessment does not publish content.
4. Publish/update through the normal WordPress REST endpoint or `wp_insert_post`/`wp_update_post`, checking its success result. The actual text must match the recorded version. A failed update leaves the old publication intact.

```json
{
  "role": "publisher",
  "facts": {
    "origin": "ai_generated",
    "applicable": true,
    "public_interest": true,
    "evidence": "Reference to this generation transaction and established publication context"
  }
}
```

These are example fields, not defaults to apply to a customer. Omitted/unknown role and unresolved facts cannot pass. Generation jobs should provide actual evidence automatically. Historical content needs established facts; do not infer origin from appearance. The `review` object follows the shared manifest format and must refer to the actual current/proposed revision. A substantive edit cannot silently reuse its exception.

Each policy/content version has an active record in a non-autoloaded WordPress option. The database's unique option name prevents conflicting initial inserts; identical retries return the existing decision. Changing facts requires the explicit amendment flow below. Records are retained on deactivation; this is not a retention/deletion policy.

Successful assessments return `revision`, `record_id`, `decision`, `policy` and `implementation_verified: false`. GET returns current `revision`, `recorded`, `supported_text`, `policy` and a private `assessment` object (or null). That object includes facts, decision, record ID, actor/time, policy and any superseded-record ID/amendment reason. Do not forward it to visitors. Responses use `Cache-Control: private, no-store`. Request bodies are limited to 1 MiB. WordPress errors carry `code`, `message` and `data.status`: authentication/capability failures use 401/403, malformed inputs 400, conflicts/publication gaps 409, oversized requests 413, unresolved facts/roles/surfaces 422, and an audit-storage failure 503. See [OpenAPI](openapi.json). Breaking changes require a new API version; there is no list endpoint.

## Correct facts or update a review

Read the current private assessment. POST the complete replacement `facts`, established `role`, `replaces` set to its `record_id`, and a nonempty `amendment_reason` (at most 1000 UTF-8 bytes). Keep the actual title/content/excerpt unchanged when only the assessment changes. For a proposed content update, supply the proposed text fields and the record ID returned when that proposed version was assessed.

The server assesses the replacement facts before changing anything. It archives the old record, rereading past a cached missing key if another writer inserted that same archive, then atomically replaces the active database value only if the old value still matches byte-for-byte. A stale writer receives 409; read the current assessment before deciding whether to try again. Repeating a successful amendment with the same replaced ID, facts and reason returns the same record ID without another write or event. A retry after a later amendment receives 409.

An authorized caller can read a retained record at `GET /wp-json/ai-disclosure/v1/posts/{id}/assessments/{record_id}`. This retrieves one archived snapshot, not an unbounded history list; unknown or other-post IDs return 404. A snapshot is saved before the database replacement, so its presence alone does not prove an amendment committed. The active record and its `supersedes` chain establish the committed state. The same capability checks and private/no-store headers apply. The current record remains available through the singular assessment endpoint.

Rejected or unresolved amendments leave the active assessment unchanged; they do not revoke it. Use explicit withdrawal when the evidence is invalid.

## Withdraw invalid facts

First change the post to **Draft** and save it using WordPress's normal controls. Load that saved text in the AI disclosure panel, enter the reason and choose **Withdraw assessment**. This retains the historical facts and prior record but marks the current assessment `withdrawn`. It cannot authorize publication. The panel clears the human-review selection. Re-establish the facts and use **Record assessment** with a reason to restore approval; reusing old facts without explicitly replacing the withdrawn record is rejected.

Agents use `POST /wp-json/ai-disclosure/v1/posts/{id}/withdrawal` with `revision`, `replaces` (the current record ID) and `reason` (nonblank, at most 1000 UTF-8 bytes). Only the exact saved draft revision can be withdrawn. The response is a private record, including `decision: "withdrawn"`; its facts are historical, not approved. GET may still report `recorded: true` because the record exists. Check the decision, not just existence. Authentication, limits and cache headers match the assessment endpoint. Identical retries return the same record; stale IDs, missing assessments or non-draft posts return 409. Storage failures return 503 and require reading the current state before retrying.

The replacement uses the same byte-exact database comparison as amendments and checks draft status in that database write. Supported editor/native publication UPDATEs also require the exact assessment value to remain present in the same SQL statement. A withdrawal or conflicting amendment committed after the precheck prevents that UPDATE from changing the post. A post-write hook remains as a fallback and rereads the assessment after clearing the process-local cache.

The editor/native conditional guard matches the `wpdb::update` query generated from `pre_post_update` data; its SQL shape and percent escaping are tested against WordPress 7.1/PHP 8.3 on SQLite and MySQL 8.4. Reverify it when changing WordPress versions or installing plugins that rewrite SQL. It does not intercept arbitrary SQL or every publishing path. WordPress can return a post ID or HTTP 200 when the conditional UPDATE changed zero rows: callers must inspect the returned/current status and revision rather than treating transport success as publication. Withdrawal does not delete evidence or unpublish old CDN copies.

Committed first records and amendments clear WordPress's post/object cache and emit `ai_disclosure_assessment_recorded` or `ai_disclosure_assessment_amended` with post ID and content revision. Connect external page/CDN caches to these hooks and verify invalidation before adoption. Committed withdrawals emit `ai_disclosure_assessment_withdrawn` with the same arguments. No private facts are included in the event arguments. A newly required label must not remain absent from a previously cached page.

When WP Super Cache is active, the plugin automatically calls its full cache-clear API after each committed assessment change. Full clearing covers shared home, archive and feed output as well as the individual post, including withdrawal on a draft. This can temporarily increase page-generation load. No additional agent instructions or visitor script are required. Other page caches and CDNs still need their own adapter. The provider API does not acknowledge every file deletion; verify writable cache storage and the actual public result. This does not prevent an already-running cache writer from restoring older output.

## Presentation and coverage

Required text notices appear before post content and excerpts, using a local stylesheet. Rendered REST content and RSS carry the notice too. Current declared text exceptions emit no extra notice. Private evidence is not registered as REST metadata and is not included in generated content. Verify the actual theme, cache/CDN, language, archive templates and CSS/CSP before adoption. The default wording is English.

The gate covers tested REST updates and `wp_insert_post`/`wp_update_post`. Scheduled posts with stale policy records move to pending before WordPress's cron publication handler. The status-only UPDATE used by `wp_publish_post`, including core cron, is also guarded against missing/changed assessments and source changes. Cron captures the scheduled source, status and dates before its publisher runs; cancellation, rescheduling or content changes must still match at the SQL write. Arbitrary SQL shapes, custom post types, featured media, arbitrary post metadata, custom renderers and caches are not covered. Plugin deactivation removes the gates and dynamic notices. This version does not provide a claim that every publishing path is intercepted.

Body media, shortcodes and unsupported/dynamic blocks are rejected by this text adapter rather than silently assigned text treatment. Supported block names are paragraph, heading, list, list-item, quote and separator, plus ordinary sanitized static text HTML. Independently encountered assets, exports, social previews and native applications require separate integrations.

## Run the live tests

From the repository root, install development dependencies with `npm ci --ignore-scripts`, install Chromium with `npx playwright install chromium`, then run `npm run test:wordpress`. Playground boots a disposable WordPress 7.1/PHP 8.3 site, activates the actual plugin, exercises native/REST operations and verifies public output in Chromium with JavaScript disabled. It also logs into disposable admin credentials to exercise the classic and block editor panels, stale text, recording, review amendments, draft withdrawal/restoration and actual editor publication. Inventory tests cover bounded traversal, permission filtering, fixed upper IDs, legacy unknown-origin publications, withdrawn/unsupported content and database failures. It closes the test server afterward. Production HTTPS/application-password configuration, other roles, themes and editor versions still need deployment-specific verification.

Both WordPress runners build the allowlisted ZIP into a temporary directory and print its digest. Playground installs the archive through its plugin-install step. The MySQL runner verifies the copied archive's SHA-256 and uses WordPress's `Plugin_Upgrader` before activation. Neither runner mounts the plugin source, so the PHP, editor and public-output checks exercise the packaged files. Temporary host archives are removed after reading.

For a separate MySQL check, install Docker and run `npm run test:wordpress:mysql`. This starts uniquely named disposable WordPress/PHP-Apache and MySQL containers on their own bridge network, publishes only the web port on loopback, installs a fictional test site and the built archive, and runs the same PHP and browser assertions plus the admin replacement checks above. Database and admin passwords are random test values. Normal success/failure cleanup removes those containers, their anonymous volumes and their network; it does not remove unrelated Docker resources. A forcibly killed process may require removing its `aid-mysql-test-*` resources. The images may be downloaded on first use. HTTPS hosting, version-changing upgrades and broader filesystem behavior remain deployment checks.

The MySQL runner also starts separate PHP workers with distinct database connections and coordinates them at actual write boundaries. It verifies that competing amendments yield exactly one winner and one 409 while preserving the original audit record. It exercises both withdrawal/publication orderings: a withdrawal committed after publication precheck keeps the row in draft, with anonymous HTTP 404 verified while the publishing worker is paused after its UPDATE and before corrective hooks; publication committed before the withdrawal write makes the draft guard reject withdrawal. These deterministic interleaving tests cover that intermediate reader; they are not a load test or proof for arbitrary readers, SQL-rewriting plugins or alternative publication paths. A fourth separate-worker case pauses the core cron publisher after its guarded SQL is prepared, cancels the schedule and withdraws its assessment from another connection, then verifies draft status and anonymous HTTP 404 before corrective hooks. Regression checks also exercise cached missing archive keys. External page caches and other publishing paths remain separate deployment checks.

The image digests are fixed in `scripts/verify_wordpress_mysql.cjs`, using the [official WordPress image](https://hub.docker.com/_/wordpress) and [official MySQL image](https://hub.docker.com/_/mysql). The test asserts MySQL 8.4, PHP 8.3 and WordPress 7.1 at runtime and prints the precise versions, theme and server collation. A separate `wordpress-mysql` CI job runs these checks. This adds production-database evidence for the tested configuration; it does not establish compatibility with all hosting, persistent caches or concurrent traffic.

The MySQL runner also downloads the official WP Super Cache 3.1.3 archive, verifies its SHA-256 before extraction and activates it only in the disposable site. It verifies genuine anonymous cache hits and cache invalidation after amendment, withdrawal and a first assessment on legacy content, including absence of private evidence. The fixture uses single-site PHP serving (Simple mode), trailing-slash permalinks and cache rebuild disabled. Expert/mod_rewrite mode, multisite, other cache providers, CDNs and concurrent cache writers are not verified. The cache plugin is a test dependency, not bundled with AI Disclosure.

The root development package pins Express's `qs` dependency to 6.16.0 for the patched query parser. This override belongs to the Playground test server; no npm packages ship in the WordPress plugin.

The PHP implementation avoids requiring Python, shell execution or a remote service on a WordPress host. It accepts the same declared-facts JSON as the core Python engine and returns the same policy identifier, decisions, reasons, presentation guidance and unresolved role gaps. It does not discover content, verify evidence, compute WordPress revisions, render disclosures or certify compliance.

```php
require_once '/path/to/ai-disclosure/integrations/wordpress/policy.php';
$facts = json_decode($private_json, false, 512, JSON_THROW_ON_ERROR);
$assessment = \AiDisclosure\assess($facts);
```

Pass decoded JSON objects, not associative arrays. Invalid input throws `InvalidArgumentException`. Keep the assessment and facts private. Call `assess`, which validates before making decisions; `decide` is an internal helper. PHP 8.3 is the currently tested runtime.

## Policy maintenance

The Python engine and its legal references remain the policy source for this port. Every policy change must update both implementations and pass the parity verifier before release. Equal outputs establish implementation agreement, not legal correctness. Legal review must include any differences in actual WordPress publishing and presentation.

```sh
python3 scripts/verify_php_policy.py --php /path/to/php
```

Or use the pinned official PHP image used for development/CI:

```sh
python3 scripts/verify_php_policy.py --docker php:8.3-cli-alpine@sha256:afdf8b1fee58486ccc0dab5f30f634b86873d56dac985f71ba217945647c05ad
```

The verifier compares complete results across 9,253 inputs: origin and scope combinations, public-interest text, deepfakes, creative context, interaction declarations, missing evidence, current/expired review, role gaps and malformed values. The Docker test runs offline with read-only source mounts, dropped capabilities and a memory limit. Docker is a development option, not a WordPress runtime requirement.

## Remaining integration contract

Before production use, complete evidence-backed historical migration, applicable additional surfaces and independent legal review. Test the exact target WordPress/database/theme combination; the live fixtures cover Playground SQLite and the pinned MySQL 8.4 image, including database compare-and-swap checks. Other database versions, server configuration, themes and concurrent deployment behavior remain unverified.

Publication gates must be verified against REST/block-editor updates, classic-editor updates, scheduled posts and supported programmatic publication. WordPress offers a [REST pre-insert filter](https://developer.wordpress.org/reference/hooks/rest_pre_insert_this-post_type/) and an [insert short-circuit filter](https://developer.wordpress.org/reference/hooks/wp_insert_post_empty_content/), but neither alone establishes coverage of every publishing path. Do not advertise that coverage until tested against a running WordPress instance.

Dynamic blocks, shortcodes, independently encountered media and theme-specific output still need dedicated handling. The native policy engine provides decisions; plugin tests establish only the specific integration behavior described above.
