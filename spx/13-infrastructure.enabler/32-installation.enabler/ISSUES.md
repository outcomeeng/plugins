# Issues: Installation Enabler

## 1. Cache listing shows no `← current` for a working-tree-pinned plugin ahead of its cache (FOLLOW-UP)

`print_cache` / `cached_entries` (`outcomeeng/validation/install.py`) mark `← current` on the cache directory whose name equals the working-tree manifest version. For the Claude Code cache, resolution is working-tree-pinned (see `21-codex-cache-preservation.adr.md`), so the cache directories are an informational record, not the resolution source. When the working tree advances past every cached version directory (the cache updates lazily), no directory name matches the working-tree version, so the plugin shows no `← current` marker at all — making an up-to-date, correctly-resolving install look stale.

Observed: spec-tree resolved to the working-tree version while its cache directories topped out two patch versions behind, so the listing showed every other plugin's `← current` but none for spec-tree.

This is a display-semantics question, not a resolution defect — resolution is correct. The decision for whoever next touches the listing: should the listing mark the working-tree version as current regardless of whether a matching cache directory exists (annotate "resolves from working tree", or synthesize the current row), or is the cache-directory-match marker acceptable given the working-tree-pinned contract?

Distinct from the numeric-ordering fix (PR #94): that corrected the sort key; this concerns the `← current` marker semantics.
