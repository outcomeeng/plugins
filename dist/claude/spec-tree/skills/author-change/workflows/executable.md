<required_reading>

Use skill `spec-tree:change-standards`. Invoke it with `Executable`; it loads the common record contract and the cumulative Executable Definition of Ready only. Read `${CLAUDE_SKILL_DIR}/templates/executable.md` and `spx/local/coordination.md` when present.

</required_reading>

<process>

1. Resolve the selected Change and apply `<revision_safety>`: a Sliced Leaf to advance, or a current Executable Leaf to revise. A Parent never reaches Executable; stop and name the Parent. For a Sliced Change require its `## Slice` with the one-repository boundary and resolved dependency sequence, and apply `<authority_gate>` for leaving `Sliced`; the Refiner then advances to `Executable` inside the confirmed slice with no further move. A revision of an Executable Change keeps `maturity: Executable`, applies steps 2 to 4 to the sections the revision names inside the confirmed Frame and slice, and continues at step 5.
2. Settle implementation detail only inside the governing records, mutations blocks, and settled decisions the Maintainer's confirmations covered. A reopened product or architecture judgment stops advancement and returns to the operator through Framed refinement.
3. In the `## Governance mutations` and `## Spec mutations` blocks, state every consequential decision for the changeset, adding each Node the changeset touches only through a dependency with its malleability before and after.
4. Order the blocks so a fresh Executor can complete each without the prior conversation or reopened judgment, providers first. Write no result, producer, or Verifier into the record: execution derives them from the merge composition the loaded Definition of Ready carries.
5. Leave `## Artifacts` with no links until a round produces content. Set `maturity: Executable` only when every cumulative Executable DoR criterion holds. Return the stabilized candidate to `<audit_gate>`, then `<persistence>`.

</process>

<artifacts_recording>

After a round returns audited content for a record or Node, add its link to `## Artifacts` as a revision of the Executable Change under `<revision_safety>`, so a Handoff resumes from the record. A link is a path pinned to the commit that holds the content, resolving in every execution environment. For a decision record the changeset adds that has not merged, post its content as a comment on the Change's issue with `gh issue comment <N> --repo <store> --body-file <file>`, the body written to a payload file under `inert-stdin`, and link that comment.

</artifacts_recording>

<success_criteria>

- The store showed the Product's Maintainer's move out of `Submitted` at `Sliced` before Maturity advanced to `Executable`.
- The mutations blocks state every consequential decision for the changeset inside the authority of the confirmed Framed and Sliced records.
- The record names no result, producer, or Verifier.
- Ordered blocks permit execution without reopening product or architecture judgment, and `## Artifacts` links only content a round produced.

</success_criteria>
