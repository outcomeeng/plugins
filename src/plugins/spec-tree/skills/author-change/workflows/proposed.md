<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Proposed`; it loads the common record contract and the Proposed Definition of Ready only. Read `${CLAUDE_SKILL_DIR}/templates/change.md` and the router's store configuration.

</required_reading>

<process>

1. Resolve new root, new successor, or existing Change through the router. Search the configured store for the same intended Output before creating a new identity.
2. Apply `<intake_and_triage>`. Confirm the Output and established priority basis. Ask only about unresolved choices needed to state a reviewable proposal.
3. For a root set `refined_from: []`; for a successor record the complete immutable predecessor set. Record every known blocker in `blocked_by`. Use the configured Product and truthful Lifecycle.
4. Fill all four top-level sections. Keep consequential unresolved questions explicit in `# Frame`. Exclude received conversation input, transcripts, and prompt copies.
5. Present the proposal for operator review. After explicit review, add `Proposal review: reviewed by the operator on <date>.` inside `# Frame` and record `maturity: Proposed`; never infer review from a drafting request or silence.
6. Check every Proposed DoR criterion. Return the stabilized local candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- One reviewed Proposed record carries its in-Frame review statement and satisfies every Proposed criterion.
- Root or successor lineage and blockers are complete in front matter and absent from body restatements.
- Open consequential questions remain explicit without invented answers.

</success_criteria>
