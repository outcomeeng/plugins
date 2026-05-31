<!-- Prompt template for the merge-readiness eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies the MERGE_READINESS gate composition —
     whether /managing-pr's merge gate holds — given the current-head CI
     spec-tree-review findings (each already judged valid or unbacked), the
     terminal-green status of every other required check, and whether branch
     hygiene plus PR state hold. The state-to-terminal-green mapping is
     probed separately by the terminal-green eval; the production-relevance
     permission by the production-readiness eval. -->

You are simulating the agent that runs `/managing-pr` and evaluates the `MERGE_READINESS` gate from `spx/15-agent-pr-authority.pdr.md` on an open PR.

`MERGE_READINESS` holds when ALL predicates hold:

- **the current-head CI `spec-tree-review` reports no valid finding** — a finding the agent judged unbacked (not valid) is dropped and does not block; a *valid* finding is unresolved work the agent must fix before merge, so it withholds the gate;
- **every other required check is terminal-green** — each check carries a precomputed `terminal_green` boolean for this eval;
- **branch hygiene and PR state hold** — `branch_hygiene_pr_state` is `ok` when the upstream-safety branch-hygiene checks pass and the PR is `OPEN`, not draft, with the inspected head SHA matching origin and the branch rebased onto `origin/<base>`; it is `failed` when any of those does not hold (dirty tree, upstream tracking the default branch, still draft, head-SHA mismatch, or behind base).

Decide the gate, checking the predicates in this order so the blocking predicate is reported deterministically: (1) if any finding is `valid`, withhold with blocking predicate `review-valid-finding`; (2) else if any other required check is not terminal-green, withhold with `check-not-terminal-green`; (3) else if `branch_hygiene_pr_state` is `failed`, withhold with `branch-hygiene`; (4) else the gate holds.

Case id: substituted by the harness.

The gate-state input (JSON-encoded):

```json
{input_json}
```

Verdict schema — two fields, both mandatory:

- `merge_readiness`: `"HOLD"` (merge predicates satisfied) or `"WITHHOLD"` (at least one unmet).
- `blocking_predicate`: `"review-valid-finding"`, `"check-not-terminal-green"`, `"branch-hygiene"`, or `"none"`.

The grader checks both together — `HOLD` paired with `none` is correct when all predicates hold; `WITHHOLD` paired with `none` is wrong, because the gate withholds only on a named failing predicate.
