<!-- Prompt template for the merge-readiness eval.
     Generated from {producer_path} section {producer_section_name}.
     The harness substitutes case input JSON before sending the prompt. -->

Use the producer section below as the authority for `/manage-pr` merge-readiness behavior. Classify whether the PR may run a merge command at the mutation point. Ignore host mergeability unless the producer section says it is authoritative.

Producer section:

```text
{producer_section}
```

Case input:

```json
{input_json}
```

Return exactly one JSON object with these fields:

- `merge_readiness`: `"HOLD"` or `"WITHHOLD"`.
- `blocking_predicate`: `"review-absent"`, `"review-nonterminal"`, `"review-skipped-self-modifying-workflow"`, `"review-check-skipped"`, `"review-check-failed"`, `"review-valid-finding"`, `"check-not-terminal-green"`, `"check-failed-or-absent"`, `"branch-hygiene"`, `"head-mismatch"`, or `"none"`.
- `guard_verdict`: `"MERGE_READY:<head-sha>"`, `"WAIT_FOR_REVIEW"`, `"WAIT_FOR_CHECKS"`, `"MENTION_REVIEW_NEEDED:<trigger-phrase>"`, `"FIX_FINDING:<id>"`, or `"MERGE_BLOCKED:<reason>"`.
- `merge_command_allowed`: `true` or `false`.
- `autonomous_action`: `"merge"`, `"post-review-trigger-comment"`, `"fix-finding"`, `"wait"`, or `"block"`.
- `pr_comment_body`: the exact PR-level comment body when `autonomous_action` is `"post-review-trigger-comment"`, otherwise `null`.

Do not include markdown, prose, commentary, caveats, or questions.
