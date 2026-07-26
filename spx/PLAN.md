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

Release-path alignment applied: `spx/local/merging.md` declares no release action, and both root
guides state that a merge to the default branch on origin is the publication. Both agents resolve
from the `outcomeeng/plugins` marketplace this checkout declares, so no worktree serves plugin
content.

Pending implementation: the live `just sync-marketplace`, `just push-marketplace`, and
`just marketplace-source-root` recipes and the distribution modules behind them still carry the
superseded user-scope model and have no remaining subject. Their retirement, and the re-scoping of
`spx/32-distribution.enabler/21-sync.enabler` that follows, is tracked in that node's `PLAN.md`,
together with the disposable-home install-completeness harness that
`spx/12-marketplace-state.adr.md` asserts and no test on the default branch establishes. Until that
lands, the "Repository-scoped marketplace synchronization and install verification" scope bullet is a
declared, governing capability, not delivered behavior.
