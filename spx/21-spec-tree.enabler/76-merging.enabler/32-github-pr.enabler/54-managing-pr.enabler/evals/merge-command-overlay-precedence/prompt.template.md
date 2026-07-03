<!-- Prompt template for the merge-command-overlay-precedence eval.
     Generated from {producer_path} section {producer_section_name}.
     The harness substitutes case input JSON before sending the prompt. -->

Use the producer section below as the authority for `/manage-pr` merge-command selection after `MERGE_READINESS` holds. The case input gives the overlay merge-command declaration available to the producer.

Producer section:

```text
{producer_section}
```

Case input:

```json
{input_json}
```

Return exactly one JSON object with these fields:

- `merge_flag`: `"--rebase"`, `"--merge"`, or `"--squash"` — the flag passed to `gh pr merge`.
- `source`: `"overlay"` when the choice follows an overlay declaration, or `"universal-default"` when the overlay is silent.
- `delete_branch_flag`: `"--delete-branch=false"` when the universal default is selected, or `null` when the overlay declaration controls cleanup.
- `cleanup_sequence`: `"worktree-safe-manual-branch-deletion"` when the universal default is selected, or `"overlay-declared"` when the overlay declaration controls cleanup.

Do not include markdown, prose, commentary, caveats, or questions.
