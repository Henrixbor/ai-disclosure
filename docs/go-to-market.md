# Go-to-market plan

Owner: Henrixbor. Prepared 10 September 2026. Planning assumptions and targets below are hypotheses, not demonstrated market demand, legal advice or revenue forecasts. Product release remains subject to the engineering and scope gates in RELEASE-PLAN.md.

## Positioning

**AI disclosures that fit your site.** Give your coding agent a small skill, record AI use in your publishing workflow, and display the appropriate notices without adding a blanket banner.

Explain three capabilities in the first screen: agent-guided integration, minimal content-associated disclosure, and checks that catch missing or stale records. Explain supported integrations beside the install command. Do not market the product as a universal AI detector, all-law compliance engine, legal certification or automatic blanket-popup exemption.

The origin of the content and the publisher's context determine the legal assessment. The product makes known facts operational; it cannot establish every historical fact by scanning a page. This should be evident in the onboarding, not only hidden in terms.

## Initial customer

Start with small web agencies and developer-led publishers that already use coding agents and control their CMS/templates or build pipeline. They can install the skill, supply generation metadata and see the benefit across multiple sites. Prefer teams with a repeatable publishing process over completely unknown archives.

Initial jobs:

1. An agency adds appropriate article and media disclosures to a client site without redesigning it.
2. A publisher stops manually placing labels after each AI generation job.
3. A developer verifies that a content or theme change has not invalidated a review or hidden a disclosure.

Qualify pilot applicants by stack, content modalities, origin records, review workflow, EU audience and control over deployment. Do not prioritise regulated/high-risk products or customers expecting the tool to legalise deceptive content. Route broader legal requirements to appropriate review.

## Why someone would choose it

The existing market already includes notice widgets and CMS labelling. The proposed advantage is a small, inspectable, self-hostable workflow that coding agents can use and publishing systems can verify. A reusable notice is free software; integrations and reliable operations are the product value.

