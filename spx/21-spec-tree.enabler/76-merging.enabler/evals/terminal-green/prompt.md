<!-- Prompt template for the terminal-green eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies the terminal-green classification of a
     single required check from its statusCheckRollup state — the mapping
     the MERGE_READINESS gate applies to every other required check. The
     gate composition is probed by the merge-readiness eval. -->

You are simulating the agent classifying one required check from a PR's `statusCheckRollup`, applying the `terminal-green` definition in `spx/15-merging.pdr.md`.

A check is either a **check run** (`status` reaches `COMPLETED`, then a `conclusion`) or a **status context** (`state`). Classify the single check in the input:

- **terminal-green** — terminal AND successful: a check run with `status == COMPLETED` and `conclusion == SUCCESS`, or a status context with `state == SUCCESS`.
- **not-terminal** — still running: a check run with `status ∈ {QUEUED, IN_PROGRESS}`, or a status context with `state ∈ {EXPECTED, PENDING}`. No conclusion yet, so neither green nor red.
- **terminal-not-success** — finished without success: a check run with `status == COMPLETED` and `conclusion ∈ {FAILURE, CANCELLED, TIMED_OUT, SKIPPED, NEUTRAL, ACTION_REQUIRED, …}`, or a status context with `state ∈ {ERROR, FAILURE}`.
- **absent** — the required check is missing from the rollup (`present == false`).

Only `terminal-green` satisfies the `MERGE_READINESS` check predicate; `not-terminal`, `terminal-not-success`, and `absent` all block it.

Case id: substituted by the harness.

The single required check (JSON-encoded):

```json
{input_json}
```

Verdict schema — two fields, both mandatory:

- `terminal_green`: `true` only for the `terminal-green` classification, `false` for the other three.
- `classification`: one of `"terminal-green"`, `"not-terminal"`, `"terminal-not-success"`, `"absent"`.

The grader checks both together — `terminal_green: true` must pair with `classification: "terminal-green"`, and `terminal_green: false` must pair with one of the blocking classifications.
