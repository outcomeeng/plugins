<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Sliced`; it loads the common record contract and the cumulative Sliced Definition of Ready only. Read `${CLAUDE_SKILL_DIR}/templates/sliced.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve the selected Change and apply `<revision_safety>`. Require its complete Framed sections and apply `<authority_gate>` for leaving `Framed`.
2. Test whether the framed work forms one coherent, independently integrable unit in one repository. When it does not, split it. Read the source's Lifecycle, holder, and newest Handoff, and stop before any claim, naming the source, when another session holds it, it is terminal, or its Handoff names a branch or pull request. Hold the source: when this session does not hold it, use skill `spec-tree:claim-change` and invoke it with the source Change's issue URL; when the claim fails, stop, naming the source. Author each child as a new Change through this skill at `Proposed`, the Maturity every new Change takes, with `parent` naming the source and the source's Product, carrying in its `## Intent` and `## Decisions` the part of the source's Intent, Nodes, Assertion operations, and Decisions that it continues; the child re-frames after its own confirmation. Once every child exists, revise the source in place: remove its `## Nodes` and `## Assertion operations`, keep its Intent and `## Decisions`, and persist it under `<persistence>`. The source is then a Parent and stays open until its children close. Never hide multiple units inside Mutations.
3. To merge two Changes of one Output, hold both as step 2 states, keep the survivor, close the absorbed Change `Abandoned` through `spec-tree:close-change`, and add its canonical identity to the survivor's `refined_from`. To reframe a Change whose Frame no longer holds, edit it in place and lower its Maturity to `Proposed` under `maturity-and-authority`. No route writes `Refined`.
4. Resolve repository boundary, dependencies, blocker lineage, and execution sequence. A blocker cycle prevents Sliced Maturity. Keep active blockers in `blocked_by` while refinement continues.
5. For a Leaf write `## Mutations`: the one repository, the one observable check, and one row per Node with its transition — add, modify, or implement — in execution order, providers first. Name no person; the store's move out of `Submitted` at `Sliced` is the confirmation of the slice. A Parent carries no `## Mutations`; it is Sliced when every child exists naming it in `parent` and its record carries neither `## Nodes` nor `## Assertion operations`.
6. Set `maturity: Sliced` only when the full cumulative Sliced DoR holds. Return the stabilized candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- The store showed the Product's Maintainer's move out of `Submitted` at `Framed` before Maturity advanced to `Sliced`.
- A Leaf's `## Mutations` states one repository, one observable check, and each Node's transition in execution order.
- A split leaves a Parent whose children each name it in `parent`, and the Parent carries no Nodes or Assertion operations.
- Dependencies and sequence are resolved, with no blocker cycle, and no route wrote `Refined`.
- The record carries no accountable-person or attestation line.

</success_criteria>
