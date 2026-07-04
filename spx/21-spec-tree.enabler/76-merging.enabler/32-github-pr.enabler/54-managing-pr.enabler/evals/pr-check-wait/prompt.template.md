<!-- Prompt template for the pr-check-wait eval.
     Materialized from {producer_path}, section "{producer_section_name}". -->

This is an eval invocation. Do not ask clarifying questions. Do not invoke skills. Do not inspect a repository. Do not run tools. Return the verdict JSON object only.

Evaluate the wait and re-entry plan against this producer section from `{producer_path}`. The section is the source under audit; do not replace it with a copied policy or external memory.

```text
{producer_section}
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
