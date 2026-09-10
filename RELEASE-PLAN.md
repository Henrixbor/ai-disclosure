# Release requirements

Objective: finish the minimal, agent-friendly AI disclosure product, publish it on Henrixbor's public GitHub profile, and deliver a go-to-market plan. An initial prototype is not completion of this objective.

## Acceptance evidence required

- [ ] Maintained, versioned policy decisions with uncertainty, evidence, current editorial review, timing and role boundaries.
- [ ] Actual disclosure rendering and content/publishing integration, not only assessment instructions.
- [ ] Existing-content inventory, safe migrations, repeatable future-content handling and change detection.
- [ ] Supported article, image, audio/video and chatbot presentation; unsupported contexts clearly reported.
- [ ] First-exposure, direct-link, accessibility and dynamic-content verification on a real rendered example.
- [ ] Portable minimal Codex / Claude skills with tested installation and distribution packaging.
- [ ] Reliable local operation, safe input/output handling, documentation, tests and CI.
- [ ] Website with installation, examples, scope and truthful product claims.
- [ ] Licence, contribution/security guidance, versioned release and clean packaged artifacts.
- [ ] Public repository under Henrixbor, verified remote contents and CI status.
- [ ] Concrete go-to-market plan, audience, channels, launch materials, metrics and operating responsibilities.
- [ ] Final requirement-by-requirement audit, including legal-review status and any unmet production gate.

## Current state

2026-09-10: original skill/helper prototype inspected. GitHub CLI is authenticated as Henrixbor; no remote or initial commit exists. Previous work is concrete progress (files and passing prototype tests), not a finished product. No external legal review has been obtained. Implementation and release work can proceed; avoid claiming legal certification.

## Implementation direction

Keep one portable skill and a dependency-free local publishing tool. Add explicit content bindings and version detection so publishing can render minimal disclosures reliably without guessing origins from text. Let agents adapt those bindings to site structure. Begin with static HTML build output and documented framework/CMS hooks; retain all originally discussed modalities and report unintegrated surfaces honestly. Public demo and release will follow verification, not precede it.
