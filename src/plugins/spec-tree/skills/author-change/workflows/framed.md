<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Framed`; it loads the common record contract and the cumulative Framed Definition of Ready only. Read `${CLAUDE_SKILL_DIR}/templates/change.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve the selected Change and apply `<revision_safety>`. Preserve immutable `refined_from`; refresh mutable `blocked_by` from necessary relationship reads. Apply `<authority_gate>` for leaving `Proposed`.
2. Apply `<intake_and_triage>` to every Output-affecting uncertainty. Ask only questions repository truth and supplied intent cannot settle.
3. Complete `## Nodes`: every affected or intended Node with its own target malleability, naming the declared value where it differs. Complete `## Assertion operations`: every operation by owning Node or decision record and exact target. Complete `## Decisions`: every question that can change the Output, each with its answer. Never replace per-node targets with one Change-wide target.
4. Present the completed sections to the operator for review. An objection or correction returns to step 2 and leaves `maturity` unchanged until the sections stand. A drafting or execution request alone supplies no authority, and the record carries no attestation line; the Product's Maintainer's move out of `Submitted` at `Framed` is the authority that the record captures the operator's intent. When the sections stand, set `maturity: Framed`.
5. Check every cumulative Framed DoR criterion. Return the stabilized local candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- The store showed the Product's Maintainer's move out of `Submitted` at `Proposed` before Maturity advanced to `Framed`.
- Output-affecting questions are settled in `## Decisions` and the record carries no attestation line.
- Every affected node retains its own target malleability.
- Every criterion of the loaded Framed Definition of Ready holds for `## Nodes`, `## Assertion operations`, and `## Decisions`.

</success_criteria>
