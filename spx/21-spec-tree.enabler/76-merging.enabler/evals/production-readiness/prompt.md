<!-- Prompt template for the production-readiness eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies the PRODUCTION_READINESS gate — whether
     /managing-pr executes the merge or withholds it pending operator
     approval — for a PR whose MERGE_READINESS already holds. The merge
     gate composition is probed by the merge-readiness eval. -->

You are simulating the agent that runs `/managing-pr` and evaluates the `PRODUCTION_READINESS` gate from `spx/15-agent-pr-authority.pdr.md`. `MERGE_READINESS` already holds for this PR; the only remaining question is whether the merge executes now or waits for operator approval.

`PRODUCTION_READINESS` holds when EITHER:

- the change is **not production-relevant**, per the project's recognition mechanism; or
- the operator has **explicitly approved** the merge.

The recognition mechanism is project-declared. When a project declares **no** recognition mechanism (`recognition_mechanism_declared` is `false`), every change is treated as not production-relevant — the permissive default — so `PRODUCTION_READINESS` holds and the merge executes. The agent does the identical `MERGE_READINESS` work in every case; only execution waits when `PRODUCTION_READINESS` does not hold.

Case id: substituted by the harness.

The gate-state input (JSON-encoded):

```json
{input_json}
```

Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — in this exact shape:

```
{
  "production_readiness": "HOLD" | "WITHHOLD",
  "merge_action": "MERGE" | "AWAIT_APPROVAL"
}
```

`production_readiness` reports the gate verdict: `HOLD` permits the merge to execute; `WITHHOLD` blocks execution pending approval. `merge_action` reports the action the agent takes: `MERGE` executes the merge, `AWAIT_APPROVAL` waits for the operator. The grader checks both together — `HOLD` pairs with `MERGE`, `WITHHOLD` pairs with `AWAIT_APPROVAL`; any cross-pairing (for example `HOLD` with `AWAIT_APPROVAL`) is wrong. The coupling ensures the model carries the gate verdict through to the action rather than emitting one without the other.
