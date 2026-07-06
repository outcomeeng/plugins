# Runtime Marketplace Config Ownership

Maintainer marketplace sync owns the `outcomeeng` marketplace registration for Claude Code and Codex. Before any plugin refresh or cache reconciliation, the workflow reconciles both runtimes to the default-branch worktree root as the local marketplace source path. Cache reconciliation preserves every version already present in a plugin's cache by retargeting it to a direct symlink at the reconciliation target, so a Codex session started on any previously-installed version keeps resolving its advertised skill cache path.

## Rationale

Codex Git marketplace startup auto-upgrade force-reinstalls plugins and replaces a plugin's cache root with the staged current version. That behavior can delete versioned paths still referenced by running sessions. Local Codex marketplace sources are excluded from that startup auto-upgrade path, so maintainer sync repairs Git-backed, absent, or path-mismatched Codex registrations to a local source before refresh. Claude Code uses the same local source so both runtime surfaces resolve the same generated marketplace tree.

A Codex session resolves a plugin's skills through the cache path for the version installed when the session started, and that path must keep resolving for the session's lifetime, which can outlast many version bumps. Publication recency does not record which versions a session has resolved: a version's manifest commit can age past the window while a session still resolves that version, and an infrequently-changed plugin's previously-installed version need never fall inside the window at all. The cache directory does record which versions sessions have resolved, so reconciliation keys preservation on cache presence rather than publication age — it retargets every present version to a symlink at the reconciliation target instead of pruning by age. Compatibility symlinks cost almost nothing, and the set grows only until the plugin is removed or its cache rebuilt.

The managed Codex plugin set comes from `dist/codex/*/.codex-plugin/plugin.json`, so an empty, stale, or partially broken Codex installed-set report cannot prevent a generated plugin from being materialized or override the generated local manifest version as the refreshed plugin's reconciliation target. The workflow still reads `codex plugin list --json --marketplace <marketplace>` after refresh to learn resolved installed versions that may need compatibility symlinks. Validation reads the Codex marketplace version from the configured local source root, making stale Git clones under the Codex home directory irrelevant to maintainer validation.

## Invariants

- Maintainer sync reconciles Claude Code and Codex `outcomeeng` marketplace registrations to the default-branch worktree root as the same local source path before refresh.
- The set of addable Codex plugins is the sorted set of plugin manifests under `dist/codex/*/.codex-plugin/plugin.json`.
- The set of refreshed plugins is the working-tree plugin set intersected with the addable `dist/codex` plugin set.
- Each refreshed plugin is reinstalled by `codex plugin add <plugin>@outcomeeng`; maintainer sync never runs `codex plugin marketplace upgrade outcomeeng`.
- When Claude Code source repair removes an existing `outcomeeng` marketplace registration, maintainer sync snapshots installed user-scope `outcomeeng` Claude Code plugins first and restores each plugin's enabled state after re-adding the local marketplace source through the user registration path; project/local plugin selections are not restored by maintainer sync.
- The post-refresh cache topology is a pure function of the version paths already present in the plugin's cache directory, the published git history, the working-tree manifests, the addable `dist/codex` manifests, and the Codex-reported installed versions.
- A refreshed plugin's reconciliation target is the version declared by `dist/codex/<plugin>/.codex-plugin/plugin.json`; a non-refreshed installed plugin's reconciliation target is the Codex-reported installed version.
- For any installed plugin `P` whose reconciliation target exists as a complete real directory after refresh, `~/.codex/plugins/cache/<marketplace>/P/` contains exactly one real version directory after reconciliation: the reconciliation target. Every other version path — whether it was already present in the cache, is a published-in-window version recreated for chain recovery, or is a stale post-refresh Codex-reported version, and whether it was a real directory or a symlink — is a direct symlink to that directory.
- No version path already present in a plugin's cache is removed for falling outside the publication window; a present non-target version is retargeted to a direct symlink at the reconciliation target rather than pruned. The publication window only adds symlinks for in-window versions absent from the cache; it never subtracts a present one.
- Each preserved compatibility symlink's modification time is refreshed on every reconciliation, so a stale-symlink check over the cache measures time since the last reconciliation rather than time since the version was published.
- When all plugin adds complete successfully, for any plugin `P` outside the refreshed set, `~/.codex/plugins/cache/<marketplace>/P/` does not exist after reconciliation.
- When a plugin add exits non-zero, cache entries for plugins whose adds were not attempted remain untouched.

