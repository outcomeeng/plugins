<!-- Prompt template for the auditor-verdict-handling eval.
     The harness substitutes the case id and input JSON tokens before
     sending the prompt to the model.

     Probe scope: the eval verifies the PR workflow's handling of
     structured auditor verdicts that surface while the agent is driving
     review feedback. -->

You are simulating the agent that runs `/managing-pr` and triages auditor verdicts surfaced while driving PR review feedback.

The handling rule:

- A `REJECTED` or `UNKNOWN` overall verdict, a `FAIL` or `UNKNOWN` row, or a `REJECT` finding is in-slice unresolved work when the verdict cites a concern or audit uncertainty in this PR's diff. The agent fixes the cited issue or resolves the audit uncertainty before merge.
- `APPROVED`, `PASS`, `INFO`, and `WARNING` do not require a blocking repair by themselves.
- The agent must not leave an in-slice `REJECTED`, `UNKNOWN`, `FAIL`, or `REJECT` as deferred `ISSUES.md` / `PLAN.md` work on the open PR.

Decide the required action for the verdict in the input. Check in this order: (1) if `in_pr_diff` is `false`, the issue is not in this PR's shipped diff and the action is `TRACK_OUT_OF_PR`; (2) else if the overall is `REJECTED` or `UNKNOWN`, any row status is `FAIL` or `UNKNOWN`, or any finding verdict is `REJECT`, the action is `FIX_BEFORE_MERGE`; (3) otherwise the verdict is satisfied for this PR and the action is `NO_REPAIR`.

Case id: substituted by the harness.

The auditor verdict summary (JSON-encoded):

```json
{input_json}
```

Verdict schema — two fields, both mandatory:

- `required_action`: `"FIX_BEFORE_MERGE"`, `"TRACK_OUT_OF_PR"`, or `"NO_REPAIR"`.
- `merge_blocked`: `true` only when the required action is `FIX_BEFORE_MERGE`.

The grader checks both together. `FIX_BEFORE_MERGE` must pair with `merge_blocked: true`; the other actions must pair with `merge_blocked: false`.
