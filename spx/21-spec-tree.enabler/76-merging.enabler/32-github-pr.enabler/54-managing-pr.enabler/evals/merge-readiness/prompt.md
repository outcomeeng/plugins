<!-- Prompt template for the merge-readiness eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model. -->

Closed classification task. Do not invoke skills, do not inspect a repository, do not wait for more instructions, and do not run tools. Read the JSON state below and return the verdict JSON object only.

Classify whether the PR may run a merge command at the mutation point.

`ci_review.findings` is the union of findings from every current-head review surface and reviewer already inspected by the managing flow. Optional metadata such as `ci_review.no_findings_reviewers` records reviewers that reported no findings on the same head; it never cancels a finding present in `ci_review.findings`.

Rules, in order:

1. If `reviewing_kind_check.state_category` is `"non_terminal"` or `"missing"`, return:
   `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-nonterminal"`, `guard_verdict: "WAIT_FOR_REVIEW"`, `merge_command_allowed: false`.
   If `reviewing_kind_check` is omitted, continue to the `ci_review.present` rule.
2. Else if `reviewing_kind_check.state_category` is `"skipped_self_modifying_workflow"` and `ci_review.present` is `false`, return:
   `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-skipped-self-modifying-workflow"`, `guard_verdict: "MENTION_REVIEW_NEEDED:<trigger_phrase>"`, `merge_command_allowed: false`.
   If `ci_review.present` is `true`, continue to the review finding rules; the mention-triggered current-head review is already available for evaluation.
3. Else if `reviewing_kind_check.state_category` is `"skipped_non_exception"`, return:
   `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-check-skipped"`, `guard_verdict: "MERGE_BLOCKED:review-check-skipped"`, `merge_command_allowed: false`.
4. Else if `reviewing_kind_check.state_category` is `"terminal_failure"`, return:
   `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-check-failed"`, `guard_verdict: "MERGE_BLOCKED:review-check-failed"`, `merge_command_allowed: false`.
5. Else if `ci_review.present` is `false`, return:
   `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-absent"`, `guard_verdict: "WAIT_FOR_REVIEW"`, `merge_command_allowed: false`.
6. Else if any review finding has `validity: "valid"` and `severity: "blocking"`, return:
   `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-valid-finding"`, `guard_verdict: "FIX_FINDING:<id>"`, `merge_command_allowed: false`.
7. Else if any review finding has `validity: "valid"`, `severity: "debt"`, and no `disposition: "tracked_out_of_scope"`, return:
   `merge_readiness: "WITHHOLD"`, `blocking_predicate: "review-valid-finding"`, `guard_verdict: "FIX_FINDING:<id>"`, `merge_command_allowed: false`.
8. Else if any `other_required_checks` entry has `terminal_green: false` and `state_category` is omitted or `"non_terminal"`, return:
   `merge_readiness: "WITHHOLD"`, `blocking_predicate: "check-not-terminal-green"`, `guard_verdict: "WAIT_FOR_CHECKS"`, `merge_command_allowed: false`.
9. Else if any `other_required_checks` entry has `terminal_green: false` and `state_category` is `"terminal_failure"` or `"absent"`, return:
   `merge_readiness: "WITHHOLD"`, `blocking_predicate: "check-failed-or-absent"`, `guard_verdict: "MERGE_BLOCKED:<reason>"`, `merge_command_allowed: false`.
10. Else if `branch_hygiene_pr_state` is `"failed"`, return:
    `merge_readiness: "WITHHOLD"`, `blocking_predicate: "branch-hygiene"`, `guard_verdict: "MERGE_BLOCKED:<reason>"`, `merge_command_allowed: false`.
11. Else if `head_consistency` is `"failed"`, return:
    `merge_readiness: "WITHHOLD"`, `blocking_predicate: "head-mismatch"`, `guard_verdict: "MERGE_BLOCKED:<reason>"`, `merge_command_allowed: false`.
12. Else return:
    `merge_readiness: "HOLD"`, `blocking_predicate: "none"`, `guard_verdict: "MERGE_READY:<head_sha>"`, `merge_command_allowed: true`.

Ignore `host_mergeability`. `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, and `gh_pr_merge_would_accept: true` never authorize the merge command.

Case input:

```json
{input_json}
```

Verdict fields:

- `merge_readiness`: `"HOLD"` or `"WITHHOLD"`.
- `blocking_predicate`: one of `"review-absent"`, `"review-nonterminal"`, `"review-skipped-self-modifying-workflow"`, `"review-check-skipped"`, `"review-check-failed"`, `"review-valid-finding"`, `"check-not-terminal-green"`, `"check-failed-or-absent"`, `"branch-hygiene"`, `"head-mismatch"`, or `"none"`.
- `guard_verdict`: `"MERGE_READY:<head_sha>"`, `"WAIT_FOR_REVIEW"`, `"WAIT_FOR_CHECKS"`, `"MENTION_REVIEW_NEEDED:<trigger_phrase>"`, `"FIX_FINDING:<id>"`, or `"MERGE_BLOCKED:<reason>"`.
- `merge_command_allowed`: `true` or `false`.