Competitor observations were gathered in [the research brief](../research/product-feasibility.md): [DiscloseKit](https://disclosekit.eu/) advertises disclosure and evidence operations; [AIM Transparency](https://aimtransparency.com/) advertises WordPress media labelling; [Klaibel](https://klaibel.com/widget) offers a notice widget. These are vendor descriptions, not independently audited capabilities. Recheck them before final launch messaging. Do not claim a unique category or proven competitive moat.

## Distribution order

### 1. Public repository and working examples

Publish a versioned repository on Henrixbor's profile, with a concise install path, MIT licence for original software, supported-surface matrix, runnable examples, security reporting and release notes. Keep third-party research material's rights separate from the software licence; link official sources in public releases instead of repackaging source documents unnecessarily.

The README should answer, in order: what it does, one installation command, one prompt, a before/after demonstration, supported scope, and verification. Use a real public URL after repository creation. No imaginary package name or download command.

### 2. Coding-agent distribution

Ship the same skill for Codex and Claude Code. Preserve project-local installation for repeatability and opt-in personal installation for cross-project use. Offer host-specific plugin packaging only where tested. Seek marketplace listings through their normal submissions; acceptance and automatic selection are not guaranteed.

Use clear metadata such as “Fix AI disclosure and EU AI Act transparency issues in websites and products.” A broad “fix the legal requirements” prompt may route to the AI portion, but must not hijack unrelated privacy, accessibility or consumer-law work. Include explicit invocation as a fallback.

### 3. Integration-led discovery

Write one detailed integration guide per supported stack. Demonstrate a generation hook updating content facts and a pre-deploy check catching stale review. Publish small template examples suitable for other maintainers to adopt, without silently adding tracking or remote services.

After pilots, approach maintainers of relevant starter templates and CMS plugins with a concrete working integration and test evidence. Do not submit unsolicited bulk PRs or insert promotional instructions into other projects.

### 4. Educational content

Publish a focused article: “Does an AI-built website need an AI label?” Follow with “Why one site-wide popup cannot cover every AI disclosure” and “Keeping disclosures correct when agents edit content.” Link official sources, date the legal basis and distinguish requirements from conservative product defaults.

Use short recordings showing the actual workflow and the resulting UI. Show an unresolved case as well as a successful one; that builds realistic expectations. Review legal claims before publication.

## Pilot and launch sequence

Durations are scheduling estimates after the release gates pass, not promises to launch unverified features.

| Phase | Work | Evidence to advance |
|---|---|---|
| Readiness | Verify supported modes, browser behaviour, packaging and CI; review rules/claims; prepare documentation | Passing release audit with named limitations and owners |
| Two-week pilot | Recruit up to five design partners with distinct publishing workflows; provide hands-on onboarding | At least three independently reproduced integrations; no unresolved critical defects |
| Two-week improvement | Fix repeated onboarding friction and missing adapter coverage; obtain permission for any testimonials | Partners can publish a new item through the integrated workflow without manual label placement |
| Public launch | Release notes, website, technical walkthrough and opt-in community posts | Install commands and demo work from a clean environment; support channel staffed |
| Following month | Measure retention and repeated integrations; prioritise one additional adapter | Evidence of recurring use, not only repository stars |

No outreach messages, social posts, paid campaigns or marketplace submissions are sent by this document. Drafts below are preparation for explicit publication decisions.

## Metrics without tracking site visitors

Measure opt-in developer onboarding and aggregate repository/support activity. The embedded notices should not become analytics beacons.

- Activation: completed installation plus a verified example on a supported route.
- Time to first working notice: pilot target under 15 minutes when origin/context facts are available; track missing-fact time separately.
- Automation: proportion of subsequent supported publications that require no manual label editing.
- Precision: unnecessary notices and missed required notices found by human review; record both rather than claiming a universal accuracy percentage.
- Reliability: deployment failures, stale-record detections and hidden-label regressions.
- Retention: teams still running checks after four weeks and agencies integrating a second site.
- Support burden: issues per integration and time spent resolving them.

Use targets to test the thesis. Stop broad promotion and fix the product if users cannot complete installation or supported content repeatedly loses disclosures. Do not optimise a “compliance score” that hides missing coverage.

## Business model

Keep the core skill, renderer and local checks usable without a hosted subscription. Do not remove legally relevant notices when a customer stops paying.

Validate paid demand for agency workspaces, managed policy distribution, team review queues, private evidence storage and integration support. Add these only after the local workflow is reliable. Pricing should be tested with customers before building billing; do not attach a revenue forecast to unvalidated interest. Offer optional integration services first if they reveal repeatable adapter needs.

## Draft launch copy

### Repository / release introduction

“AI Disclosure helps coding agents add appropriate AI notices to existing sites. It combines a small skill with local publishing checks, so labels follow recorded content facts and stale editorial approvals are caught before deployment. Start with the supported examples, inspect the output, and keep your site's design. It supports transparency work; it does not certify compliance or detect every AI-generated asset.”

### Pilot invitation (not sent)

“I'm looking for a few agencies or publishers using coding agents and a repeatable content workflow to test AI Disclosure. The aim is to reduce manual disclosure work without adding a blanket banner. I'd like to learn which content origins you can record, how reviews happen, and what breaks during publishing. Would you be interested in trying an integration on a test site?”

### Website primary call to action

“Install the skill” with a secondary “Try the example”. Link directly to the verified release command. Avoid an email gate for open-source downloads.

## Operations and responsibility

Henrixbor owns releases, support triage and decisions about scope/claims. Assign an EU regulatory adviser to review policy changes and deployment-specific edge cases; no such review is represented as completed. Keep a dated source register and legal-review status. Critical security or disclosure regressions receive a documented fix/release path; customers receive actionable notices through channels they chose.

Before public promotion, verify the public repository, release artifacts, install commands and website from outside the development checkout. Review all screenshots and examples for private data. Maintain a changelog explaining behaviour changes, migration steps and any changed legal basis.

The [legal review package](legal-review.md) gives the reviewer concrete decisions, code, test outputs and launch claims to assess. Use its scoped approval record before treating the readiness phase as complete.
