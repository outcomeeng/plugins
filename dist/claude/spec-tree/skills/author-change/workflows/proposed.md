<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Proposed`; it loads the common record contract and the Proposed Definition of Ready only. Read `${CLAUDE_SKILL_DIR}/templates/proposed.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve new Change or existing Change through the router. Search the configured store for the same intended Output before creating a new identity: run `gh issue list --repo <store> --state all --search '<the intended Output in words>' --json number,title,url --limit 50` as one single-quoted search argument under `inert-stdin`, and read any title that names the same Output. A result of 50 entries is a blocked search naming `50 issues`; narrow the words and search again.
2. Apply `<intake_and_triage>`. Confirm the Output and the established reason it is worth refining. Ask only about unresolved choices needed to state a proposal the Proposed audit can judge.
3. Set `refined_from: []` for a new Change; only a merge adds entries. Set `parent` to the Parent's canonical identity when the request names one, otherwise `null`; a child carries its Parent's Product. Record every known blocker in `blocked_by`. Use the configured Product, or none for a root whose work spans Products, and `maturity: Proposed`. Set `lifecycle: Available` for a new Change; for an existing Change keep the Lifecycle its store record carries, because only the Lifecycle transitions that the `Lifecycle` selection of `spec-tree:change-standards` states move it.
4. Write `## Intent`. When the request is a raw submission — an unstructured report, idea, request, or conversation excerpt — derive What, Why, Observation, and Evidence from it under `intent`, restating the submission in the proposer's terms and excluding its received text. Keep Observation only where the submission reports an observed state. Record every unclear part that can change the Output as an open question under `## Decisions`, never as an invented answer. Add no section beyond `## Intent` and `## Decisions`, and keep the title, each Intent part, and `## Decisions` within the limits of `record-limits`.
5. Check every Proposed DoR criterion. Return the stabilized local candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- One Proposed record satisfies every Proposed criterion and reaches `<audit_gate>` as the stabilized local candidate.
- The Intent states What, Why, and Evidence, and a raw submission's received text stays out of the record.
- Lineage, `parent`, and blockers are complete in front matter and absent from body restatements.
- Open consequential questions remain explicit under `## Decisions` without invented answers.

</success_criteria>
