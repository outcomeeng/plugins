<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Framed`; it loads the common record contract and the cumulative Framed Definition of Ready only. Read `${SKILL_DIR}/templates/framed.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve the selected Change and apply `<revision_safety>`. Preserve append-only `predecessors` and `parent`; refresh mutable `blocked_by` from necessary relationship reads. Apply `<authority_gate>` for leaving `Proposed`.
2. Apply `<intake_and_triage>` to every Output-affecting uncertainty. Ask only questions repository truth and supplied intent cannot settle.
3. Complete `## Governance`: every record that governs the Change by its path from `spx/`, each with the verdict `in line`, `amended`, or `new`. Complete `## Governance mutations`: one block for each amended or new record, opening with `<path> states:` and listing its decisions in exact text, each opening with a slug and a colon. Complete `## Spec mutations`: one block for each affected or intended Node in execution order, opening with `<path>: <malleability before> -> <malleability after>` and continuing with `<file> states:` and the Node's assertions as bare bullets. Never replace per-Node values with one Change-wide target. A Parent carries neither mutations section.
4. Settle every question that can change the Output with a justified assumption: the block that states its answer carries the answer, and `## Assumptions`, between `## Spec mutations` and `## Slice`, holds each settled question as its answer and one sentence of reason, under `assumptions`. Omit `## Assumptions` when the Frame settled no question. A question no assumption can defend goes, with your best answer, to the superior that assigned the refinement; frame every part that does not depend on the answer, and leave the record at `Proposed` with the question under `## Open questions` until the answer arrives. Remove `## Open questions` from a record that frames.
5. Present the completed sections to the operator for review. An objection or correction returns to step 2 and leaves `maturity` unchanged until the sections stand. A drafting or execution request alone supplies no authority, and the record carries no attestation line; the Product's Maintainer's move out of `Submitted` at `Framed` is the authority that the record captures the operator's intent. When the sections stand, set `maturity: Framed`.
6. Check every cumulative Framed DoR criterion. Return the stabilized local candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- The store showed the Product's Maintainer's move out of `Submitted` at `Proposed` before Maturity advanced to `Framed`.
- Output-affecting questions are settled in the mutations blocks and `## Assumptions`, `## Open questions` is absent, a question no assumption can defend reached the superior with its best answer, and the record carries no attestation line.
- Every affected Node retains its own malleability before and after.
- Every criterion of the loaded Framed Definition of Ready holds for `## Governance`, `## Governance mutations`, and `## Spec mutations`.

</success_criteria>
