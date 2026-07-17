# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

The decision bounds the marketplace toolchain to the invocation checkout: it reconciles only
that checkout's committed runtime configuration and never mutates a developer's user-scope
marketplace registrations, plugin caches, or agent directories. Install completeness is
established by an isolated harness that provisions real runtimes in disposable homes.

Spec alignment applied: `installation.md` now declares the checkout-bounded read and refresh
mechanics the decision leaves standing — the Codex installed-set CLI payload contract, the
addable-plugin-set derivation from `dist/codex/*/.codex-plugin/plugin.json`, and the per-plugin
`codex plugin add` refresh command form (never `codex plugin marketplace upgrade`). The superseded
user-scope assertions are removed — Codex plugin-cache preservation (compatibility symlinks,
version-directory topology, orphan and unmanaged-plugin pruning, reconciliation-timestamp
freshness), user-scope marketplace-source reconciliation, registration repair, and
plugin-selection restore, and the `validate_install` assertions verifying user-scope cache
topology and cache listing. The preserved assertions survive because the decision changes where
install state lives and forbids user-scope mutation, not how a payload parses, where the addable
set is derived, or which refresh command installs a plugin; the isolated harness performs these
same reads and installs in disposable runtime homes.

Pending implementation:

- Build the isolated real-runtime installation harness — real `claude` and `codex` binaries in
  disposable runtime homes — that verifies every catalog plugin installs and enables while
  mutating no user-scope state. The harness assertion belongs in a node of its own: `spx/EXCLUDE`
  is node-granular, so excluding this node to admit a not-yet-implemented harness assertion would
  also stop its passing test files. Declare the harness node with `/author`, then route its
  assertions through `/test`. When that node exists, the addable-set and refresh-command-form
  assertions re-home to it alongside the harness.
- Remove the superseded user-scope installation implementation and its now-unlinked test files
  (`test_codex_plugin_cache.scenario.l1.py`, `test_codex_plugin_cache.property.l1.py`,
  `test_marketplace_sources.*`, `test_validate_install.scenario.l1.py`) in the production cutover
  of `just sync-marketplace`. `test_codex_plugin_cache.compliance.l1.py` stays linked — it backs
  the preserved addable-set and refresh-command-form assertions.
