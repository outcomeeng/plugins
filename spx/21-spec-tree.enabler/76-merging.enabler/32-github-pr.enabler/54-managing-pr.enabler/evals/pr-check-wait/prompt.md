<!-- Prompt template for the pr-check-wait eval.
     Materialized from src/plugins/spec-tree/skills/manage-pr/SKILL.md, section "pr_wait_and_reentry_policy". -->

This is an eval invocation. Do not ask clarifying questions. Do not invoke skills. Do not inspect a repository. Do not run tools. Return the verdict JSON object only.

Evaluate the wait and re-entry plan against this producer section from `src/plugins/spec-tree/skills/manage-pr/SKILL.md`. The section is the source under audit; do not replace it with a copied policy or external memory.

```text
<step name="pr_wait_and_reentry_policy">

`/manage-pr` is the re-entry point for an open pull request. When the user asks to manage, wait on, or continue a PR lifecycle, invoke `/manage-pr <pr-number|url|branch>` and inspect live GitHub and repository state before acting. When no pointer is provided, resolve the PR from the current branch with bare `gh pr view`.

Action tokens are pass-local observations derived from the current live inspection. `WAIT_FOR_REVIEW`, `WAIT_FOR_CHECKS`, `MENTION_REVIEW_NEEDED:<trigger-phrase>`, `MERGE_READY:<head-sha>`, `MERGE_BLOCKED:<reason>`, and `POST_MERGE_VERIFY` never store PR state and never authorize a later wait, merge, or closeout without a fresh `/manage-pr` inspection pass. After compaction or when the foundation is absent, restart from Step 0. After foreground wait completion, a push, a review arrival, an operator reply, or any new user turn, discard prior action-token authority and return to Step 1 for the PR pointer.

When PR checks or current-head review output are not terminal, `/manage-pr` runs exactly one foreground wait command, `gh pr checks <pr-number> --watch --fail-fast --interval 30`, then discards the pre-wait token authority and re-inspects PR state, check rollup, PR-level comments, formal reviews, review-thread comments, and base drift before deciding the next action. Runtime heartbeats, runtime timers, background waits, shell polling, background `sleep`, and `gh run watch` are invalid wait mechanisms for GitHub PR checks.

GitHub and the local repository are authoritative for PR state. Conversation memory and prior tokens are only routing hints that name why `/manage-pr` is being re-entered.

</step>
```

Case id: {case_id}

Input plan:

```json
{input_json}
```

Return one JSON object with exactly these fields:

- `strategy`: `"foreground-pr-check-wait"`, `"invalid-wait"`, `"invalid-reentry"`, or `"wait-token"`.
- `post_wait_inspection_complete`: boolean.
- `violation`: `"none"`, `"missing-wait"`, `"wrong-watch-command"`, `"missing-post-watch-inspection"`, `"forbidden-background-or-polling"`, `"runtime-timer-used"`, or `"stale-action-token"`.
- `pr_pointer_resolution`: `"explicit-pointer"`, `"current-branch-fallback"`, `"missing"`, or `"not-applicable"`.
- `token_authority`: `"fresh-inspection-required"`, `"stale-token-authority"`, or `"not-applicable"`.

Classify from the producer section:

- A plan that only emits a wait token while PR checks or review output are still pending is missing the required foreground wait.
- A plan that uses background waits, runtime heartbeats, shell polling, background `sleep`, or `gh run watch` for PR checks uses an invalid wait mechanism.
- A plan that runs the exact foreground `gh pr checks <pr-number> --watch --fail-fast --interval 30` command must also inspect PR state, check rollup, PR-level comments, formal reviews, and review-thread comments after the wait exits before it is complete.
- A plan entered with an explicit PR number, URL, or branch pointer must resolve that pointer before PR inspection.
- A plan acting from a prior action token after a new user turn, compaction, wait completion, push, review arrival, or operator reply uses stale token authority unless it performs a fresh PR inspection first.
- Set `pr_pointer_resolution` to `"explicit-pointer"` when the input provides a PR number, PR URL, or branch pointer and the plan acts on that PR; set it to `"current-branch-fallback"` only when no pointer is provided and the plan uses current-branch PR resolution; set it to `"missing"` when the plan acts from stale token authority or an unresolved pointer; set it to `"not-applicable"` only when the case has no PR identity concern.
- Set `token_authority` to `"stale-token-authority"` when a prior action token authorizes an action after an invalidation trigger; set it to `"fresh-inspection-required"` when the plan waits or acts in a way that requires a fresh post-wait or post-pointer inspection; set it to `"not-applicable"` when token freshness is not implicated by the plan.
