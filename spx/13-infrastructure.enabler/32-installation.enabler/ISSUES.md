# Issues: Installation Enabler

## 1. Cache listing shows no `← current` for a working-tree-pinned plugin ahead of its cache (FOLLOW-UP)

`print_cache` / `cached_entries` (`outcomeeng/validation/install.py`) mark `← current` on the cache directory whose name equals the working-tree manifest version. For the Claude Code cache, resolution is working-tree-pinned (see `21-codex-cache-preservation.adr.md`), so the cache directories are an informational record, not the resolution source. When the working tree advances past every cached version directory (the cache updates lazily), no directory name matches the working-tree version, so the plugin shows no `← current` marker at all — making an up-to-date, correctly-resolving install look stale.

Observed: spec-tree resolved to the working-tree version while its cache directories topped out two patch versions behind, so the listing showed every other plugin's `← current` but none for spec-tree.

This is a display-semantics question, not a resolution defect — resolution is correct. The decision for whoever next touches the listing: should the listing mark the working-tree version as current regardless of whether a matching cache directory exists (annotate "resolves from working tree", or synthesize the current row), or is the cache-directory-match marker acceptable given the working-tree-pinned contract?

Distinct from the numeric-ordering fix (PR #94): that corrected the sort key; this concerns the `← current` marker semantics.

## 2. `codex plugin marketplace upgrade` does not materialize current versions into the Codex cache (INVESTIGATE)

`just sync-marketplace` fails (`validate_install` exit 1) because the Codex plugin cache holds only stale real version directories while the current working-tree/published versions are absent as real directories.

Observed (PR #165 post-merge, base `a0f4d447`): the Codex marketplace clone at `~/.codex/.tmp/marketplaces/outcomeeng` publishes `python` `0.18.8`, but `~/.codex/plugins/cache/outcomeeng/python/` holds only `0.18.6` (a real dir from the prior day). Same for `develop` (`0.9.6` missing) and `typescript` (`0.19.6` missing). `validate_install` correctly reports `MISSING …/python/0.18.8` etc. Re-running `sync-marketplace` does not change this — preservation reports `0 links, 0 pruned` and the cache stays at `0.18.6`.

This is not a preservation defect: the cache-preservation step (`outcomeeng/distribution/codex_cache.py`, per `21-codex-cache-preservation.adr.md`) only creates or prunes symlinks against the real directory the upgrade leaves; it never materializes a version directory. Materialization is the responsibility of `codex plugin marketplace upgrade` (the Codex CLI), which clones the marketplace and is expected to copy each plugin's current version into `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`. The clone has the current content; the per-plugin cache does not receive it.

The `21-codex-cache-preservation.adr.md` target-identity fix (PR #167) makes this state honest: with no real directory for the current version, preservation prunes all compatibility symlinks rather than fabricating a `current → stale` link, so `validate_install` surfaces `MISSING` instead of a misleading `SYMLINK`. The underlying gap — the upgrade not materializing the current version — predates that fix.

To investigate: why `codex plugin marketplace upgrade` (the installed Codex CLI) leaves the per-plugin cache at a stale real directory after a successful upgrade — whether it is a Codex CLI behavior/limitation, a clone-layout mismatch (the clone exposes `dist/claude/<plugin>` and legacy `plugins/<plugin>`; the cache is keyed by version directory), or a gap in the `outcomeeng.distribution.sync` flow that should copy the clone's current version into the cache when the CLI does not. Governed by this node and `21-codex-cache-preservation.adr.md`.
