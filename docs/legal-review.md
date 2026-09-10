# Legal review package

Status: **not commissioned, not approved**. Prepared 10 September 2026 for Henrixbor. This document requests review of a defined implementation; it is not a legal opinion, a claim of Code adherence or a compliance certificate. No request has been sent to anyone.

## Product and proposed launch scope

AI Disclosure is an MIT-licensed local toolkit used by coding agents and publishers. It accepts declared content facts, renders notices, catches stale records and supplies integration points for publishing. It has no origin detector, legal-fact verifier, hosted evidence service or visitor telemetry. A coding-agent host and website host have their own data processing, separate from this package.

The initial product is deployer/publisher transparency support. The research plan explicitly postpones specialised provider marking; see [the proposed launch sequence](../research/product-feasibility.md). Provider/both/unknown roles remain unresolved in the tool. A customer must not choose “publisher” solely to make a build pass.

Public release alpha.2 supports static publishing, local chat/media presentation and CMS/server component rendering. Main additionally contains portable article/image HTML export, a Node publishing client, a Next.js static-export example and an experimental WordPress text plugin with private assessments, publication gates and a migration client. These development integrations are not installed by the alpha.2 catalog. Review the exact release and commit being approved; approval must not silently attach to later versions. The [release audit](../RELEASE-PLAN.md) distinguishes implemented behavior, tested fixtures and unverified production conditions.

## Source status

