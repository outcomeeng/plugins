<!-- Prompt template for the check-watch-fallback eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: the eval verifies the PR check wait contract in
     /tracking-tasks, /standardizing-merging, /opening-pr, and /managing-pr.
     The runtime timer or heartbeat is preferred when available. When it is
     unavailable, the PR lifecycle uses one foreground `gh pr checks` watcher,
     then inspects the full merge gate before acting. -->

Closed classification task. Do not invoke skills, do not inspect a repository, do not wait for more instructions, and do not run tools. Read the JSON wait plan below and return the verdict JSON object only.

The wait contract:

- If a runtime heartbeat or timer is available, schedule or refresh it and re-enter the managing flow from the PR pointer.
- If no runtime heartbeat or timer is available and the open PR is blocked by check completion — a non-terminal required check, a non-terminal reviewing-kind check, or absent review output while another current-head check is non-terminal — run exactly one foreground command: `gh pr checks <pr-number> --watch --fail-fast --interval 30`.
- After that foreground watcher exits, inspect the full merge gate before choosing the next action: PR state, check rollup, PR-level comments, formal reviews, and review-thread comments.
- Background waits, shell polling loops, background `sleep`, and `gh run watch` are invalid wait mechanisms.

Classify the wait plan in the input.

Case id: substituted by the harness.

The wait plan (JSON-encoded):

```json
{input_json}
```

Verdict schema — three fields, all mandatory:

- `strategy`: `"runtime-heartbeat"`, `"foreground-pr-check-watch"`, `"invalid-wait"`, or `"wait-token"`.
- `post_wait_inspection_complete`: `true` only when the plan inspects PR state, check rollup, PR-level comments, formal reviews, and review-thread comments after the foreground watcher exits. For runtime-heartbeat plans, use `false`.
- `violation`: `"none"`, `"missing-watch"`, `"wrong-watch-command"`, `"missing-post-watch-inspection"`, `"forbidden-background-or-polling"`, or `"runtime-timer-bypassed"`.

The grader checks the three fields together. A no-timer plan with pending checks is valid only with `strategy: "foreground-pr-check-watch"`, `post_wait_inspection_complete: true`, and `violation: "none"`. A plan that only emits a wait token while no runtime timer exists must report `violation: "missing-watch"`.
