# Distribution

AI Disclosure maintains one skill under `skills/ai-disclosure`. Archive layouts serve different installation routes:

| Archive | Layout and use |
| --- | --- |
| `ai-disclosure-skill.zip` | `ai-disclosure/SKILL.md` and its bundled tools. Extract into the agent's skills directory, or use the repository's project installer. |
| `ai-disclosure-plugin.zip` | `ai-disclosure/.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `skills/ai-disclosure`, README and licence. For plugin loaders and catalog maintainers. |
| `ai-disclosure-wordpress.zip` | Experimental PHP text plugin for a WordPress test site. It contains no agent skill or migration CLI. Available when explicitly included in a release; follow the [WordPress guide](../integrations/wordpress/README.md) before activation. |

Download versioned assets from [GitHub releases](https://github.com/Henrixbor/ai-disclosure/releases). Development versions are prereleases, not a production/legal-compliance guarantee. Compare downloaded files against `SHA256SUMS` from the same release, for example with `shasum -a 256 -c SHA256SUMS`. Checksums detect changed bytes; they are not a signature or an independent trust guarantee.

Current prerelease: [0.1.0-alpha.3](https://github.com/Henrixbor/ai-disclosure/releases/tag/v0.1.0-alpha.3), with all three archives. The owner-maintained Claude catalog pins its plugin ZIP and SHA-256; this is not an official host catalog listing.

## Project installation

The shortest supported route for both Codex and Claude Code remains:

```sh
python3 scripts/install.py --project /absolute/path/to/your-site
```

This installs into that project's skill directories. Do not install both a project skill and the same plugin unless you intentionally want two discoverable copies. Future-content coverage still requires integration with the project's publishing pipeline.

Claude Code v2.1.224+ can install the checksum-pinned alpha through this repository's catalog:

```sh
claude plugin marketplace add Henrixbor/ai-disclosure
claude plugin install ai-disclosure@henrixbor-ai-disclosure
```

This is Henrixbor's catalog, not an official Anthropic listing. The catalog points to the versioned public archive and pins its SHA-256. Restart or reload plugins as directed by Claude. See [archive source requirements](https://code.claude.com/docs/en/plugin-marketplaces#zip-archives).

For Claude Code local plugin testing, extract the plugin archive and launch `claude --plugin-dir /absolute/path/to/ai-disclosure`. The plugin skill is namespaced `/ai-disclosure:ai-disclosure`. Project-installed skills use `/ai-disclosure`. See [Claude's plugin documentation](https://code.claude.com/docs/en/plugins).

The Codex plugin manifest is validated against the bundled plugin schema. This repository has not been admitted to an official catalog, and the archive alone does not configure a Codex marketplace. Use the project installer for working Codex installation today. Do not advertise nonexistent marketplace installation commands or imply OpenAI/Anthropic endorsement.

## Maintainer release procedure

1. Bump both plugin manifests to the same semantic version. Do not replace an existing version's assets with different content.
2. Run Python and browser tests, build the skill/plugin archives and any included WordPress archive, extract them, validate both host manifests and execute the extracted tools. Verify the WordPress archive through its documented installation checks.
3. Commit and push the exact source. Wait for that commit's GitHub checks to succeed.
4. Create a GitHub release tied to that commit, upload the verified archives and SHA256SUMS, and mark development versions as prereleases. State which tooling remains repository-only.
5. Download the public assets and compare their hashes with the locally verified files. Record the release URL and remaining limitations.

```sh
python3 scripts/package_skill.py --format skill --output release/ai-disclosure-skill.zip
python3 scripts/package_skill.py --format plugin --output release/ai-disclosure-plugin.zip
```

Archive generation is reproducible and uses an explicit file allowlist. Tests, media fixtures, website files, repository state and local evidence are excluded. Plugin assets contain only the shared skill plus manifests, README and licences. Release publishing is a maintainer action; nothing in the installed skill performs automatic updates or external publication.
