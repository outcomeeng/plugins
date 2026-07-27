# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Spec alignment applies through `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler`,
`spx/13-infrastructure.enabler/32-installation.enabler`, and
`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler`. The
repository-installation node declares the checkout-bounded command and isolated real-agent harness,
while `spx/32-distribution.enabler/21-installation.enabler/PLAN.md` reserves explicit consumer
installation as the dependent next slice. The
`spx/21-spec-tree.enabler/79-diagnostics.enabler` re-declaration is deferred behind a published
`@outcomeeng/spx` dependency (see that node's `PLAN.md`).

The decision governs user-scope state ownership. Alignment removes the assertions it directly
supersedes and preserves the rest with their evidence — an assertion the decision does not
reach keeps its declaration, whatever else changes around it.

Pending implementation: the tree declares the bounded model through
`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler`. The live
`just sync-marketplace` and installation tooling still run the superseded user-scope model. The
production cutover — `just install-marketplace`, the isolated real-agent harness, and the
release-path change in `spx/local/merging.md` — realizes the
"Repository-scoped marketplace synchronization and install verification" scope item. Until
then, that scope bullet is a declared, governing capability, not delivered behavior.
