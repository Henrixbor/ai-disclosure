=== AI Disclosure (Development) ===
Contributors: henrixbor
Requires at least: 7.1
Tested up to: 7.1
Requires PHP: 8.3
Stable tag: 0.1.0-alpha.3
License: MIT
License URI: https://opensource.org/license/mit

Version-bound text assessments and minimal publication notices. Experimental integration; not legal certification.

== Description ==

Record known AI-use facts in the post editor or authenticated REST API. The plugin adds text notices to supported post/page content, excerpts and feeds when its assessment requires one. Publication gates hold unassessed, stale or unsupported updates on the tested publishing paths. Private evidence is retained outside public content.

This development build does not detect AI origin, assess every website law, cover all media or intercept every publishing path. It does not classify historical content on activation. Supply real evidence and verify the site's actual rendering, caching and publishing workflow before adoption.

No Python, Node.js, remote service, model API key or visitor tracking is required on the WordPress host.

== Installation ==

1. Use an isolated copy of the site with WordPress 7.1 and PHP 8.3. Activation adds publication gates and may hold existing publishing workflows.
2. In Plugins > Add New Plugin > Upload Plugin, select the built ai-disclosure-wordpress ZIP, install and activate AI Disclosure (Development).
3. Open AI disclosure below the post editor (Meta Boxes in the block editor). Load current text, supply known facts and evidence, and record the assessment before publishing.
4. Integrate automated generation and publishing with the authenticated API, then verify public notices, exports and cache behavior. An installed plugin cannot establish missing historical facts.

Full scope, API and development instructions:
https://github.com/Henrixbor/ai-disclosure/tree/main/integrations/wordpress

== Operations ==

WP Super Cache is cleared after committed assessment changes. Other page caches and CDNs need integration and verification. Do not treat deactivation as a rollback of an assessment: it removes dynamic notices and publication gates. Private records are retained; this build has no automatic uninstall deletion or migration of historical content.

== Changelog ==

= 0.1.0-alpha.3 (development) =
Text assessments, editor controls, revision checks, private inventory/history, explicit amendments and withdrawals, conditional publication guards and WP Super Cache invalidation. Not a stable release or a WordPress.org directory listing.
