# Codex Cache Preservation Source

The preservation set is the union of plugin-version pairs that have appeared in `src/plugins/<plugin>/.claude-plugin/plugin.json` on the published branch within the last ten days, derived from `git log` of that manifest. The marketplace recipe `just push-marketplace` invokes the cache-preservation script, which accepts an injected plugin-history source exposing the working-tree plugin set, each plugin's versions published within the window — the default wrapping `git log` against the working tree's manifest — and each plugin's current working-tree manifest version, and computes the symlink set from that source's output rather than from a pre-upgrade cache snapshot. The compatibility-symlink target for each plugin is the cache directory whose name equals that plugin's current working-tree manifest version; absent a real directory of that name after the upgrade, the recipe creates no compatibility symlink for the plugin.

## Rationale

Two requirements collide: the preservation set must cover in-flight conversations, and the mechanism must survive a single missed invocation of the recipe. A set computed from the pre-upgrade cache snapshot satisfies the first only when every prior push captured its predecessor; a single push that bypasses the recipe drops the predecessor permanently. A set derived from git history satisfies both — every invocation recomputes from the published commits in the window, cache state is consequential output rather than input, and a bypassed push is repaired by the next invocation. The ten-day window covers a working week plus weekend margin while keeping the symlink set bounded. Pinning Codex resolution to the working tree diverges from the version-pathed lookup contract, and an external sidecar file introduces a second source of truth that drifts under exactly the bypass scenarios this decision addresses. Identifying the symlink target by the current working-tree version rather than by the newest cache directory keeps the target a function of the manifests, not of cache timestamps: a timestamp-selected target points the current version at a stale predecessor whenever an upgrade exits successfully without materializing the current version as a real directory, so the recipe instead creates no compatibility symlink for a plugin until its current version exists as a real directory.

## Invariants

- For any plugin `P` with manifest version `V` published to the marketplace branch within the last ten days, `~/.codex/plugins/cache/<marketplace>/P/V/` resolves to the current version directory or a symlink to it immediately after `just push-marketplace` completes.
- For any version `V` that is neither current nor present in the last ten days of `P`'s manifest history, `~/.codex/plugins/cache/<marketplace>/P/V/` does not exist after the recipe completes.
- The post-recipe cache state is a pure function of the published git history and the working-tree manifests, independent of the cache state observed before the recipe ran.
- The compatibility-symlink target for plugin `P` is the real cache directory named with `P`'s current working-tree manifest version; version identity selects the target, never directory modification time. Absent that real directory after the upgrade, no path under `~/.codex/plugins/cache/<marketplace>/P/` is created as a compatibility symlink, so no version resolves to a non-current directory's content.

## Verification

### Testing

- ALWAYS: the preservation script derives the preservation set per plugin from a published-versions callable parameterized by a time window — git history is authoritative, snapshot deltas are not ([property])
- ALWAYS: the default published-versions callable invokes `git log` against the working tree's manifest for the configured plugin, limited to a ten-day window ([compliance])
- ALWAYS: compatibility symlinks for plugin versions outside the window are pruned during the same recipe invocation that creates current-window symlinks ([property])
- ALWAYS: plugins absent from the working tree but present in cache have their entire cache directory pruned — orphaned plugins retain no compatibility paths ([property])
- ALWAYS: the compatibility-symlink target is the real cache directory whose name equals the plugin's current working-tree manifest version — version identity selects the target, never directory modification time ([property])
- NEVER: create a compatibility symlink for a plugin whose current working-tree version is absent as a real cache directory after the upgrade — a symlink to a non-current directory resolves the current version to stale content ([compliance])
- NEVER: compute the preservation set solely from the pre-upgrade snapshot delta — bypass a single recipe invocation and the chain breaks permanently ([property])
- NEVER: skip preservation when the git-history callable returns an empty set for a plugin — the empty set entails the orphan-prune behavior, not a silent skip ([compliance])

### Audit

- ALWAYS: the published-versions callable is injected as a Protocol parameter — enabling `l1` testing of preservation logic against controlled version sets without invoking real git ([audit])
- ALWAYS: each plugin's current working-tree version is exposed through the injected plugin-history Protocol — enabling `l1` testing of target identification against controlled versions without invoking real git ([audit])
- NEVER: substitute the published-versions callable in tests with `unittest.mock.patch` or framework mocks — dependency injection is the standard ([audit])
- NEVER: persist preservation state to disk outside the cache directory — git history is the source of truth; a sidecar file introduces drift ([audit])
