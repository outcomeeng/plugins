<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Proposed`; it loads the common record contract and the Proposed Definition of Ready only. Read `${SKILL_DIR}/templates/change.md` and the router's store configuration.

</required_reading>

<process>

1. Resolve new root, new successor, or existing Change through the router. Search the configured store for the same intended Output before creating a new identity.
2. Apply `<intake_and_triage>`. Confirm the Output and established priority basis. Ask only about unresolved choices needed to state a proposal the Proposed audit can judge.
3. For a root set `refined_from: []`; for a successor record the complete immutable predecessor set. Record every known blocker in `blocked_by`. Use the configured Product and `maturity: Proposed`. Set `lifecycle: Available` for a new root or successor; for an existing Change keep the Lifecycle its store record carries, because only `claim-change`, `release-change`, and `close-change` move it.
4. Fill all four top-level sections. Keep consequential unresolved questions explicit in `# Frame`. Exclude received conversation input, transcripts, and prompt copies.
5. Check every Proposed DoR criterion. Return the stabilized local candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- One Proposed record satisfies every Proposed criterion and reaches `<audit_gate>` as the stabilized local candidate.
- Root or successor lineage and blockers are complete in front matter and absent from body restatements.
- Open consequential questions remain explicit without invented answers.

</success_criteria>
