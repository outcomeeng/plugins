# Codex Local Refresh Source

Maintainer Codex refreshes use the same local marketplace source that Claude Code uses for `outcomeeng`. Before any Codex plugin refresh or cache reconciliation, the workflow verifies that Codex reports `outcomeeng` as a local marketplace and that its path equals Claude Code's Directory source path. The Codex refresh operation reinstalls each installed plugin from that local source with `codex plugin add <plugin>@outcomeeng`; the cache reconciliation step then repairs compatibility symlinks from git history and the Codex-reported installed versions.

## Rationale

Codex Git marketplace startup auto-upgrade force-reinstalls plugins and replaces a plugin's cache root with the staged current version. That behavior can delete versioned paths still referenced by running sessions. Local Codex marketplace sources are excluded from that startup auto-upgrade path, so maintainer machines use the local marketplace source for sync. Refreshing each installed plugin with `codex plugin add <plugin>@outcomeeng` updates Codex's installed plugin materialization from the validated local source while preserving the recipe's explicit post-refresh compatibility-link repair.

The installed set remains Codex's authority: the workflow reads `codex plugin list --json --marketplace <marketplace>` and refreshes the installed plugins whose manifests exist under `dist/codex`. The available plugin set comes from `dist/codex/*/.codex-plugin/plugin.json`, so the maintainer workflow follows the generated marketplace tree and never embeds a separate plugin-name list. A Git-backed Codex registration or a local-source path mismatch is configuration drift, so the workflow fails before mutation and reports the mismatch. Validation reads the Codex marketplace version from the configured local source root, making stale Git clones under the Codex home directory irrelevant to maintainer validation.

## Invariants

- The maintainer Codex marketplace source for `outcomeeng` is local, and its path equals Claude Code's Directory source path for `outcomeeng`.
- The set of addable Codex plugins is the sorted set of plugin manifests under `dist/codex/*/.codex-plugin/plugin.json`.
- The set of refreshed plugins is the intersection of Codex's installed set, the working-tree plugin set, and the addable `dist/codex` plugin set.
- Each refreshed plugin is reinstalled by `codex plugin add <plugin>@outcomeeng`; maintainer sync never runs `codex plugin marketplace upgrade outcomeeng`.
- The post-refresh cache state is a pure function of the published git history, the working-tree manifests, the addable `dist/codex` manifests, and the Codex-reported installed versions.
- For any installed plugin `P` whose Codex-reported installed version exists as a complete real directory after refresh, `~/.codex/plugins/cache/<marketplace>/P/` contains exactly one real version directory after reconciliation: the Codex-reported installed version. Every other in-window version path is a direct symlink to that directory, and every other real version directory is removed.
- For any plugin `P` outside the refreshed set, `~/.codex/plugins/cache/<marketplace>/P/` does not exist after reconciliation.

## Verification

### Testing

- ALWAYS: the source preflight accepts matching Claude Directory and Codex local marketplace sources for `outcomeeng` ([conformance])
- ALWAYS: the source preflight rejects a Git-backed Codex marketplace source for `outcomeeng` before any Codex plugin add or cache prune can occur ([conformance])
- ALWAYS: the source preflight rejects mismatched Claude and Codex local marketplace paths and names both paths in the diagnostic ([conformance])
- ALWAYS: the addable Codex plugin set is read from `dist/codex/*/.codex-plugin/plugin.json`, sorted by plugin name ([conformance])
- ALWAYS: local refresh invokes `codex plugin add <plugin>@outcomeeng` for refreshed installed plugins in deterministic manifest order ([scenario])
- NEVER: local refresh invokes `codex plugin marketplace upgrade outcomeeng` ([scenario])
- ALWAYS: compatibility symlinks for plugin versions outside the window are pruned during the same recipe invocation that creates current-window symlinks ([property])
- ALWAYS: plugins outside the refreshed set have their entire cache directory pruned ([property])
- ALWAYS: the compatibility-symlink target is the complete real cache directory whose name equals the plugin's Codex-reported installed version ([property])
- NEVER: leave or create a compatibility symlink for a plugin whose Codex-reported installed version is absent as a complete real cache directory after refresh ([compliance])
- ALWAYS: incomplete in-window compatibility roots are replaced with direct symlinks to the complete Codex-reported installed version directory ([property])
- ALWAYS: the installed set is parsed from `codex plugin list --json` output as the `name` and `version` of each entry in the `installed` array, scoped to the queried marketplace ([property])
- NEVER: mutate the cache when the installed-set query fails or returns an unrecognized shape ([compliance])
- ALWAYS: validate_install reads Codex marketplace versions from the configured local marketplace source root, including `dist/codex` manifests, rather than from the historical Git clone location under the Codex home directory ([scenario])

### Audit

- ALWAYS: the source discovery parser is injected behind a command-runner boundary, enabling l1 verification without invoking Claude Code or Codex ([audit])
- ALWAYS: the installed-set provider is injected as a Protocol parameter, enabling l1 testing of refreshed-set selection without invoking the real Codex CLI ([audit])
- ALWAYS: each plugin's current working-tree version remains exposed through the injected plugin-history Protocol while target selection uses the injected installed-version provider ([audit])
- NEVER: persist preservation state to disk outside the cache directory ([audit])
