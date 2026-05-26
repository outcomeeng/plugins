<!-- Prompt template for the merge-readiness eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies the MERGE_READINESS gate composition —
     whether /managing-pr's merge gate holds — given the current-head CI
     spec-tree-review findings (each already judged valid or unbacked) and
     the terminal-green status of every other required check. The
     state-to-terminal-green mapping is probed separately by the
     terminal-green eval; the production-relevance permission by the
     production-readiness eval. -->

You are simulating the agent that runs `/managing-pr` and evaluates the `MERGE_READINESS` gate from `spx/15-agent-pr-authority.pdr.md` on an open PR.

`MERGE_READINESS` holds when BOTH predicates hold:

- **the current-head CI `spec-tree-review` reports no valid finding** — a finding the agent judged unbacked (not valid) is dropped and does not block; a *valid* finding is unresolved work that the agent must fix before merge, so it withholds the gate; and
- **every other required check is terminal-green** — each check carries a precomputed `terminal_green` boolean for this eval.

Decide the gate. Check the review predicate first: if any finding is `valid`, the gate withholds and the blocking predicate is `review-valid-finding`. Otherwise, if any other required check is not terminal-green, the gate withholds and the blocking predicate is `check-not-terminal-green`. Otherwise the gate holds.

Case id: substituted by the harness.

The gate-state input (JSON-encoded):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — in this exact shape:

```
{
  "merge_readiness": "HOLD" | "WITHHOLD",
  "blocking_predicate": "review-valid-finding" | "check-not-terminal-green" | "none"
}
```

`merge_readiness` reports the gate verdict: `HOLD` means the merge predicates are satisfied; `WITHHOLD` means at least one is unmet. `blocking_predicate` reports which predicate drove a withhold, or `none` when the gate holds. The grader checks both together — `HOLD` paired with `none` is correct when no valid finding remains and every other check is terminal-green; `WITHHOLD` paired with `none` is wrong, because the gate withholds only on a named failing predicate. The coupling ensures the model identifies WHY the gate withheld rather than guessing the verdict.
