<!-- Prompt template for the merge-readiness eval.
     Generated from dist/claude/spec-tree/skills/manage-pr/SKILL.md section merge_readiness_decision_table.
     The harness substitutes case input JSON before sending the prompt. -->

Use the producer section below as the authority for `/manage-pr` merge-readiness behavior. Classify whether the PR may run a merge command at the mutation point. Ignore host mergeability unless the producer section says it is authoritative.

Producer section:

```text
<step name="merge_readiness_decision_table">

Classify `MERGE_READINESS` in this order:

1. Missing or non-terminal review-kind check -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-nonterminal"`, `guard_verdict: "WAIT_FOR_REVIEW"`, `merge_command_allowed: false`, `autonomous_action: "wait"`, `pr_comment_body: null`.
2. Current-head CI review exists with a valid `BLOCKING` or in-scope `DEBT` finding -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-valid-finding"`, `guard_verdict: "FIX_FINDING:<id>"`, `merge_command_allowed: false`, `autonomous_action: "fix-finding"`, `pr_comment_body: null`.
3. Review-kind check skipped because the PR modifies the reviewer's own workflow file and current-head CI review is absent -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-skipped-self-modifying-workflow"`, `guard_verdict: "MENTION_REVIEW_NEEDED:<trigger-phrase>"`, `merge_command_allowed: false`, `autonomous_action: "post-review-trigger-comment"`, `pr_comment_body: "<trigger-phrase> review"`.
4. Review-kind check skipped for any other reason -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-check-skipped"`, `guard_verdict: "MERGE_BLOCKED:review-check-skipped"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
5. Review-kind check failed, cancelled, timed out, requires action, or is neutral -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-check-failed"`, `guard_verdict: "MERGE_BLOCKED:review-check-failed"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
6. Current-head CI review absent after the review-kind check guard -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-absent"`, `guard_verdict: "WAIT_FOR_REVIEW"`, `merge_command_allowed: false`, `autonomous_action: "wait"`, `pr_comment_body: null`.
7. Non-review required check non-terminal -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "check-not-terminal-green"`, `guard_verdict: "WAIT_FOR_CHECKS"`, `merge_command_allowed: false`, `autonomous_action: "wait"`, `pr_comment_body: null`.
8. Non-review required check terminal-but-not-success or absent -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "check-failed-or-absent"`, `guard_verdict: "MERGE_BLOCKED:<reason>"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
9. Branch hygiene or PR-state predicate failed -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "branch-hygiene"`, `guard_verdict: "MERGE_BLOCKED:<reason>"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
10. Head SHA, fetched branch head, or status-check head mismatch -> `merge_readiness: "WITHHOLD"`, `blocking_predicate: "head-mismatch"`, `guard_verdict: "MERGE_BLOCKED:<reason>"`, `merge_command_allowed: false`, `autonomous_action: "block"`, `pr_comment_body: null`.
11. Otherwise -> `merge_readiness: "HOLD"`, `blocking_predicate: "none"`, `guard_verdict: "MERGE_READY:<head-sha>"`, `merge_command_allowed: true`, `autonomous_action: "merge"`, `pr_comment_body: null`.

Ignore host mergeability. `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, and a successful `gh pr merge` response never authorize the merge command.

</step>
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
