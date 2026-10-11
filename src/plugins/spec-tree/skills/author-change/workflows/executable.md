<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Executable`; it loads the common record contract and the cumulative Executable Definition of Ready only. Read `${CLAUDE_SKILL_DIR}/templates/executable.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve the selected Change and apply `<revision_safety>`: a Sliced Leaf to advance, or a current Executable Leaf to revise. A Parent never reaches Executable; stop and name the Parent. For a Sliced Change require its `## Mutations` with the one-repository boundary and resolved dependency sequence, and apply `<authority_gate>` for leaving `Sliced`; the Refiner then advances to `Executable` inside the confirmed slice with no further move. A revision of an Executable Change keeps `maturity: Executable`, applies steps 2 to 4 to the sections the revision names inside the confirmed Frame and slice, and continues at step 5.
2. Settle implementation detail only inside the Nodes, Assertion operations, and Decisions the Maintainer's confirmations covered. A reopened product or architecture judgment stops advancement and returns to the operator through Framed refinement.
3. In `## Nodes`, state for every Node the changeset touches its Malleability before and after, adding each Node the changeset touches only through a dependency, and state each Node's required state. Settle every consequential Decision for the changeset in `## Decisions`.
4. Order the `## Mutations` rows so a fresh Executor can assign and complete each Node's result without the prior conversation or reopened judgment, providers first. In each row name the results the loaded Definition of Ready's `<merge_composition>` selects for its Node, each with its producer, and the decision-record audit for each added or changed decision record the Node owns. Name every `VERIFICATION_READINESS` predicate that composition selects for the changeset, and name no Verifier outside them. Cite the obligation each result satisfies instead of a skill's default gates.
5. Leave `## Artifacts` with no links until a round produces content. Set `maturity: Executable` only when every cumulative Executable DoR criterion holds. Return the stabilized candidate to `<audit_gate>`, then `<persistence>`.

</process>

<artifacts_recording>

After a round returns audited content for a Node, add its link to `## Artifacts` as a revision of the Executable Change under `<revision_safety>`, so a Handoff resumes from the record. A link is a path pinned to the commit that holds the content, resolving in every execution environment. For a decision record the changeset adds that has not merged, post its content as a comment on the Change's issue with `gh issue comment <N> --repo <store> --body-file -`, the body sent as literal stdin under `inert-stdin`, and link that comment.

</artifacts_recording>

<success_criteria>

- The store showed the Product's Maintainer's move out of `Submitted` at `Sliced` before Maturity advanced to `Executable`.
- `## Nodes` states each Node's Malleability before and after and its required state.
- Each `## Mutations` row's results and producers agree with what `<merge_composition>` selects for its Node.
- Every consequential Decision is settled inside the authority of the confirmed Framed and Sliced records.
- Ordered Mutations rows permit execution without reopening product or architecture judgment, and `## Artifacts` links only content a round produced.

</success_criteria>
