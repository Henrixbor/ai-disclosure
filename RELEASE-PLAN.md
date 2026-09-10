# Release requirements and current audit

Objective: finish the minimal agent-friendly AI disclosure product, publish it on Henrixbor's public GitHub profile, and deliver a go-to-market plan. A development release does not complete the production objective. Status checked 2026-09-10.

| Requirement | Current evidence | Remaining production work |
| --- | --- | --- |
| Maintained policy, uncertainty and evidence | Dated official sources in skill references; versioned assessment decisions; unknown facts remain unresolved; review tied to revision | Independent legal review; the review package and PDF change-check procedure are prepared but no reviewer has been engaged |
| Actual notices and publishing integration | Static HTML builder; shared component renderer for CMS/server transactions; article/image/chat and local media controls | Framework/CMS adoption tests beyond fixtures; alternate media sources and other track types |
| Existing and future content | HTML candidate inventory, explicit bindings, record hook, media-byte hashes, staging snapshot checks | Historical facts require real evidence; arbitrary structures cannot be proved inventoried automatically |
| First-exposure and accessibility | Chromium desktop/mobile, no-JS, chat deep-link/resume, audible-notice sequencing, captions and fullscreen checks | Real spoken notice validation, broader browser/assistive-technology testing, external widgets and voice/native interactions |
| Dynamic publishing | Actual fragment renderer exercised with a recorded update and held stale update, preserving published content | Production framework caching, navigation and asset lifecycle integration |
| Exports and provenance | Portable article/image HTML exports embed original raster bytes and preserve notices offline and in print styling; provider duties remain separate | Raw media, audio/video, PDF/Word and native/social exports; machine-readable provider marking and provenance validation |
| Minimal host integration | One five-step portable skill; project installer; standalone and dual-host archives; validated plugin schemas | Official catalog submissions and host-selection evaluation; no claim of automatic discovery in uninstalled sessions |
| Tests and safe operation | Python 3.9/3.13 Linux/macOS CI; browser job; local suite now 54 tests | Final verification against deployed customer integrations and remaining modalities |
| Website | Refreshed [owner-private Sites website](https://henrixbor-ai-disclosure.henrixbor.chatgpt.site) with alpha.2 downloads, catalog commands and current scope; deployment succeeded and returned current content | Decide public audience for launch; current access remains owner-only |
| Repository and release | Public [Henrixbor/ai-disclosure](https://github.com/Henrixbor/ai-disclosure); MIT licence, contribution/security guidance; immutable alpha.1 assets downloaded and hash-matched | Complete the remaining production gates before a stable release |
| Distribution | Real Claude catalog installation into temporary configuration, exactly one skill and no agents/hooks/servers; Codex project installer tested | Codex marketplace packaging/listing; official catalog acceptance not obtained |
| Go-to-market | Audience, pilots, positioning, channels, metrics, operating ownership and draft launch copy in `docs/go-to-market.md` | Pilot partners, independently reproduced integrations and approved external promotion |

## Current release

[0.1.0-alpha.2](https://github.com/Henrixbor/ai-disclosure/releases/tag/v0.1.0-alpha.2) is public, tied to source commit `e761ab7203c9b5994f00425fb6bfe785e23f54d1`. Its 46-test suite and all five GitHub jobs passed. Skill/plugin archives were validated, downloaded and hash-matched. Claude's catalog pins the alpha.2 archive SHA-256. Alpha.1 remains available unchanged.

## Completion boundary

The full objective remains open. No independent legal review has been obtained, no official marketplace listing is claimed, and no tool result certifies all website law. Complete the remaining engineering and deployment work, then audit every row with current authoritative evidence. Do not remove a requirement simply because an alpha can be published. Keep the existing Sites project; never recreate it.

Website deployment evidence: source `eedd40aacce1db75e4d550416085865f3a502877`, Sites version 2, successful deployment and authenticated HTTP 200 with current release/scope. That commit’s five CI jobs passed. No public access change has been made.

Unreleased main: portable document export is implemented and browser-tested offline with no external requests. The public catalog remains pinned to alpha.2 until the next validated release; do not describe these main changes as already installed for catalog users.

A [legal review package](docs/legal-review.md) maps the implemented decisions and sample outputs to specific questions for a qualified reviewer. The PDF fingerprint checker does not automate legal judgment. The public website-access question remains pending; the site stays owner-private.
