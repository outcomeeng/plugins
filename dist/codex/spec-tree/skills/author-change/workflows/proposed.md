<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Proposed`; it loads the common record contract and the Proposed Definition of Ready only. Read `${SKILL_DIR}/templates/proposed.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve new Change or existing Change through the router. Search the configured store for the same intended Output before creating a new identity: run `gh issue list --repo <store> --state all --search '<the intended Output in words>' --json number,title,url --limit 50` as one single-quoted search argument under `inert-stdin`, and read any title that names the same Output. A result of 50 entries is a blocked search naming `50 issues`; narrow the words and search again.
2. Apply `<intake_and_triage>`. Confirm the Output and the established reason it is worth refining. Ask only about unresolved choices needed to state a proposal the Proposed audit can judge.
3. Set `predecessors: []` for a new Change; only a merge adds entries. Set `parent` to the Parent's canonical identity when the request names one, otherwise `null`; a child carries the Product that owns its Output. Record every known blocker in `blocked_by`. Use the configured Product, or none for a root whose work spans Products, and `maturity: Proposed`. Set `lifecycle: Available` for a new Change; for an existing Change keep the Lifecycle its store record carries, because only the Lifecycle transitions that the `Lifecycle` selection of `spec-tree:change-standards` states move it.
4. Write `## Intent` within the limit of `record-limits`; a count over a limit is a non-blocking finding, and the word counts need no repair round. When the request is a raw submission — an unstructured report, idea, request, or conversation excerpt — derive What, Why, Observation, and Evidence from it under `intent`, restating the submission in the proposer's terms and excluding its received text. Keep Observation only where the submission reports an observed state.
5. Complete `## Governance`: every record the Output touches or that governs it, by its path from `spx/`, each with the verdict `in line`, `amended`, or `new`. Complete `## Governance mutations`: one block for each amended or new record, opening with `<path> states:` and listing the exact text of every decision the Output adds or amends, each opening with a slug and a colon. Complete `## Spec mutations`: one block for each affected or intended Node in execution order, opening with `<path>: <malleability before> -> <malleability after>`; Proposed names the Node by that opening line alone, and Framed adds its assertions. A Parent carries neither mutations section.
6. Record every unclear part that can change the Output under `## Open questions`, never as an invented answer, and end the record there. Add no section beyond `## Intent`, `## Governance`, `## Governance mutations`, `## Spec mutations`, and `## Open questions`.
7. Check every Proposed DoR criterion. Return the stabilized local candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- One Proposed record satisfies every Proposed criterion and reaches `<audit_gate>` as the stabilized local candidate.
- The Intent states What, Why, and Evidence within the `record-limits` limit, and a raw submission's received text stays out of the record.
- `## Governance` lists every record the Output touches or that governs it, `## Spec mutations` names every Node the Output touches, and `## Governance mutations` holds the exact text of every decision the Output adds or amends.
- Lineage, `parent`, and blockers are complete in front matter and absent from body restatements.
- Open consequential questions remain explicit under `## Open questions` without invented answers.

</success_criteria>
