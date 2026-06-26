<examples>

The skill's entire output is the JSON verdict (see `<verdict_format>` in the skill). These examples show the verdict shape for an APPROVED audit and a REJECTED audit; the audit runs no deterministic verification, so there is no automated-gates or test-execution row.

<example name="approved">

Auditing `product/config/` for a CLI tool.

```json
{
  "schema_version": 1,
  "skill": "audit-python",
  "target": "product/config/",
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

Every concern passes: 12 functions read with no surprises, IO separated from logic with dependency injection, package imports with no deep relatives, and the database ADR's constraints reflected in the code.

</example>

<example name="rejected-design-flaw">

Auditing `product/orders/` for a web service.

```json
{
  "schema_version": 1,
  "skill": "audit-python",
  "target": "product/orders/",
  "overall": "FAIL",
  "rows": [
    {
      "name": "function-comprehension",
      "status": "FAIL",
      "findings": [
        {
          "id": "f-001",
          "file": "product/orders/processor.py",
          "line": 42,
          "rule": "io-logic-tangle",
          "severity": "REJECT",
          "message": "Predict/verify: `process_orders` is predicted to compute and return order results, but the body computes totals AND sends confirmation emails via `sendgrid.send()`. IO is tangled with logic — the function cannot be tested without an email server. Extract `compute_order_totals` as a pure function and move sending behind an injected `EmailSender` protocol."
        }
      ]
    },
    {
      "name": "design-coherence",
      "status": "FAIL",
      "findings": [
        {
          "id": "f-002",
          "file": "product/orders/processor.py",
          "line": 42,
          "rule": "io-logic-separation",
          "severity": "REJECT",
          "message": "Core logic cannot be tested without IO; pure computation and the email side effect are not separated. Inject the email boundary via an `EmailSender` protocol parameter so the totals logic is exercisable in isolation."
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
          "file": "product/orders/processor.py",
          "line": 3,
          "rule": "dependency-injection",
          "severity": "REJECT",
          "message": "`from sendgrid import SendGridAPIClient` — the governing ADR requires external service calls to use dependency injection. A direct import creates a hard dependency. Accept an `EmailSender` protocol via parameter instead."
        }
      ]
    }
  ],
  "metadata": { "branch": "<branch>" }
}
```

</example>

</examples>
