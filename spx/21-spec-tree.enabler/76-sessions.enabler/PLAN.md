# Plan: Sessions

## Decision placement across the composed children

Three decision records sit at this node while the concerns they govern now live in children:

- `spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md` governs the origin-branch anchor, asserted in `spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler/20-closure.enabler` and constraining the `git_ref` contract in `spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler`.
- `spx/21-spec-tree.enabler/76-sessions.enabler/65-pickup-claim-verification.adr.md` governs the reconciliation mechanism, asserted in `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler/30-claim-verification.enabler`.
- `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md` governs the compaction contract, which remains cross-cutting and is asserted on this node.

A decision constrains its higher-index siblings and their descendants, so all three reach the concerns they govern from where they sit. Whether the first two belong beside those concerns instead is a placement question with a real consequence for context-loading reach: moving `13-handoff-persistence.adr.md` under `25-handoff.enabler` would stop it constraining `15-session-store.enabler`, whose `git_ref` Scenarios depend on it.

**Resolution shape**: run `/decompose spx/21-spec-tree.enabler/76-sessions.enabler` scoped to decision placement, which owns this question when the location depends on concept ownership and context-loading reach. Either relocate a decision beside its concern and prove no consumer loses it, or record here that all three stay at the node and why.

**Revisit condition**: before the next change to any of the three decision records, so the placement is settled while their content is already in context.