## Verification

### Testing

- ALWAYS: source reconciliation accepts matching Claude Directory and Codex local marketplace sources for `outcomeeng` without repair ([conformance])
- ALWAYS: source reconciliation replaces a Git-backed Codex marketplace source for `outcomeeng` with the canonical local source before refresh ([conformance])
- ALWAYS: source reconciliation replaces mismatched Claude Code or Codex local marketplace paths with the canonical local source before refresh ([conformance])
- ALWAYS: an explicit canonical source root replaces stale local marketplace paths in both runtimes before refresh ([conformance])
- ALWAYS: Claude Code source repair preserves installed user-scope `outcomeeng` plugin selections by restoring each plugin's enabled state after re-adding the local marketplace source through the user registration path, while project/local plugin selections are not restored by maintainer sync ([conformance])
- ALWAYS: source reconciliation adds an absent Claude Code or Codex `outcomeeng` marketplace registration from the canonical local source before refresh ([conformance])
- ALWAYS: the addable Codex plugin set is read from `dist/codex/*/.codex-plugin/plugin.json`, sorted by plugin name ([conformance])
- Given generated Codex plugin manifests and an installed-set query, local refresh invokes `codex plugin add <plugin>@outcomeeng` for refreshed plugins in deterministic manifest order ([scenario])
- NEVER: local refresh invokes `codex plugin marketplace upgrade outcomeeng` ([compliance])
- ALWAYS: a version path present in the cache outside the publication window is retargeted to a direct symlink at the reconciliation target during reconciliation, never pruned for age ([property])
- ALWAYS: every version present in a plugin's cache other than the reconciliation target resolves to a direct symlink at the target directory after reconciliation, whether it was a real directory or a symlink before ([property])
- ALWAYS: each preserved compatibility symlink's modification time is refreshed on every reconciliation so a stale-symlink check over the cache measures time since the last reconciliation, not time since publication ([property])
- ALWAYS: plugins outside the managed generated Codex plugin set have their entire cache directory pruned after all plugin adds complete successfully ([property])
- Given a non-zero plugin add after one successful plugin add, cache reconciliation repairs the successfully refreshed plugin and leaves cache entries for plugins whose adds were not attempted untouched ([scenario])
- ALWAYS: the compatibility-symlink target is the complete real cache directory whose name equals the plugin's reconciliation target ([property])
- NEVER: leave or create a compatibility symlink for a plugin whose reconciliation target is absent as a complete real cache directory after refresh ([compliance])
- ALWAYS: incomplete in-window compatibility roots are replaced with direct symlinks to the complete reconciliation target directory ([property])
- ALWAYS: the installed set is parsed from `codex plugin list --json` output as the `name` and `version` of each entry in the `installed` array, scoped to the queried marketplace, for post-refresh resolved-version reconciliation ([property])
- NEVER: mutate the cache when the installed-set query fails or returns an unrecognized shape ([compliance])
- Given a configured local Codex marketplace source root and a stale historical Git clone under the Codex home directory, validate_install reads Codex marketplace versions from the configured local source root, including `dist/codex` manifests ([scenario])

### Audit

- ALWAYS: the source discovery parser is injected behind a command-runner boundary, enabling l1 verification without invoking Claude Code or Codex ([audit])
- ALWAYS: the installed-set provider is injected as a Protocol parameter, enabling l1 testing of refreshed-set selection without invoking the real Codex CLI ([audit])
- ALWAYS: each plugin's current working-tree version remains exposed through the injected plugin-history Protocol while target selection uses the injected installed-version provider ([audit])
- NEVER: persist preservation state to disk outside the cache directory ([audit])
