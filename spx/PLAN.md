# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Spec alignment applied: `spx/18-plugin-build.enabler/54-conversion.enabler/21-agents.enabler`,
`spx/13-infrastructure.enabler/32-installation.enabler`, and
`spx/32-distribution.enabler/21-sync.enabler` are aligned — each node's spec declares only the
assertions the decision leaves standing, scoped to what their linked evidence verifies, with the
superseded user-scope assertions removed. Each node's `PLAN.md` names what the decision supersedes,
what it leaves standing, and the pending implementation cutover. The
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

## Configured-agent identity protocol

**Active scope.** [Agentic execution](43-agentic-execution.enabler/agentic-execution.md)
owns portable configured-agent task intent and execution policy. [Coding agents](68-coding-agents.enabler/coding-agents.md)
owns Claude Code and Codex grammar, rendering, invocation, and protocol. This slice aligns
[plugin build](18-plugin-build.enabler/plugin-build.md), adds the Codex identity-first role
protocol to the generated instruction surface, and preserves Claude Code's native configured-agent
invocation.

**Temporary dependency.** The instruction template remains under the Spec Tree plugin build
surface while `spx/68-coding-agents.enabler` declares the product boundary it implements. Direct
spec ownership moves only with a separately reviewed tree refactor.

**Parked scope.** Child decomposition for the two agent-harness surfaces, broader custom-agent
conversion migration, and installation remain separate changes. This slice prepends the Codex identity
preflight during conversion and adds mapping evidence for that behavior; it changes no eval evidence.

**Verification route.** Format and validate the changed specs, audit each changed node and the
instruction template, run focused and selected deterministic checks, review the exact committed
changeset, then run the full deterministic gate before `/merge`.
