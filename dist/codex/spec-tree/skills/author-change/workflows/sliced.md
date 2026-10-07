<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Sliced`; it loads the common record contract and the cumulative Sliced Definition of Ready only. Read `${SKILL_DIR}/templates/change.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve the selected Change and apply `<revision_safety>`. Require its complete Framed sections and apply `<authority_gate>` for leaving `Framed`.
2. Test whether the framed work forms one coherent, independently integrable unit in one repository. When it does not, refine lineage instead of advancing. First read every source Change's Lifecycle, holder, and newest Handoff, and stop before any claim, naming the source, when one is held by another session, is terminal, or carries a Handoff that names a branch or pull request. Then hold every source: for each source this session does not hold, use skill `spec-tree:claim-change` and invoke it with the source Change's issue URL. When a claim still fails, release each source this route claimed — use skill `spec-tree:release-change` — and stop, naming the source. Then author each successor as a new Change through this skill at `Proposed`, the Maturity every new Change takes, carrying in its `## Intent` and `## Decisions` the part of the source's Intent, Nodes, Assertion operations, and Decisions that it continues, which the successor re-frames after its own confirmation; its `refined_from` names every source Change whose remaining Output it continues — one successor per unit for a split, one successor naming every source for a coalescence. Once every known successor exists, close each held source `Refined`: use skill `spec-tree:close-change` and invoke it with `Refined` and the source Change's issue URL. Never hide multiple units inside Activities.
3. Resolve repository boundary, dependencies, blocker lineage, and execution sequence. A blocker cycle prevents Sliced Maturity. Keep active blockers in `blocked_by` while refinement continues.
4. Write `## Slice`: the one repository, the one vertical slice, and its observable check. Name no person; the store's move out of `Submitted` at `Sliced` is the confirmation of the slice.
5. Set `maturity: Sliced` only when the full cumulative Sliced DoR holds. Return the stabilized candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- The store showed the Product's Maintainer's move out of `Submitted` at `Framed` before Maturity advanced to `Sliced`.
- One repository receives one coherent, independently integrable unit, and `## Slice` states its observable check.
- Dependencies and sequence are resolved, with no blocker cycle.
- The record carries no accountable-person or attestation line.

</success_criteria>
