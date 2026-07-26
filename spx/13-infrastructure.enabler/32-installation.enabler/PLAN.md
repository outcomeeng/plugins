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

## This repository's release process

This product ships plugins for two agents, and a published plugin reaches nobody until each agent's
marketplace is updated to the new version. That update is this repository's `RELEASE` action: after a
plugin change merges to the default branch on origin, both agents' marketplaces advance to the merged
versions so sessions resolve them. The action is declared in `spx/local/merging.md` and runs under
`RELEASE_READINESS` in the phase order the spec-tree plugin ships.

Declaring it is not optional bookkeeping. `spx/21-spec-tree.enabler/76-merging.enabler` builds the
shipped capability of driving a consumer's declared `PREVIEW`, `DEPLOY`, and `RELEASE` phases; this
repository is the consumer that exercises the release path. With no declaration here, the shipped
`RELEASE` phase has no live exerciser and only ever runs as a no-op.

**Sync is not what we are doing.** Reconciling a developer's marketplace registration, repairing a
plugin cache, or fast-forwarding a worktree that serves plugin content are all the superseded
user-scope model that `spx/12-marketplace-state.adr.md` removes from the toolchain's reach. The
release action updates each agent's marketplace to the published versions and nothing else.

Steps:

- Declare `RELEASE` in `spx/local/merging.md` with the update command for each agent, and state the
  `RELEASE_READINESS` predicates that authorize it. Keep the overlay to those values; the phase
  order, the gate, and the worktree and cleanup protocols are the shipped skills'.
- Widen this node beyond Codex. `installation.md` declares the Codex installed-set payload contract,
  the addable-set derivation, and the per-plugin refresh form; the release updates both agents, so
  the Claude side needs the same declared read and update contracts before the action is verifiable.
- Establish evidence for the release action through `/verify`, which selects the verification type,
  then `/test` for whatever it routes to test. Do not presuppose the type, the assertion type, or the
  execution level here: the assertion's quantifier selects the assertion type, and operational
  reality selects the level. This node already reads a real agent CLI at `L1`
  (`test_installed_set.conformance.l1.py`), so invoking a CLI is not what makes evidence heavier —
  full install cost across the catalog is. Whatever setup the routing needs, including a disposable
  agent home, belongs to a spec-governed harness; the executed test owns the assertion flow alone.
- Correct the root guides to name the release command as the way published versions reach an agent,
  and drop any text telling a developer to run the underlying primitives by hand.

Out of scope here: `spx/21-spec-tree.enabler/76-merging.enabler/PLAN.md` describes the shipped
lifecycle and stays free of this repository's specifics. Restore it complete and pure; the
declaration above is what makes its release path exercised, not part of its content.

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
