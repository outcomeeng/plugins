<!-- Prompt template for the pr-check-wait eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: the eval verifies the PR check wait and PR re-entry contracts in
     /merging-standards, /open-pr, and /manage-pr. The PR lifecycle
     uses one foreground `gh pr checks` wait, then inspects the full merge gate
     before acting. A re-entry pass resolves an explicit PR pointer before
     inspection and treats prior action tokens as non-authoritative. -->

Closed classification task. Do not invoke skills, do not inspect a repository, do not wait for more instructions, and do not run tools. Read the JSON wait plan below and return the verdict JSON object only.

The wait contract:

- If the open PR is blocked by check completion — a non-terminal required check, a non-terminal review-kind check, or absent review output while another current-head check is non-terminal — run exactly one foreground command: `gh pr checks <pr-number> --watch --fail-fast --interval 30`.
- After that foreground wait exits, inspect the full merge gate before choosing the next action: PR state, check rollup, PR-level comments, formal reviews, and review-thread comments.
- Runtime heartbeats, runtime timers, background waits, shell polling loops, background `sleep`, and `gh run watch` are invalid wait mechanisms for GitHub PR checks.
- If a PR number, URL, or branch pointer is provided, resolve that pointer before inspecting PR state; use bare current-branch `gh pr view` only when no pointer is provided.
- Prior action tokens are pass-local observations. After a foreground wait, push, review arrival, operator reply, or new user turn, a plan must discard stale token authority and perform a fresh PR inspection before any wait, merge, or closeout action.

Classify the wait plan in the input.

Case id: substituted by the harness.

The wait plan (JSON-encoded):

```json
{input_json}
```

Verdict schema — five fields, all mandatory:

- `strategy`: `"foreground-pr-check-wait"`, `"invalid-wait"`, `"invalid-reentry"`, or `"wait-token"`.
- `post_wait_inspection_complete`: `true` only when the plan inspects PR state, check rollup, PR-level comments, formal reviews, and review-thread comments after the foreground wait exits.
- `violation`: `"none"`, `"missing-wait"`, `"wrong-watch-command"`, `"missing-post-watch-inspection"`, `"forbidden-background-or-polling"`, `"runtime-timer-used"`, or `"stale-action-token"`.
- `pr_pointer_resolution`: `"explicit-pointer"`, `"current-branch-fallback"`, `"missing"`, or `"not-applicable"`.
- `token_authority`: `"fresh-inspection-required"`, `"stale-token-authority"`, or `"not-applicable"`.

The grader checks the five fields together. A pending-check plan is valid only with `strategy: "foreground-pr-check-wait"`, `post_wait_inspection_complete: true`, and `violation: "none"`. A plan that only emits a wait token must report `violation: "missing-wait"`.
A re-entry plan with an explicit PR number, URL, or branch pointer is valid only with `pr_pointer_resolution: "explicit-pointer"`. A plan that acts from a prior action token without fresh inspection must report `strategy: "invalid-reentry"`, `violation: "stale-action-token"`, and `token_authority: "stale-token-authority"`.
