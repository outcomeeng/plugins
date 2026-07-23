# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Spec alignment applied: `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler`,
`spx/13-infrastructure.enabler/32-installation.enabler`, and
`spx/32-distribution.enabler/21-sync.enabler` are aligned — each node's spec declares only the
assertions the decision leaves standing, scoped to what their linked evidence verifies, with the
superseded user-scope assertions removed. The installation and sync nodes' `PLAN.md` files name what
the decision supersedes, what it leaves standing, and the pending implementation cutover; the
agents-conversion node's plan is fully applied and carries none. The
`spx/21-spec-tree.enabler/79-diagnostics.enabler` re-declaration is deferred behind a published
`@outcomeeng/spx` dependency (see that node's `PLAN.md`).

The decision governs user-scope state ownership. Alignment removes the assertions it directly
supersedes and preserves the rest with their evidence — an assertion the decision does not
reach keeps its declaration, whatever else changes around it.

Pending implementation: the tree declares the bounded model but does not yet implement it. The
live `just sync-marketplace` and installation tooling still run the superseded user-scope
model. The production cutover — checkout-bounded sync and install implementation, the isolated
real-runtime harness, and the release-path change in `spx/local/merging.md` — realizes the
"Repository-scoped marketplace synchronization and install verification" scope item. Until
then, that scope bullet is a declared, governing capability, not delivered behavior.
