# AI Disclosure plugin — development release

One shared skill for Codex and Claude Code, with local assessment and publishing tools. Python 3.9+ is needed to run the bundled scripts. The host agent supplies repository editing and browser verification.

Ask: **Fix this site's AI disclosure requirements with the least intrusive appropriate notices. Use ai-disclosure and verify the result.**

The skill inspects content sources, records established facts, implements supported disclosures and verifies the rendered result. It does not infer authorship from prose, certify legal compliance or cover every website law. Future content requires publishing integration; installing the skill alone is not a background service.

Supported tools include static article/image notices, local chat interaction wrappers, a Node publishing client, portable article/image HTML exports and experimental media controls. The publishing reference also links to the repository-only Next.js example and WordPress development integration; neither is installed by this archive. External widgets, arbitrary runtime frameworks, raw media/PDF/Word exports and provider marking remain integration gaps. Independent legal review has not been obtained.

This archive contains `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, one `skills/ai-disclosure` directory and the MIT licence. It has no account, API key, MCP server, install hook, telemetry or automatic update code. Your chosen agent host's own data handling still applies. The browser media helper only requests the configured local media files.

For installation options, limitations, examples and updates, see [the source repository](https://github.com/Henrixbor/ai-disclosure). Review changes before updating production integrations. Official marketplace inclusion has not been obtained.
