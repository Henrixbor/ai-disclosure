# WordPress adapter development

This directory currently contains a native PHP assessment engine, **not an installable WordPress plugin**. It has no publishing hooks, admin interface, storage, authentication or rendered notices yet. Do not upload it and assume a site is covered.

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

The plugin must record evidence against the actual proposed post version and hold stale or unresolved publication updates without deleting the previous publication. Facts must remain private across WordPress REST responses, feeds, revisions and public pages. Generation agents need an authenticated publishing route; editors need actionable errors. Historical posts require inventory and real evidence, not an invented origin default.

Publication gates must be verified against REST/block-editor updates, classic-editor updates, scheduled posts and supported programmatic publication. WordPress offers a [REST pre-insert filter](https://developer.wordpress.org/reference/hooks/rest_pre_insert_this-post_type/) and an [insert short-circuit filter](https://developer.wordpress.org/reference/hooks/wp_insert_post_empty_content/), but neither alone establishes coverage of every publishing path. Do not advertise that coverage until tested against a running WordPress instance.

Notices must survive the site's actual content, excerpt, REST-rendered and feed surfaces. Dynamic blocks, shortcodes, independently encountered media and theme-specific output need explicit handling. This module provides decisions only; it does not yet fulfill that integration contract.
