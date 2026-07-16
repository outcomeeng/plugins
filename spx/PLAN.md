# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Spec alignment: `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler` is
aligned — Codex custom-agent installation is scoped to the checkout's `.codex/agents/`, and the
rule keeps its linked evidence. Alignment remains for
`spx/13-infrastructure.enabler/32-installation.enabler` and
`spx/32-distribution.enabler/21-sync.enabler`; both carry their full assertion sets, and each
node's `PLAN.md` names what the decision supersedes and what it leaves standing. The
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
