# AI Disclosure

Minimal AI disclosure guidance for coding agents. Ask an agent to inspect a site, apply appropriate notices and verify the result without adding unnecessary banners.

**Status: local development release.** Includes one portable skill, dependency-free assessment and HTML publishing tools, and a project installer. Article/image output is implemented; an experimental local audio/video player is in development, and a local chat wrapper renders interaction notices. A shared fragment renderer supports CMS/server integration; framework-specific adapters remain incomplete. Versioned development archives are available through GitHub releases; no hosted compliance service is provided. Rules have not been reviewed by counsel; the [legal review package](docs/legal-review.md) identifies the decisions and evidence needed. Assessment output is not legal certification.

## Install into a project

Clone [Henrixbor/ai-disclosure](https://github.com/Henrixbor/ai-disclosure). From the checkout, with Python 3.9+:

```sh
python3 scripts/install.py --project /absolute/path/to/your-site
```

This installs the same self-contained skill for Codex and Claude Code. Use `--agent codex` or `--agent claude` to select one. Identical installs are harmless; differing existing skills are left untouched and reported. It does not change global settings or publish anything. Commit the installed skill with the project if the team should have it. Start a fresh session if it is not listed.

Then ask:

> Fix this site's AI disclosure requirements with the least intrusive appropriate notices. Use ai-disclosure and verify the result.

Explicit invocation: `$ai-disclosure` in Codex; `/ai-disclosure` in Claude Code. A broader request such as “fix the legal requirements” may select the installed skill for its AI-transparency part, but selection is not guaranteed and other legal requirements remain separate.

## What the agent does

1. Inspect the site's content and publishing flows; reuse existing notices.
2. Establish origin and context, preserving unknowns rather than guessing.
3. Assess supported publisher facts with the bundled helper.
4. Edit the site's own components and publishing hooks.
5. Test rendered disclosures and record unresolved coverage.

The skill entrypoint stays short; legal distinctions and input details load from references. The host agent supplies repository editing and browser tools. Python is needed only for installation and the assessment helper. No API key, model SDK, MCP server, runtime dependency or visitor tracking is required by this package.

The assessment helper accepts declared facts and never edits the site. The [HTML publishing adapter](skills/ai-disclosure/references/publishing.md) inventories bindings, records actual content versions and renders article/image notices into a fresh local output directory. It rejects stale facts and unresolved cases. The agent is responsible for integration and browser verification. Future content is covered only after the site's publishing process is integrated; an installed skill is not a background process.

## Discovery and distribution

An arbitrary session cannot reliably discover an unpublished or uninstalled repository. Use explicit installation first, then make discovery easier:

| Channel | Approach |
|---|---|
| Codex projects | Install under `.agents/skills/ai-disclosure`. |
| Claude Code projects | Install under `.claude/skills/ai-disclosure`. |
| Personal sessions | Users can copy the same folder to `~/.agents/skills/` or `~/.claude/skills/`, respectively. Local installation does not automatically propagate to cloud sessions. |
| Public repository | Publish a stable repository URL, concise README, skill metadata and examples. Search ranking and implicit selection are not guarantees. |
| Plugins / marketplaces | A dual-host plugin archive packages this same skill with validated Codex and Claude manifests. Official marketplace listing requires separate submission and acceptance. See [distribution](docs/distribution.md). |
| Framework / CMS templates | Later bundle supported publishing integrations and the skill so new projects start with them. |

Discovery sources checked 2026-09-10: [Codex skill documentation](https://learn.chatgpt.com/docs/build-skills), [Claude Code skill documentation](https://code.claude.com/docs/en/skills). Both support descriptions for implicit selection. Neither makes a public Git repository automatically available to every session.

Release work is tracked in [the release plan](RELEASE-PLAN.md). The original software uses the [MIT licence](LICENSE); linked third-party legal sources retain their own terms. The [go-to-market plan](docs/go-to-market.md) covers pilots, distribution, launch copy and metrics. Add MCP only when access to a shared remote registry justifies a server.

## Development

```sh
python3 -m unittest discover -s tests -v
```

The public [Checks workflow](https://github.com/Henrixbor/ai-disclosure/actions/workflows/checks.yml) runs Python tests on Linux/macOS and browser checks on the generated demo. For local browser checks, follow [CONTRIBUTING.md](CONTRIBUTING.md).

To create a standalone skill archive, run `python3 scripts/package_skill.py --output release/ai-disclosure.zip`. It includes the instructions, references, scripts and licence, with reproducible contents and a printed SHA-256 digest. Extract the `ai-disclosure` folder into the relevant agent's skills directory. A packaged development build is not a production certification.

Tests cover declared decisions, uncertainty, stale review, role gaps, invalid input, CLI exit codes and installation preservation. They do not test real model skill selection or a production site's visual/legal compliance.

See [the skill](skills/ai-disclosure/SKILL.md), [assessment input](skills/ai-disclosure/references/manifest.md), and [research brief](research/product-feasibility.md).

The [distribution guide](docs/distribution.md) covers standalone skill and plugin archives, versioning and verification. Development releases are explicitly marked as prereleases.

Unreleased main also includes portable article/image HTML export with embedded raster assets. Catalog installations remain on the versioned release shown in the distribution guide; consult the release audit for current development differences.

JavaScript publishing workers on unreleased main can use the optional [Node client](skills/ai-disclosure/references/publishing.md#javascript-publishing-client) to inspect, render and export in memory. It calls the existing Python engine at publishing time, requires no npm dependencies, and holds unresolved updates. Framework-specific installation, transactions and caching still need integration.

The runnable [Next.js static export example](examples/nextjs/README.md) integrates that client into the actual build configuration. It keeps facts private, emits the notice before JavaScript runs, and stops a stale-content build. This covers the demonstrated static publishing flow; it does not automatically integrate other routes or a CMS.

The [experimental WordPress text plugin](integrations/wordpress/README.md) runs a native PHP engine with private evidence recording and publication gates. Its live WordPress tests cover the documented REST/native update paths and text notices. It is intended for isolated integration testing while amendment, editor and broader content workflows remain incomplete.
