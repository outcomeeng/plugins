<!-- Prompt template for the shared-constant-bag eval.
     The harness substitutes {case_id} and {input_json}.
-->

You are auditing a single TypeScript test file against the test-data-ownership rules in `spx/43-typescript.enabler/25-typescript-standards.enabler/25-typescript-tests.enabler/32-test-data-ownership.enabler/test-data-ownership.md`.

The rule under audit is:

> NEVER: create shared test-owned constants such as `TEST_FIXTURES`, `SAMPLE_PATHS`, `TYPICAL`, or `EDGES` to satisfy literal-reuse checks — named example bags preserve hand-picked values.

Case id: `{case_id}`

The file under audit (JSON-encoded payload follows):

```json
{input_json}
```

Decide whether the file violates the rule. Your **entire response** must be exactly one JSON document — no prose, no markdown fences, no commentary before or after — in this exact shape:

```
{
  "status": "approved" | "rejected",
  "findings": [
    { "rule": "shared-test-owned-constant-bag", "present": true | false }
  ]
}
```

Set `"status": "rejected"` and `"present": true` when the file declares a shared test-owned constant bag for the rule above. Set `"status": "approved"` and `"present": false` when no such bag is declared. Emit exactly one finding object for this eval — do not include findings for other rules. The response must be parseable JSON; the harness parses your entire response with `json.loads`.
