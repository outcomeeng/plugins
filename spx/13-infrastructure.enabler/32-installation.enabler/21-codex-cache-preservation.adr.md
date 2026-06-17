# Runtime Marketplace Config Ownership

Maintainer marketplace sync owns the `outcomeeng` marketplace registration for Claude Code and Codex. Before any plugin refresh or cache reconciliation, the workflow reconciles both runtimes to the running repository root as the local marketplace source path. The Codex refresh operation reinstalls each generated Codex plugin exposed by that local source with `codex plugin add <plugin>@outcomeeng`; the cache reconciliation step then repairs compatibility symlinks from git history and the Codex-reported installed versions.

## Rationale

Codex Git marketplace startup auto-upgrade force-reinstalls plugins and replaces a plugin's cache root with the staged current version. That behavior can delete versioned paths still referenced by running sessions. Local Codex marketplace sources are excluded from that startup auto-upgrade path, so maintainer sync repairs Git-backed, absent, or path-mismatched Codex registrations to a local source before refresh. Claude Code uses the same local source so both runtime surfaces resolve the same generated marketplace tree.

The managed Codex plugin set comes from `dist/codex/*/.codex-plugin/plugin.json`, so an empty, stale, or partially broken Codex installed-set report cannot prevent a generated plugin from being materialized. The workflow still reads `codex plugin list --json --marketplace <marketplace>` after refresh to learn the resolved installed versions that cache reconciliation verifies. Validation reads the Codex marketplace version from the configured local source root, making stale Git clones under the Codex home directory irrelevant to maintainer validation.

## Invariants

- Maintainer sync reconciles Claude Code and Codex `outcomeeng` marketplace registrations to the running repository root as the same local source path before refresh.
- The set of addable Codex plugins is the sorted set of plugin manifests under `dist/codex/*/.codex-plugin/plugin.json`.
- The set of refreshed plugins is the working-tree plugin set intersected with the addable `dist/codex` plugin set.
- Each refreshed plugin is reinstalled by `codex plugin add <plugin>@outcomeeng`; maintainer sync never runs `codex plugin marketplace upgrade outcomeeng`.
- The post-refresh cache state is a pure function of the published git history, the working-tree manifests, the addable `dist/codex` manifests, and the Codex-reported installed versions.
- For any installed plugin `P` whose Codex-reported installed version exists as a complete real directory after refresh, `~/.codex/plugins/cache/<marketplace>/P/` contains exactly one real version directory after reconciliation: the Codex-reported installed version. Every other in-window version path is a direct symlink to that directory, and every other real version directory is removed.
- When all plugin adds complete successfully, for any plugin `P` outside the refreshed set, `~/.codex/plugins/cache/<marketplace>/P/` does not exist after reconciliation.
- When a plugin add exits non-zero, cache entries for plugins whose adds were not attempted remain untouched.

## Verification

### Testing

- ALWAYS: source reconciliation accepts matching Claude Directory and Codex local marketplace sources for `outcomeeng` without repair ([conformance])
- ALWAYS: source reconciliation replaces a Git-backed Codex marketplace source for `outcomeeng` with the canonical local source before refresh ([conformance])
- ALWAYS: source reconciliation replaces mismatched Claude Code or Codex local marketplace paths with the canonical local source before refresh ([conformance])
- ALWAYS: an explicit canonical source root replaces stale local marketplace paths in both runtimes before refresh ([conformance])
- ALWAYS: source reconciliation adds an absent Claude Code or Codex `outcomeeng` marketplace registration from the canonical local source before refresh ([conformance])
- ALWAYS: the addable Codex plugin set is read from `dist/codex/*/.codex-plugin/plugin.json`, sorted by plugin name ([conformance])
- Given generated Codex plugin manifests and an installed-set query, local refresh invokes `codex plugin add <plugin>@outcomeeng` for refreshed plugins in deterministic manifest order ([scenario])
- NEVER: local refresh invokes `codex plugin marketplace upgrade outcomeeng` ([compliance])
- ALWAYS: compatibility symlinks for plugin versions outside the window are pruned during the same recipe invocation that creates current-window symlinks ([property])
- ALWAYS: plugins outside the managed generated Codex plugin set have their entire cache directory pruned after all plugin adds complete successfully ([property])
- Given a non-zero plugin add after one successful plugin add, cache reconciliation repairs the successfully refreshed plugin and leaves cache entries for plugins whose adds were not attempted untouched ([scenario])
- ALWAYS: the compatibility-symlink target is the complete real cache directory whose name equals the plugin's Codex-reported installed version ([property])
- NEVER: leave or create a compatibility symlink for a plugin whose Codex-reported installed version is absent as a complete real cache directory after refresh ([compliance])
- ALWAYS: incomplete in-window compatibility roots are replaced with direct symlinks to the complete Codex-reported installed version directory ([property])
- ALWAYS: the installed set is parsed from `codex plugin list --json` output as the `name` and `version` of each entry in the `installed` array, scoped to the queried marketplace, for post-refresh resolved-version reconciliation ([property])
- NEVER: mutate the cache when the installed-set query fails or returns an unrecognized shape ([compliance])
- Given a configured local Codex marketplace source root and a stale historical Git clone under the Codex home directory, validate_install reads Codex marketplace versions from the configured local source root, including `dist/codex` manifests ([scenario])

### Audit

- ALWAYS: the source discovery parser is injected behind a command-runner boundary, enabling l1 verification without invoking Claude Code or Codex ([audit])
- ALWAYS: the installed-set provider is injected as a Protocol parameter, enabling l1 testing of refreshed-set selection without invoking the real Codex CLI ([audit])
- ALWAYS: each plugin's current working-tree version remains exposed through the injected plugin-history Protocol while target selection uses the injected installed-version provider ([audit])
- NEVER: persist preservation state to disk outside the cache directory ([audit])
