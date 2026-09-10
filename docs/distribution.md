# Distribution

AI Disclosure maintains one skill under `skills/ai-disclosure`. Two archive layouts serve different installation routes:

| Archive | Layout and use |
| --- | --- |
| `ai-disclosure-skill.zip` | `ai-disclosure/SKILL.md` and its bundled tools. Extract into the agent's skills directory, or use the repository's project installer. |
| `ai-disclosure-plugin.zip` | `ai-disclosure/.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `skills/ai-disclosure`, README and licence. For plugin loaders and catalog maintainers. |

Download versioned assets from [GitHub releases](https://github.com/Henrixbor/ai-disclosure/releases). Development versions are prereleases, not a production/legal-compliance guarantee. Compare downloaded files against `SHA256SUMS` from the same release, for example with `shasum -a 256 -c SHA256SUMS`. Checksums detect changed bytes; they are not a signature or an independent trust guarantee.

## Project installation

The shortest supported route for both Codex and Claude Code remains:

```sh
python3 scripts/install.py --project /absolute/path/to/your-site
```

This installs into that project's skill directories. Do not install both a project skill and the same plugin unless you intentionally want two discoverable copies. Future-content coverage still requires integration with the project's publishing pipeline.

For Claude Code local plugin testing, extract the plugin archive and launch `claude --plugin-dir /absolute/path/to/ai-disclosure`. The plugin skill is namespaced `/ai-disclosure:ai-disclosure`. Project-installed skills use `/ai-disclosure`. See [Claude's plugin documentation](https://code.claude.com/docs/en/plugins).

The Codex plugin manifest is validated against the bundled plugin schema. This repository has not been admitted to an official catalog, and the archive alone does not configure a Codex marketplace. Use the project installer for working Codex installation today. Do not advertise nonexistent marketplace installation commands or imply OpenAI/Anthropic endorsement.

## Maintainer release procedure

1. Bump both plugin manifests to the same semantic version. Do not replace an existing version's assets with different content.
2. Run Python and browser tests, build both archives, extract them, validate both host manifests and execute the extracted tools.
3. Commit and push the exact source. Wait for that commit's GitHub checks to succeed.
4. Create a GitHub release tied to that commit, upload both archives and SHA256SUMS, and mark development versions as prereleases.
5. Download the public assets and compare their hashes with the locally verified files. Record the release URL and remaining limitations.

```sh
python3 scripts/package_skill.py --format skill --output release/ai-disclosure-skill.zip
python3 scripts/package_skill.py --format plugin --output release/ai-disclosure-plugin.zip
```

Archive generation is reproducible and uses an explicit file allowlist. Tests, media fixtures, website files, repository state and local evidence are excluded. Plugin assets contain only the shared skill plus manifests, README and licences. Release publishing is a maintainer action; nothing in the installed skill performs automatic updates or external publication.
