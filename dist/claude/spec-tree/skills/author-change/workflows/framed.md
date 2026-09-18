<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Framed`; it loads the common record contract and the cumulative Framed Definition of Ready only. Read `${CLAUDE_SKILL_DIR}/templates/change.md` and the router's store configuration.

</required_reading>

<process>

1. Resolve the selected Change and apply `<revision_safety>`. Preserve immutable `refined_from`; refresh mutable `blocked_by` from necessary relationship reads.
2. Apply `<intake_and_triage>` to every Output-affecting uncertainty. Ask only questions repository truth and supplied intent cannot settle.
3. Complete `# Frame`: every affected or intended Node with its own target malleability, every Assertion operation, and every governing or intended Decision with its settled choice. Never replace per-node targets with one Change-wide target.
4. Present the complete Frame to the operator. After explicit approval, add `Intent attestation: attested by the operator on <date>.` inside `# Frame` and set `maturity: Framed`. A drafting or execution request alone supplies no attestation.
5. Check every cumulative Framed DoR criterion. Return the stabilized local candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- Output-affecting questions are settled and the complete Frame carries explicit operator attestation.
- Every affected node retains its own target malleability.
- Nodes, Assertion operations, and Decisions are complete enough to preserve product intent.

</success_criteria>