- [Consolidated AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng): operative legislation must be consulted directly by the reviewer. Automated retrieval currently encounters a browser-verification screen; this package does not represent a fresh complete reading of that consolidated page.
- [Commission Code overview](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content): distinguishes the mandatory obligations from voluntary Code adherence and alternative means of demonstrating adequacy.
- [Commission guidelines](https://ec.europa.eu/newsroom/dae/redirection/document/131215): scope, roles, public-interest text, deepfakes, exceptions, timing and accessibility. The current PDF was downloaded and matched to the research copy on 10 September 2026.
- [Code of Practice](https://ec.europa.eu/newsroom/dae/redirection/document/129555): Section 2 covers presentation and organisational commitments for signatories. Its current PDF also matched the research copy.
- [EU icon guidance](https://digital-strategy.ec.europa.eu/en/policies/eu-icons-labelling-ai-generated-content): icons are optional and do not independently establish compliance; it describes placement, accessibility and download/resharing considerations.

The PDF fingerprints and the unavailable consolidated-page check are recorded in [the source registry](../research/policy-sources.json). A matching PDF does not prove there have been no relevant amendments, court decisions, national rules or other guidance.

## Decisions requiring a written answer

For each row, return **acceptable within stated conditions**, **changes required**, or **outside this review**, with reasons, sources and any conditions. Do not use a single general “compliant” verdict.

| Decision | Actual implementation to review | Requested determination |
| --- | --- | --- |
| Customer roles and EU scope | Manifest role plus an evidence-backed `applicable` declaration; no automatic jurisdiction/date inference | Define when an agency, publisher or builder becomes a provider, including an integrated chatbot. Identify required onboarding facts and excluded/high-risk uses. |
| Public-interest text | `public_interest: true` leads to a headline/start notice unless current review is declared | Confirm decision examples for editorial reporting, marketing, product claims, health/safety/sustainability and investor material; distinguish ordinary technical editing. |
| Human-review exception | A version-matched substantive review declaration and named responsible entity can remove a text notice | Specify the necessary real review/control and responsibility. Assess supplementary contact/policy obligations if following the Code. The tool does not prove these activities occurred. |
| Deepfake boundary | A contextual `deepfake` fact drives media notices; the agent does not infer this solely from photorealism | Review realistic synthetic products, backgrounds, avatars, voices, incidental editing and mixed human/AI works against intended and foreseeable audiences. |
| Minimal presentation | English “AI-generated”, “AI-modified” or “You are interacting with AI.”; one notice per bound publication/asset/session | Determine adequacy of the actual wording, placement and custom text badges; identify conditions for using these instead of EU icons and whether Code adherence is intended. |
| Creative works | Still disclosed; current renderer uses the same visible badge | Define when a less intrusive adjacent or contextual presentation is justified. No creative-work exemption should be inferred merely from an aesthetic style. |
| Blanket/session mode | A universal “may contain AI” banner is not implemented as a substitute | Identify any narrow short-text or session accommodation that can be specified and tested. Review its boundaries before enabling it. |
| Legacy content and republication | `applicable` encapsulates the operator's temporal assessment; content/asset changes invalidate stored versions | Verify the guidelines' legacy distinction and the legal effect of new edits, first publication, republication and missing dates. File age alone is not an implemented exemption. |
| WordPress migration and publication gates | Authenticated discovery lists accessible post/page sources; migration records established facts with revision preconditions. Supported publication paths hold unassessed updates, while activation does not classify or rewrite the existing archive | Review the onboarding claims and operator decisions for legacy publications, scheduled content and unsupported surfaces. Confirm how to communicate that an installed gate or completed scan does not establish historical coverage or legal adequacy. |
| Assessment history and withdrawal | Private WordPress records retain evidence, actor/time and prior assessment versions. Withdrawal of an assessed draft preserves its audit record and prevents supported republication until reassessment | Determine an appropriate evidence-minimisation, access, retention and deletion policy for the intended operators. Identify necessary handling of personal data, confidential sources, access requests and backups. History preservation is an engineering feature, not a claim that indefinite retention is legally required or permitted. |
| Audio/video | Visible player notice; required supplied audio notice plays before content; local captions; fullscreen retains the frame label | Review actual spoken words, language, audibility, late entry, repeated playback and interruptions. Test files are silent and cannot establish this adequacy. Raw downloads and native/voice surfaces remain incomplete. |
| Exports | Portable HTML keeps notices with embedded raster bytes; static images can still be extracted without a burned-in notice | Define intended export channels and which ones require embedded media labels or other measures. Do not approve raw image/audio/video redistribution on the strength of the document test. |
| Accessibility and language | Keyboard/mobile/no-JS/browser fixture checks; default notices are English | Select launch languages and audiences, including foreseeable vulnerable audiences. Specify assistive-technology checks and required translations. Existing checks are not a complete accessibility certification. |
| Provider marking/provenance | Original bytes are copied or embedded unchanged; provider-role findings stay unresolved | Confirm that preservation is not being represented as machine-readable marking, detection or signature verification. Define any obligations for the product operator itself. |
| Other law and marketing | No universal all-law claim; MIT software licence; local facts/report workflow | Review claims, terms, privacy statements and operator identity obligations. Clarify that disclosure does not authorise otherwise unlawful content. Consider host logging/authentication when reviewing “no tracking” wording. |

The distinction in the text-review row matters: [Code Commitment 4](https://ec.europa.eu/newsroom/dae/redirection/document/129555) includes appropriate editorial policies and public contact details for relevant signatories. Per-item revision records are our engineering safeguard; they should not be described as a universal statutory obligation to log each editorial review.

## Concrete evidence to inspect

- [Assessment decisions](../skills/ai-disclosure/scripts/assess.py), [publishing renderer](../skills/ai-disclosure/scripts/site.py), [media controls](../skills/ai-disclosure/assets/players.js) and [document export](../skills/ai-disclosure/scripts/exports.py).
- [Decision tests](../tests/test_tooling.py), [publication/export tests](../tests/test_site.py), [browser fixtures](../scripts/build_media_fixture.py) and [browser checks](../scripts/browser_media.cjs). Test inputs declare hypothetical contexts to exercise behavior; they are not real legal findings.
- [WordPress implementation and coverage](../integrations/wordpress/README.md), [migration behavior](../integrations/wordpress/MIGRATION.md), [PHP policy](../integrations/wordpress/policy.php), [publication gates](../integrations/wordpress/publication.php) and [withdrawal/history behavior](../integrations/wordpress/withdrawal.php). Inspect an actual deployment's templates, caches and evidence-access controls separately from the disposable fixtures.
- [Node integration contract](../skills/ai-disclosure/references/publishing.md#javascript-publishing-client) and [Next.js example](../examples/nextjs/README.md). These connect declared facts to publishing; neither independently establishes the underlying facts or the customer's legal role.
- [Agent instructions](../skills/ai-disclosure/SKILL.md), [rules](../skills/ai-disclosure/references/rules.md), [manifest contract](../skills/ai-disclosure/references/manifest.md), [publishing contract](../skills/ai-disclosure/references/publishing.md), [website source](../web/index.html) and [go-to-market claims](go-to-market.md).

Run the documented development checks to reproduce technical outputs. Also obtain representative customer outputs, generation histories, editorial procedures, spoken notices and deployment routes. Review those separately from the synthetic fixtures. Do not disclose confidential prompts, journalistic sources or personal data merely to populate a test record.

## Approval record and release gate

Record the reviewer's identity and qualification, engagement date, reviewed commit/release, jurisdictions, languages, customer roles, deployment assumptions, findings by row, required changes, approved public wording and review expiry/triggers. No fields should be prefilled as approved.

Henrixbor owns implementing and evidencing required changes. A qualified reviewer provides the scoped legal determination. Customer publishers establish their actual content facts and responsibilities. Engineering verifies the deployed behavior. A stable release must have no unresolved finding that contradicts its advertised supported use; documented unsupported uses must not be marketed as covered.

## Maintaining the legal basis

Before a release or a new deployment's legal assessment, run `python3 scripts/check_policy_sources.py`. Exit 0 means only that the listed PDF bytes match; 1 means a document changed; 2 means a source could not be checked or input failed. The `unverified` list remains visible even on exit 0.

A changed source triggers comparison and review, not automatic rewriting of legal rules or client labels. Check the operative legislation and other relevant authorities separately. Record the new source and reasoned decision, version any changed rules, add meaningful regression cases, document migration effects and release validated packages. Do not replace old public archives. There is no scheduled legal monitor or claim of continuous regulatory coverage.
