<!-- Prompt template for the review-readiness eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies the REVIEW_READINESS gate decision —
     whether /opening-pr opens the PR ready_for_review — given the
     deterministic-verification result and the local-review state. The
     reviewer's own behavior (reviewing-changes producing findings) has
     its own evals under spx/21-spec-tree.enabler/68-reviewing.enabler/
     21-reviewing-changes.enabler/evals/. -->

You are simulating the agent that runs `/opening-pr` and evaluates the `REVIEW_READINESS` gate from `spx/15-agent-pr-authority.pdr.md` before opening the PR.

`REVIEW_READINESS` holds when BOTH predicates hold:

- **deterministic verification passes** — the project's full validation-and-testing command reported success; and
- **the local review has converged** — every *valid* finding from `reviewing-changes` is either fixed in the diff or split out of the changeset and captured in `ISSUES.md` / `PLAN.md`. A finding the agent judged unbacked (not valid) is dropped and does not block. A *valid* finding still `unaddressed` (neither fixed nor split out) means the review has not converged.

Decide the gate. If deterministic verification failed, the gate withholds and the blocking predicate is `deterministic-verification` (it is checked first). Otherwise, if any valid finding is unaddressed, the gate withholds and the blocking predicate is `local-review`. Otherwise the gate holds and the PR opens ready.

Case id: substituted by the harness.

The gate-state input (JSON-encoded):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — in this exact shape:

```
{
  "open_decision": "OPEN_READY" | "WITHHOLD",
  "blocking_predicate": "deterministic-verification" | "local-review" | "none"
}
```

`open_decision` reports the gate verdict: `OPEN_READY` opens the PR `ready_for_review`; `WITHHOLD` keeps it unopened. `blocking_predicate` reports which predicate drove a withhold (`deterministic-verification` or `local-review`), or `none` when the gate holds. The grader checks both together — `OPEN_READY` paired with `none` is correct when both predicates hold; `WITHHOLD` paired with `none` is wrong, because the gate withholds only on a named failing predicate. The coupling ensures the model identifies WHY the gate withheld rather than guessing the verdict.
