<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Executable`; it loads the common record contract and the cumulative Executable Definition of Ready only. Read `${CLAUDE_SKILL_DIR}/templates/change.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve the selected Change and apply `<revision_safety>`: a Sliced Change to advance, or a current Executable Change to revise. For a Sliced Change require its `## Slice` with the one-repository boundary and resolved dependency sequence, and apply `<authority_gate>` for leaving `Sliced`; the Refiner then advances to `Executable` inside the confirmed slice with no further move. A revision of an Executable Change keeps `maturity: Executable`, applies steps 2 to 4 to the sections the revision names inside the confirmed Frame and slice, and continues at step 5.
2. Settle implementation detail only inside the Nodes, Assertion operations, and Decisions the Maintainer's confirmations covered. A reopened product or architecture judgment stops advancement and returns to the operator through Framed refinement.
3. In `## Nodes`, state for every Node the changeset touches its target malleability, adding each Node the changeset touches only through a dependency, carrying the declared malleability beside it where the two differ, and state each Node's required state. Settle every consequential Decision for the changeset in `## Decisions`.
4. Order `## Activities` so a fresh Executor can assign and complete each result without the prior conversation or reopened judgment. Include authoring before dependent verification or implementation and the required merge composition after the Change. Name in the Activities every `VERIFICATION_READINESS` predicate the loaded Definition of Ready's `<merge_composition>` selects for the changeset, each result with its producer, and the decision-record audit for each added or changed decision record, and name no Verifier outside them. Write each verification Activity to cite the obligation it satisfies instead of a skill's default gates.
5. Set `maturity: Executable` only when every cumulative Executable DoR criterion holds. Return the stabilized candidate to `<audit_gate>`, then `<persistence>`.

</process>

<success_criteria>

- The store showed the Product's Maintainer's move out of `Submitted` at `Sliced` before Maturity advanced to `Executable`.
- `## Nodes` states per-node target malleability and required state.
- The Activities' evidence obligations agree with what `<merge_composition>` selects for the changeset, and each verification Activity cites them.
- Every consequential Decision is settled inside the authority of the confirmed Framed and Sliced records.
- Ordered Activities permit execution without reopening product or architecture judgment.

</success_criteria>
