# Plan: Sessions

## Decision placement across the composed children

Two decision records sit at this node and one sits inside `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler`. A decision constrains its higher-index siblings and their descendants, so each reaches the concerns it governs only from a slot below them.

- `spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md` at index 13 constrains `15-session-store.enabler`, `25-handoff.enabler`, and `28-pickup.enabler`. It governs the origin-branch anchor asserted in `25-handoff.enabler/20-closure.enabler` and the `git_ref` contract in `15-session-store.enabler`, and reaches both.
- `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md` at index 21 constrains `25-handoff.enabler` and `28-pickup.enabler`. It does not reach `15-session-store.enabler` at index 15, which is correct: the store is a command contract that compaction does not govern.
- `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler/20-claim-verification.adr.md` sits inside the pickup node at index 20, below `30-claim-verification.enabler` and `60-resumption.enabler`, so it constrains both. From its former slot at index 65 under this node it constrained neither, because a decision reaches only siblings above it.

**Open question**: whether `13-handoff-persistence.adr.md` should move under `25-handoff.enabler` beside the closure assertions that cite it. It cannot, without losing `15-session-store.enabler`, whose `git_ref` Scenarios depend on it and which is not a descendant of `25-handoff.enabler`. Either the ADR stays where it reaches both, or the `git_ref` contract and the anchor rule are recognized as one concern and composed together.

**Revisit condition**: before the next change to `13-handoff-persistence.adr.md`, so the placement is settled while its content is already in context.
