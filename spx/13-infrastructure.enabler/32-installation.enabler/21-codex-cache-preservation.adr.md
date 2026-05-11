# Codex Cache Preservation Source

## Purpose

This decision governs the source of truth for which plugin-version paths the marketplace preserves in the Codex cache after a `marketplace upgrade`. It bounds preservation to a recent window and makes the preservation set independent of cache state.

## Context

**Business impact:** Codex resolves plugin paths from `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`. A `marketplace upgrade` removes plugin directories whose versions differ from the latest published manifest. An in-flight Codex conversation that loaded skills under a removed path loses those references mid-session — every subsequent skill invocation against that version fails. The marketplace owns the contract that keeps recently-published paths resolvable so day-to-day developer sessions survive marketplace refreshes.

**Technical constraints:** The marketplace publishes plugin versions by committing `plugins/<plugin>/.claude-plugin/plugin.json` and `plugins/<plugin>/.codex-plugin/plugin.json` (in lockstep, per `spx/13-plugin-and-runtime-conventions.adr.md`) to the published branch. The Codex marketplace clone in `~/.codex/.tmp/marketplaces/<marketplace>/` tracks that branch and publishes only the latest committed version per plugin. The plugin cache directory contains, at any moment, the latest published version as a real directory plus any compatibility paths the marketplace recipe creates. The recipe `just push-marketplace` is the only sanctioned invocation surface for cache mutation.

## Decision

The preservation set is the union of plugin-version pairs that have appeared in `plugins/<plugin>/.claude-plugin/plugin.json` on the published branch within the last ten days, derived from `git log` of that manifest.

## Rationale

Two requirements collide: the preservation set must include enough history to cover in-flight conversations, and the mechanism must survive a single missed invocation of the marketplace recipe.

A preservation set computed from the pre-upgrade cache snapshot satisfies the first requirement only when every prior push correctly captured its predecessor into the cache. A single push that bypasses the recipe — manual `codex plugin marketplace upgrade`, a CI workflow that skips the wrapper, a marketplace refresh triggered by another tool — drops the predecessor from the cache. Subsequent recipe invocations see a smaller pre-upgrade snapshot than the published history; the dropped versions never return. The chain is fragile and irrecoverable.

A preservation set derived from git history of the manifest satisfies both requirements. Every recipe invocation recomputes the set from the same source of truth: the published commits within the window. Cache state is consequential output, not input. A bypassed push has no permanent effect: the next recipe invocation restores the dropped paths. The decision flow is idempotent.

The ten-day window covers typical developer session lifetimes — a working week plus weekend margin — while remaining narrow enough that the symlink set stays bounded for plugins under active development. Versions outside the window are pruned because they fall outside any reasonable in-flight conversation scope.

Two alternatives were rejected. The first — pin Codex resolution to the working tree, mirroring the Claude Code resolver — diverges from the Codex version-pathed lookup contract; the resolver is part of Codex's interface, not a marketplace concern. The second — maintain an external sidecar file recording preserved versions — introduces a second source of truth that drifts under exactly the bypass scenarios this decision exists to address; git history already carries the authoritative record.

## Trade-offs accepted

| Trade-off                                                                                                      | Mitigation / reasoning                                                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The recipe runs `git log` per plugin manifest on every invocation                                              | Git invocations remain bounded by the plugin count; the recipe already shells out to `git`, `claude`, and `codex` per push, so the added cost is small and identical across pushes                             |
| Conversations older than ten days that reference an older plugin version break                                 | Ten days covers a working week plus weekend margin; conversations that survive longer belong to the runtime's session lifecycle, not the marketplace's preservation contract                                   |
| Git history must be available on the local working tree when the recipe runs                                   | The recipe is documented as running inside the marketplace repository's working tree; CI configurations and developer machines satisfy this constraint by construction                                         |
| Renames to manifest files (e.g., relocating `plugins/<plugin>/`) lose their history without `git log --follow` | The git walker uses `--follow` and treats discontinuities as boundaries that limit but do not corrupt the preservation set; structural renames are rare and explicit                                           |
| A plugin removed from the marketplace continues to receive symlinks for ten days under its last known target   | The pruner discards the directory entirely once no version remains in the window; ten-day persistence after removal is consistent with the in-flight-conversation rationale that motivates preservation at all |

## Invariants

- For any plugin `P` with manifest version `V` published to the marketplace branch within the last ten days, `~/.codex/plugins/cache/<marketplace>/P/V/` resolves to either the real current version directory or a symlink to it, immediately after `just push-marketplace` completes.
- For any version `V` that is neither current nor present in the last ten days of `P`'s manifest history, `~/.codex/plugins/cache/<marketplace>/P/V/` does not exist after `just push-marketplace` completes.
- The post-recipe cache state is a pure function of the published git history and the working-tree manifests, independent of the cache state observed before the recipe ran.

## Compliance

### Recognized by

The marketplace recipe `just push-marketplace` invokes the cache-preservation script. The script accepts a callable that returns, for each plugin in the working tree, the set of versions published to the manifest within the configured window. The default callable wraps `git log` against `plugins/<plugin>/.claude-plugin/plugin.json`. The script's cache-restoration loop computes the symlink set from the callable's output, not from the BEFORE-snapshot delta. Tests substitute the callable with explicit Protocol implementations.

### MUST

- The preservation script derives the preservation set per plugin from a published-versions callable parameterized by a time window — git history is the authoritative source, snapshot deltas are not ([review])
- The published-versions callable is injected as a Protocol parameter — enables `l1` testing of preservation logic against controlled version sets without invoking real git ([review])
- The default published-versions callable invokes `git log` against the working tree's manifest file for the configured plugin, limited to a ten-day window — git is `l1` infrastructure per `spx/15-test-language.adr.md` ([review])
- Compatibility symlinks for plugin versions outside the window are pruned during the same recipe invocation that creates current-window symlinks — bounded preservation set ([review])
- Plugins absent from the working tree but present in cache have their entire cache directory pruned — orphaned plugins do not retain compatibility paths ([review])

### NEVER

- Compute the preservation set solely from the BEFORE-snapshot delta — bypass a single recipe invocation and the chain breaks permanently ([review])
- Substitute the published-versions callable in tests with `unittest.mock.patch` or framework mocks — violates the dependency-injection standard from `/standardizing-python-tests` ([review])
- Skip preservation when the git-history callable returns an empty set for a plugin — the empty set means no versions in the window, which entails the orphan-prune behavior, not silent skip ([review])
- Persist preservation state to disk outside the cache directory — git history is the source of truth; a sidecar file introduces drift ([review])
