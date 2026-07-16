# Plan

Governing decision: `spx/15-marketplace-state.adr.md` (marketplace state ownership).

Pending scope realization: the "What's included" scope item "Repository-scoped marketplace
synchronization and install verification" names the checkout-bounded model the ADR declares.
The tree does not yet implement it — `spx/13-infrastructure.enabler/32-installation.enabler`
and `spx/32-distribution.enabler/21-sync.enabler` still declare and implement the superseded
user-scope model, `spx/21-spec-tree.enabler/79-diagnostics.enabler` still ships the embedded
expected-plugin catalog, and `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler`
still names a user-scope agent-install destination. Each affected node's `PLAN.md` tracks its
own pending re-declaration; the production cutover of `just sync-marketplace` (with the
release-path change in `spx/local/merging.md`) realizes the scope item. Until then, the scope
bullet is a declared, governing capability — not delivered behavior.
