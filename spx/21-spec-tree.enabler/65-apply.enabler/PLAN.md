# Plan: drain the preserved aggregate through merge cycles

`/apply` coordinates the dependency-ordered merge cycles that drain `origin/work/strict-finding-disposition`; each affected node owns the concrete branch work and revisit condition in its node-local coordination note.

## Recovery boundary

The recovery source is `origin/work/strict-finding-disposition` at `5f26a67a9aef9327e57fd5e02d130c8363578a07`. Against `origin/main` at `b8503c8147f9291a67d828e649baff0d9c078d9c`, it contains 103 branch commits and changes 189 paths. The aggregate remains recovery material and never enters whole-changeset verification or publication as one pull request.

The changeset-coherence auditor on `origin/work/changeset-coherence-auditor` remains outside this execution plan until the operator starts that work explicitly.

## Merge-cycle index

Run one independently mergeable cycle at a time. Load the target node's coordination note before reconstructing its patch from current `origin/main`.

1. `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/PLAN.md`
2. `spx/13-infrastructure.enabler/25-eval-harness.enabler/PLAN.md`
3. `spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/ISSUES.md`
4. `spx/21-spec-tree.enabler/68-audit.enabler/PLAN.md`
5. `spx/43-typescript.enabler/25-typescript-standards.enabler/29-typescript-code.enabler/PLAN.md`
6. `spx/21-spec-tree.enabler/76-merge.enabler/PLAN.md`

## Apply-local procedure

For every merge cycle:

1. Synchronize with current `origin/main` through `/sync-base`.
2. Load the owning node's current context and coordination notes.
3. Reconstruct one behavioral claim from the preserved source and any repaired extraction branch. Avoid replaying tangled commits wholesale.
4. Treat generated `dist/claude/` and `dist/codex/` files as fan-out from their authored `src/plugins/` producer when evaluating review load.
5. Complete the node plan's deterministic, auditor, review, merge, and cleanup gates.
6. Recompute the preserved aggregate against the new `origin/main`, then advance this index only after the prior node plan's revisit condition is satisfied.

The index is complete when every preserved behavioral claim is merged, explicitly superseded by current product truth, or retained in its owning node's coordination note with a concrete revisit condition.
