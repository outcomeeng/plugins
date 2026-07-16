# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Spec alignment done: the directly affected node specs declare the checkout-bounded model at
design level — `spx/13-infrastructure.enabler/32-installation.enabler`,
`spx/32-distribution.enabler/21-sync.enabler`, and
`spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler`. The
`spx/21-spec-tree.enabler/79-diagnostics.enabler` spec re-declaration is deferred behind a
published `@outcomeeng/spx` dependency (see that node's PLAN.md).

Pending implementation: the tree declares the bounded model but does not yet implement it. The
live `just sync-marketplace` and installation tooling still run the superseded user-scope
model. The production cutover — checkout-bounded sync/install implementation, the isolated
real-runtime harness, the release-path change in `spx/local/merging.md`, and concrete
`[test]`-lane assertions with tests — realizes the "Repository-scoped marketplace
synchronization and install verification" scope item. Until then, the scope bullet is a
declared, governing capability, not delivered behavior. Each affected node's `PLAN.md` tracks
its own pending implementation.
