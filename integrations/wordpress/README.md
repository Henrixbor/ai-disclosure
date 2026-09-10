# WordPress adapter development

This directory now contains an **experimental text publishing plugin** and native PHP assessment engine. WordPress 7.1/PHP 8.3 integration tests cover REST and native post updates, superseded-policy scheduling checks, public content/excerpts/feeds and private evidence. It is not a production compliance plugin: broader surfaces, editor UI, reassessment/amendment, historical inventory and legal review remain open.

Activation adds publication gates for ordinary posts and pages. New publication and edits to published content through the supported routes need evidence recorded first. Unsupported body media, dynamic blocks and shortcodes are held. Test on an isolated copy before activation on an existing site; this can interrupt workflows that have not been integrated. Activation does not retroactively classify or rewrite historical posts.

## Install in a test site

Copy this directory to `wp-content/plugins/ai-disclosure` and activate **AI Disclosure (Development)**. The entrypoint is `ai-disclosure.php`. No Python, shell execution, model SDK, npm dependency or remote disclosure service is needed on the WordPress host. The repository's Playground dependency is for disposable development tests only.

The plugin is agent/API-oriented at this stage. Use WordPress's existing authenticated REST access: cookie authentication with `X-WP-Nonce` for same-site editor clients, or an application password over HTTPS for an external publishing integration. Never put credentials in public scripts or commit them. The caller must have both permission to edit the target post and the post type's publication capability.

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

Each policy/content version has an immutable record in a non-autoloaded WordPress option. The database's unique option name prevents conflicting concurrent inserts; identical retries return the existing decision. A conflicting declaration returns 409. There is no amendment UI/API yet, so do not attempt to evade a conflict with a fabricated content edit. An explicit reassessment workflow is required before production adoption. Records are retained on deactivation; this is not a retention/deletion policy.

Successful assessments return `revision`, `decision`, `policy` and `implementation_verified: false`. The GET response returns current `revision`, `recorded`, `supported_text` and `policy`. Responses use `Cache-Control: private, no-store`. Request bodies are limited to 1 MiB. WordPress error objects carry `code`, `message` and `data.status`: authentication/capability failures use 401/403, malformed inputs 400, conflicts/publication gaps 409, oversized requests 413, and unsupported surfaces or unresolved facts/roles 422. See [OpenAPI](openapi.json). The development `/v1` contract must be versioned for breaking changes; there is no list endpoint or pagination contract yet.

## Presentation and coverage

Required text notices appear before post content and excerpts, using a local stylesheet. Rendered REST content and RSS carry the notice too. Current declared text exceptions emit no extra notice. Private evidence is not registered as REST metadata and is not included in generated content. Verify the actual theme, cache/CDN, language, archive templates and CSS/CSP before adoption. The default wording is English.

The gate covers tested REST updates and `wp_insert_post`/`wp_update_post`. Scheduled posts with stale policy records move to pending before WordPress's cron publication handler. Other code calling `wp_publish_post` directly, direct SQL, custom post types, featured media, arbitrary post metadata, custom renderers and caches are not covered. Plugin deactivation removes the gates and dynamic notices. This version does not provide a claim that every publishing path is intercepted.

Body media, shortcodes and unsupported/dynamic blocks are rejected by this text adapter rather than silently assigned text treatment. Supported block names are paragraph, heading, list, list-item, quote and separator, plus ordinary sanitized static text HTML. Independently encountered assets, exports, social previews and native applications require separate integrations.

## Run the live tests

From the repository root, install development dependencies with `npm ci --ignore-scripts`, install Chromium with `npx playwright install chromium`, then run `npm run test:wordpress`. Playground boots a disposable WordPress 7.1/PHP 8.3 site, activates the actual plugin, exercises native/REST operations and verifies public output in Chromium with JavaScript disabled. It closes the test server afterward. Authentication tests cover capability checks and anonymous HTTP denial; production HTTPS/application-password configuration and the block/classic editor UI still need deployment-specific verification.

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

Before production use, complete the amendment workflow, editor interaction, historical inventory, applicable additional surfaces and independent legal review. Test the exact target WordPress/database/theme combination; the current live fixture uses Playground's SQLite runtime.

Publication gates must be verified against REST/block-editor updates, classic-editor updates, scheduled posts and supported programmatic publication. WordPress offers a [REST pre-insert filter](https://developer.wordpress.org/reference/hooks/rest_pre_insert_this-post_type/) and an [insert short-circuit filter](https://developer.wordpress.org/reference/hooks/wp_insert_post_empty_content/), but neither alone establishes coverage of every publishing path. Do not advertise that coverage until tested against a running WordPress instance.

Dynamic blocks, shortcodes, independently encountered media and theme-specific output still need dedicated handling. The native policy engine provides decisions; plugin tests establish only the specific integration behavior described above.
