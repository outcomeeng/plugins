<examples>

The skill's entire output is the JSON verdict (see `<verdict_format>` in the skill). These examples show the verdict shape for an APPROVED audit and a REJECTED audit; the audit runs no deterministic verification, so there is no automated-gates or test-execution row.

<example name="approved">

Auditing `src/config/` for a CLI tool.

```json
{
  "schema_version": 1,
  "skill": "audit-typescript",
  "target": "src/config/",
  "overall": "PASS",
  "rows": [
    { "name": "function-comprehension", "status": "PASS", "findings": [] },
    { "name": "design-coherence", "status": "PASS", "findings": [] },
    { "name": "import-structure", "status": "PASS", "findings": [] },
    { "name": "adr-pdr-compliance", "status": "PASS", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Every concern passes: 12 functions read with no surprises, IO separated from logic with dependency injection, path aliases with no deep relatives, and the database ADR's constraints reflected in the code.

</example>

<example name="rejected-design-flaw">

Auditing `src/orders/` for an e-commerce service.

```json
{
  "schema_version": 1,
  "skill": "audit-typescript",
  "target": "src/orders/",
  "overall": "FAIL",
  "rows": [
    {
      "name": "function-comprehension",
      "status": "FAIL",
      "findings": [
        {
          "id": "f-001",
          "file": "src/orders/processor.ts",
          "line": 42,
          "rule": "io-logic-tangle",
          "severity": "REJECT",
          "message": "Predict/verify: `processOrders` is predicted to compute and return order results, but the body computes totals AND sends confirmation emails via `sendgrid.send()`. IO is tangled with logic — the function cannot be tested without an email service. Extract `computeOrderTotals` as a pure function and move sending behind an injected `EmailSender` dependency."
        }
      ]
    },
    {
      "name": "design-coherence",
      "status": "FAIL",
      "findings": [
        {
          "id": "f-002",
          "file": "src/orders/processor.ts",
          "line": 42,
          "rule": "io-logic-separation",
          "severity": "REJECT",
          "message": "Core logic cannot be tested without IO; pure computation and the email side effect are not separated. Inject the email boundary via a `deps` parameter so the totals logic is exercisable in isolation."
        }
      ]
    },
    { "name": "import-structure", "status": "PASS", "findings": [] },
    {
      "name": "adr-pdr-compliance",
      "status": "FAIL",
      "findings": [
        {
          "id": "f-003",
          "file": "src/orders/processor.ts",
          "line": 3,
          "rule": "dependency-injection",
          "severity": "REJECT",
          "message": "`import { send } from \"@sendgrid/mail\"` — the governing ADR requires external service calls to use dependency injection. A direct import creates a hard dependency. Accept an `EmailSender` via a `deps` parameter instead."
        }
      ]
    }
  ],
  "metadata": { "branch": "<branch>" }
}
```

</example>

</examples>
