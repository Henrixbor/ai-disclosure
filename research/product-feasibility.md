# AI Disclosure: product and legal feasibility

Research date: 10 September 2026. Scope: EU AI Act Article 50 and a proposed website disclosure product. This is product research, not a legal opinion or certification. Recommendations below distinguish legal requirements, Commission guidance, voluntary Code commitments, and proposed engineering controls. No software has been built or deployed as part of this research.

## Recommendation

Proceed with an open-source disclosure SDK and optional hosted management service. Position it as infrastructure for Article 50 transparency: identify applicable duties, render appropriate notices, preserve provenance, and document decisions. Do not promise automatic compliance from a banner or an AI detector.

The AI Act does not require every website to label everything touched by AI. The useful product is a rules-driven publishing integration that minimises unnecessary notices while making required disclosures reliably visible. A generic popup saying content “may be AI-generated” is not a defensible universal substitute for content-specific disclosure.

## 1. Legal baseline

The principal legal source is [Regulation (EU) 2024/1689, as amended](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng). The Commission published [Article 50 Guidelines on 20 July 2026](https://digital-strategy.ec.europa.eu/en/library/guidelines-transparency-obligations-providers-and-deployers-ai-systems). The [final Transparency Code of Practice](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content) is voluntary and has been assessed as adequate by the Commission and AI Board. It is a practical compliance route, not a replacement for the legislation or a certificate obtained by installing software.

Article 50 generally applies from 2 August 2026. Eligible generative systems placed on the market before that date have until 2 December 2026 for provider marking and detection under Article 50(2); that transition does not postpone deployer labelling or chatbot disclosure. See [Commission timing guidance](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act) and Guidelines paragraph 153.

Establishment outside the EU does not automatically remove obligations. Scope can include third-country providers and deployers where output is used in the EU. Roles depend on the actual arrangement: an organisation can be both a provider and a deployer. A branded AI application built around another company's model needs its own role assessment. Open-source distribution is not a blanket exemption for AI systems subject to Article 50. See Guidelines §§2.3–2.4 and [Article 2](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-2).

| Situation | Legal / guidance position | Product response |
|---|---|---|
| AI generated the website's source code | Source-code output is excluded from Article 50(2) marking in the Guidelines. Building with AI does not alone trigger a site-wide public label. | Separate software authorship from displayed content. |
| Generative AI system produces text, images, audio or video | Providers have marking and detectability duties under Article 50(2), with specified exceptions and technical qualifications. | Separate provider module; visible labels alone cannot satisfy these duties. |
| Professional use creates or manipulates realistic media constituting a deepfake | Deployer disclosure applies. This is broader than celebrity impersonation and is assessed against resemblance, reality and misleading authenticity in context. | Content-associated visual and/or audio disclosure. |
| AI text is published to inform the public on matters of public interest | Deployer disclosure applies unless an exception is established. | Publication-level label by default when in scope. |
| That text undergoes substantive human review or editorial control, with editorial responsibility held by a person/entity | The text disclosure exception can apply. This does not exempt deepfake media or provider marking. | Reviewed-publication workflow; public editorial contact. |
| Ordinary marketing copy or product description | Guidelines give examples outside the text obligation, excluding claims involving matters such as health, safety or sustainability. | Assess purpose and subject matter; avoid a universal “marketing is exempt” rule. |
| Obvious abstract or non-realistic AI art | May not meet the deepfake test. Provider marking is a separate question. | Optional transparency label if desired. |
| Deepfake within an evidently artistic, creative, satirical or fictional work | Disclosure can be less intrusive; it is not automatically waived. | Contextual artistic-work preset, subject to case assessment. |
| Chatbot / interactive AI | Article 50(1) requires provider-designed disclosure unless the interaction is obvious under the relevant test. | Notice at the start of the interaction/session. |

Sources: [Guidelines PDF](https://ec.europa.eu/newsroom/dae/redirection/document/131215), especially §§3–4, 6 and 7. “AI-augmented” is a useful product category, not a universal legal trigger or a prescribed disclosure term.

## 2. Can one popup replace individual labels?

**Not as a general product promise.** Article 50(5) requires clear, distinguishable disclosure by first interaction or exposure. Guidelines paragraph 143 explains that content obligations apply to each output in relation to each exposed person. Paragraph 142 rejects disclosures easily missed under ordinary conditions, including information buried in terms or menus.

The [Code PDF](https://ec.europa.eu/newsroom/dae/redirection/document/129555), Section 2, Measures 1.1–1.2, supplies a more concrete route:

- A visible AI icon or equivalent label can be compact; additional information can be layered behind it.
- For ordinary deepfake media, the label should be embedded or use an equivalent overlay that appears on the content, subject to placement rules.
- For text, a label can be near the headline or at the beginning of the publication. It need not label every paragraph.
- Short text has a contextual-notice accommodation where individual labels would impair readability or usability, including notice at the beginning of exposure or interaction.
- Artistic works have tailored options, including adjacent interface disclosures, subject to first-exposure and perceivability requirements.

These are specific accommodations, not a general permission for one website popup to cover arbitrary future media and articles.

| Proposed mode | Assessment and implementation |
|---|---|
| “This website may use AI” in a dismissible popup | Useful optional policy communication. Too uncertain and detached from particular outputs to sell as the sole disclosure for all in-scope content. |
| “All articles on this page are AI-generated” at the top of a genuine AI article collection | A possible alternative for assessment, but not established here as sufficient for every article or route. Deep links, scrolling, reuse and mixed content can defeat the association. Do not ship as the default compliance route. |
| One badge by an article headline | Stronger fit with the Code. Automatically covers the relevant publication without repeated paragraph badges. |
| Contextual notice for short text outputs | Explicitly contemplated by the Code under its conditions. Restrict the mode to that use case. |
| Small overlay on a realistic synthetic image | Stronger fit with the standard media placement rules. |
| Small adjacent label for qualifying creative work | Supported by the creative-work provisions, with context and visibility constraints. |

Recommended visible language: “AI-generated”, “AI-modified”, or a Code-compatible AI icon with an accessible explanation. Select wording based on evidence. A truthful scope statement can accompany local notices, but “may” must not replace a known fact.

Article 50 disclosure does not itself require cookie-style consent or an Accept/Reject exchange. A visitor's acknowledgment does not waive obligations. Default to passive disclosure. Design essential information to be visible without hover or click; use the click for details.

## 3. Existing content and future content

The full Guidelines are more precise than a generic statement that old content is exempt. Paragraph 154 distinguishes:

- Outputs/deepfakes generated or manipulated before 2 August 2026: no retroactive marking/labelling requirement under the described rules.
- Public-interest text generated/manipulated **and published** before that date: no retroactive labelling requirement.
- Qualifying older text first published on or after that date: labelling is required unless an exception applies.

Voluntary retroactive labelling is encouraged without disproportionate effort. A new AI modification needs reassessment. Republishing and ambiguous version histories should enter legal review rather than be silently classified as exempt. Store generation, manipulation and publication dates separately.

Historical backfill should import CMS metadata, creation records, asset credentials and accountable owner declarations. Missing credentials mean unknown, not human-authored. A detector score cannot establish the history of every legacy item or justify a guarantee of correct classification.

For future content, capture provenance at creation: the model integration, CMS plugin or builder agent records what it created or changed before publishing. Default records can inherit from a pipeline known to generate AI content, with explicit exceptions. Do not apply a false factual label merely to avoid maintaining provenance.

## 4. Proposed architecture

This is an engineering recommendation, not a legally prescribed architecture.

1. **Content record:** stable ID, version/hash, media type, origin status (`human`, `ai_generated`, `ai_modified`, `unknown`), evidence source, dates, legal role, intended audience/context, public-interest and deepfake assessments, review state, responsible publisher, and policy version. Distinguish declared from cryptographically verified provenance.
2. **Deterministic policy engine:** produces `disclose`, `exception_recorded`, `outside_scope`, or `needs_review`, with reasons and sources. A model may suggest classifications; unknown evidence must not automatically become an exemption.
3. **Rendering layer:** framework-neutral HTML/Web Component plus React/Next.js adapter; server-render the essential disclosure. Use a badge at publication level, media overlay, creative-work label, short-text session notice, or chatbot notice as appropriate.
4. **Publishing adapters:** CMS hooks, build integration, media processing and export hooks. Track derivatives, embeds, feeds and downloadable assets; a webpage overlay does not travel with an image saved directly.
5. **Evidence and operations:** versioned assessments, corrections, review decisions, reproducible publication checks, and exportable reports. Record what the system verified; do not claim that a configuration log proves what every visitor saw.

Suggested repository packages: `core`, `web`, `react`, `cli`, `adapters`, `policy-tests`, and `examples`. Publish a stable schema, agent integration instructions, idempotent record/upsert operations, dry-run migration, and examples of all supported disclosure modes. Start with a CLI and CMS hooks; add an MCP integration if customers need it.

An agent integration should inspect content, register origin and evidence, request human review when required, and verify the rendered result. An agent cannot serve as the human review needed for the editorial exception. Invalidate review status after a substantive AI edit: Guidelines paragraphs 134–136 specifically reject superficial/automated review and address post-review AI changes.

The first release should serve deployers/publishers. Provider marking and detection is a separate, significantly harder capability. Preserve existing credentials and offer verification before promising to implement that whole duty. [C2PA](https://c2pa.org/faqs/) provides provenance infrastructure; credentials can be removed, and provenance does not prove factual truth. A custom HTML attribute, JSON manifest or JSON-LD field is not by itself proof of Article 50(2) compliance.

## 5. Minimum-intrusion product controls

- No universal popup by default. Offer a compact publication badge and media-specific presets.
- No hover-only disclosure, unreadable contrast, footer-only required notice or layout that displays content before its label.
- Test direct entry to every supported route, mobile layouts, client navigation, infinite scroll, media playback after seeking, and no-JavaScript rendering.
- Preserve disclosure in supported exports and test metadata after resizing/transcoding/CDN processing.
- Clearly identify unsupported embeds or distribution channels; do not show a blanket green compliance status.
- Make public disclosure survive a hosted-service outage by publishing local static configuration and markup.
- Keep visitor tracking off by default. Separate any analytics and consent processing from the disclosure function.

These tests measure implementation coverage, not legal certification. Actual accessibility obligations depend on the service; the product should nevertheless make readable, keyboard- and screen-reader-accessible disclosure the default.

## 6. Collateral and privacy

Offer a public AI transparency page describing usage, label meanings, editorial responsibility, contact details and the correction process. Maintain an internal policy covering scoping, review responsibilities, publication, provenance preservation and incident correction. Provide deployment and legal-review exports.

The Code's editorial provision requires suitable policies and accountability; it explicitly does not require documenting every individual text-review instance. Per-version review records are a proposed product safeguard, not a universal statutory logging duty. Avoid collecting confidential prompts or journalistic sources by default.

If the hosted product processes personal data, assess controller/processor roles, legal bases, retention, transfers and contractual requirements, including a DPA where applicable. Cookie-free does not automatically mean GDPR-free. [EDPB guidance](https://www.edpb.europa.eu/sme/be-compliant/process-personal-data-lawfully_en) explains lawful processing; its [cookie taskforce report](https://www.edpb.europa.eu/system/files/2023-01/edpb_20230118_report_cookie_banner_taskforce_en.pdf) addresses storage/access requirements. A self-hosted static disclosure can reduce these operational complications.

Labelling cannot legalise unlawful content. Copyright, privacy, likeness, deceptive advertising, consumer protection and sectoral requirements still need separate assessment. Article 50 tooling also does not cover the entire AI Act, including prohibited uses or high-risk-system duties.

## 7. Market and business model

Competitors already advertise overlapping capabilities. These are vendor statements, not independently tested compliance or customer traction:

| Vendor | Advertised scope | Implication |
|---|---|---|
| [DiscloseKit](https://disclosekit.eu/) | Scope assessment, disclosure variants, inventories, statements, verification and evidence logs; listed Pro plan €49/month when checked. | A widget plus an evidence dashboard is already a direct competing proposition. |
| [AIM Transparency](https://aimtransparency.com/) | WordPress image badges, embedded source metadata, schema output and library workflows. | Image/CMS integration is already contested. |
| [Klaibel](https://klaibel.com/widget) | Free notice widget and website scanning. | The basic notice itself faces free alternatives. |

Suggested differentiation: open-source, agent-friendly creation-to-publication provenance; validated low-clutter display modes; and tests that catch stale review decisions and lost disclosures in deployment. These are hypotheses to validate, not demonstrated market gaps.

Start with agencies and teams publishing through a known CMS or React application. Offer an open-source local SDK/CLI and charge for managed policy updates, team review workflows, multi-site operations, verification and evidence exports. Keep basic public disclosure functional without a paid service dependency. Do not price around visitor consent records; consent is not the core task.

Proposed website promise: **“AI disclosures that fit your content. Integrate once, record AI use as you publish, and apply clear notices where required.”** Explain the supported scope and show a working notice gallery. Avoid “one script makes every website AI Act compliant”, “EU certified”, or “we detect all AI content”.

## 8. Delivery and legal validation

**First:** have an EU AI-regulatory lawyer review the decision table and actual sample notices. Select initial jurisdictions, languages, audience and customer roles. Obtain a written opinion on the short-text session mode, artistic-work mode, deepfake boundaries, editorial exception and historical-content handling. Review terms and marketing claims as part of the same exercise.

**Then:** build a deployer MVP with the policy core, content registry, accessible labels, static fallback, one CMS adapter, one framework adapter, and evidence export. Provide draft classifications for unknown legacy content and a review queue. Do not couple launch to solving universal AI detection or provider watermarking.

**Pilot:** use consenting design partners across a marketing site, editorial publisher and synthetic-media use case. Measure installation effort, wrong or unnecessary labels, missing provenance, direct-entry disclosure, review invalidation and export survival. Legal reviewers assess representative outputs; customers verify their content history and responsibilities.

**Expand:** add more CMSs, agent integrations and specialised provider marking only after validating the first workflow. Maintain dated policy releases with traceable sources and legal review when rules change.

Go/no-go recommendation: **go for an integration and disclosure-management product; do not base the business on universal retroactive detection or a blanket-popup compliance guarantee.** A lawyer can review defined deployments and product claims; neither that review nor software can guarantee every future customer use is lawful.

## Research files and limitations

- `sources/article-50-guidelines.pdf`: Commission PDF downloaded from document 131215; extracted text alongside it. Relevant paragraphs: 68 (source code), 119–123 (creative works), 131–138 (text/review), 142–144 (placement/accessibility), 153–154 (dates/legacy content).
- `sources/transparency-code.pdf`: final Code downloaded from document 129555; extracted text alongside it. Relevant printed pages: 29–33 (design/placement), 35–36 (creative works/editorial process).
- The EUR-Lex document pages presented a browser-verification screen during direct retrieval. Dates were cross-checked against Commission guidance and the indexed consolidated/amending legal texts. Final legal review should consult the consolidated operative legislation directly.
- No competitor product was installed or audited; no paid-market demand or market-size estimate is established here.
- Public URLs and local source copies support review as of the research date. Later legal changes and national/sectoral rules require reassessment.
