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

Later on 2026-09-10: public repository created at https://github.com/Henrixbor/ai-disclosure, initial commit 6fa984f4575d9c60bdfbc1bbc55692e5415d5135. CI run 34465220091 succeeded: Python 3.9/3.13 on Linux/macOS plus a browser job. The local suite has 26 tests. The HTML adapter now inventories, records version-bound facts, plans and stages article/image disclosures. The real demo was checked at 390px and 1440px without JavaScript. The go-to-market plan and MIT licence are in place. These checks do not establish remaining modalities, dynamic runtime coverage or legal certification.

Next work: complete audio/video and live-chat presentation/integration, improve runtime/CMS adapters and export handling, package versioned downloads/plugins, broaden behavioural/browser verification, finish hosted website and conduct final release audit. Independent legal review remains unperformed; do not hide that status. Sites project identity is persisted in .openai/hosting.json; never recreate it.

## Implementation direction

Keep one portable skill and a dependency-free local publishing tool. Add explicit content bindings and version detection so publishing can render minimal disclosures reliably without guessing origins from text. Let agents adapt those bindings to site structure. Begin with static HTML build output and documented framework/CMS hooks; retain all originally discussed modalities and report unintegrated surfaces honestly. Public demo and release will follow verification, not precede it.

Current development evidence: 34 Python tests pass locally. Media revisions now include local asset bytes. Experimental audio controls passed Chromium sequencing, pause, configuration invalidation, notice-failure and no-JavaScript checks. This does not satisfy the production media gate: captions, alternate sources, exports and real spoken-notice validation remain unresolved.

Chat presentation now uses an explicit direct-interaction fact and a static notice preceding conversation and composer. Chromium checks cover desktop/mobile deep links and replacement with a resumed conversation template. This does not implement a model service, voice interactions, third-party widgets or provider marking.

Media integration now preserves local captions/subtitles with a selector and timed audio text. Chromium checks exercise a real original WebM fixture, video captions and fullscreen disclosure visibility. Staging also reassesses the copied snapshot before publishing, catching content changes during copying. Other track types, alternate sources, direct media/export surfaces and independent legal review still need work.
