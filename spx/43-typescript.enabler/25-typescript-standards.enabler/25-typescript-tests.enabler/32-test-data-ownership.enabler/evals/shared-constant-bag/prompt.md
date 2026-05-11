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

Decide whether the file violates the rule. After any narrative analysis, emit exactly one final XML block in this shape — and nothing after it:

```
<verdict status="approved|rejected">
  <finding rule="shared-test-owned-constant-bag" present="true|false"/>
</verdict>
```

Set `status="rejected"` and `present="true"` when the file declares a shared test-owned constant bag for the rule above. Set `status="approved"` and `present="false"` when no such bag is declared. Do not emit other `<finding>` elements for this eval — limit the verdict to the single rule under audit.
