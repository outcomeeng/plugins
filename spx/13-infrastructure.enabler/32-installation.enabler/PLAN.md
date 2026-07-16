# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

The decision bounds the marketplace toolchain to the invocation checkout: it reconciles only
that checkout's committed runtime configuration and never mutates a developer's user-scope
marketplace registrations, plugin caches, or agent directories. Install completeness is
established by an isolated harness that provisions real runtimes in disposable homes.

Spec alignment applied: `installation.md` now declares only the checkout-bounded installed-set
read contract the decision leaves standing. The superseded user-scope assertions are removed —
Codex plugin-cache preservation (compatibility symlinks, version-directory topology, orphan and
unmanaged-plugin pruning, reconciliation-timestamp freshness), user-scope marketplace-source
reconciliation, registration repair, and plugin-selection restore, and the `validate_install`
assertions verifying user-scope cache topology and cache listing. The preserved assertion — the
Codex installed-set CLI payload contract — survives because the decision changes where install
state lives, not how a payload parses; the isolated harness still reads a runtime's installed
plugins through `codex plugin list --json`, and a changed CLI contract must raise rather than
yield a silent empty set.

Pending implementation:

- Build the isolated real-runtime installation harness — real `claude` and `codex` binaries in
  disposable runtime homes — that verifies every catalog plugin installs and enables while
  mutating no user-scope state. The harness assertion belongs in a node of its own: `spx/EXCLUDE`
  is node-granular, so excluding this node to admit a not-yet-implemented harness assertion would
  also stop its passing test file. Declare the harness node with `/author`, then route its
  assertions through `/test`.
- Remove the superseded user-scope installation implementation and its now-unlinked test files
  (`test_codex_plugin_cache.*`, `test_marketplace_sources.*`, `test_validate_install.scenario.l1.py`)
  in the production cutover of `just sync-marketplace`.
