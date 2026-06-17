<!-- Prompt template for the review-readiness eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies the REVIEW_READINESS gate decision —
     whether /open-pr opens the PR ready_for_review — given the
     deterministic-verification result and the local-review state. The
     reviewer's own behavior (review-changes producing findings) has
     its own evals under spx/21-spec-tree.enabler/68-reviewing.enabler/
     21-reviewing-changes.enabler/evals/. -->

You are simulating the agent that runs `/open-pr` and evaluates the `REVIEW_READINESS` gate from `spx/15-merging.pdr.md` before opening the PR.

`REVIEW_READINESS` holds when BOTH predicates hold:

- **deterministic verification passes** — the project's full validation-and-testing command reported success; and
- **the local review has converged** — every *valid* finding from `review-changes` is either fixed in the diff or split out of the changeset and captured in `ISSUES.md` / `PLAN.md`. A finding the agent judged unbacked (not valid) is dropped and does not block. A *valid* finding still `unaddressed` (neither fixed nor split out) means the review has not converged.

Decide the gate. If deterministic verification failed, the gate withholds and the blocking predicate is `deterministic-verification` (it is checked first). Otherwise, if any valid finding is unaddressed, the gate withholds and the blocking predicate is `local-review`. Otherwise the gate holds and the PR opens ready.

Case id: substituted by the harness.

The gate-state input (JSON-encoded):

```json
{input_json}
```

Verdict schema — two fields, both mandatory:

- `open_decision`: `"OPEN_READY"` (gate holds, PR opens ready) or `"WITHHOLD"` (gate fails, PR stays unopened).
- `blocking_predicate`: `"deterministic-verification"`, `"local-review"`, or `"none"`.

The grader checks both together — `OPEN_READY` paired with `none` is correct when both predicates hold; `WITHHOLD` paired with `none` is wrong, because the gate withholds only on a named failing predicate.
