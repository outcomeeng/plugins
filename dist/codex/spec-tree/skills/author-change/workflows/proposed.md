<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Proposed`; it loads the common record contract and the Proposed Definition of Ready only. Read `${SKILL_DIR}/templates/change.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve new root, new successor, or existing Change through the router. Search the configured store for the same intended Output before creating a new identity.
2. Apply `<intake_and_triage>`. Confirm the Output and the established reason it is worth refining. Ask only about unresolved choices needed to state a proposal the Proposed audit can judge.
3. For a root set `refined_from: []`; for a successor record the complete immutable predecessor set. Record every known blocker in `blocked_by`. Use the configured Product and `maturity: Proposed`. Set `lifecycle: Available` for a new root or successor; for an existing Change keep the Lifecycle its store record carries, because only the Lifecycle transitions that the `Lifecycle` selection of `spec-tree:change-standards` states move it.
4. Write `## Intent`. When the request is a raw submission — an unstructured report, idea, request, or conversation excerpt — derive What, Why, Observation, and Evidence from it under `intent`, restating the submission in the proposer's terms and excluding its received text. Keep Observation only where the submission reports an observed state. Record every unclear part that can change the Output as an open question under `## Decisions`, never as an invented answer. Add no section beyond `## Intent` and `## Decisions`.
5. Check every Proposed DoR criterion. Return the stabilized local candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- One Proposed record satisfies every Proposed criterion and reaches `<audit_gate>` as the stabilized local candidate.
- The Intent states What, Why, and Evidence, and a raw submission's received text stays out of the record.
- Root or successor lineage and blockers are complete in front matter and absent from body restatements.
- Open consequential questions remain explicit under `## Decisions` without invented answers.

</success_criteria>
