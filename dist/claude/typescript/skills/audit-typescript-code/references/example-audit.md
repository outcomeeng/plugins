<examples>

The skill's entire output is the JSON concern verdict. These examples show `PASS` and `FAIL`; the audit runs no deterministic verification.

<example name="pass">

```json
{
  "schema_version": 1,
  "skill": "audit-typescript-code",
  "target": "src/config/",
  "overall": "APPROVED",
  "rows": [
    { "name": "function-comprehension", "status": "PASS", "findings": [] },
    { "name": "design-coherence", "status": "PASS", "findings": [] },
    { "name": "import-structure", "status": "PASS", "findings": [] },
    { "name": "adr-pdr-compliance", "status": "PASS", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

</example>

<example name="fail">

```json
{
  "schema_version": 1,
  "skill": "audit-typescript-code",
  "target": "src/orders/",
  "overall": "REJECTED",
  "rows": [
    {
      "name": "design-coherence",
      "status": "FAIL",
      "findings": [
        {
          "file": "src/orders/processor.ts",
          "line": 42,
          "rule": "io-logic-separation",
          "severity": "blocking",
          "message": "Order calculation and email delivery share one function, coupling core behavior to an external side effect.",
          "observed": "processOrders computes totals and calls the concrete email client in the same body",
          "expected": "core order calculation is independently observable and external delivery crosses an injected boundary"
        }
      ]
    }
  ],
  "metadata": { "branch": "<branch>" }
}
```

</example>

</examples>
