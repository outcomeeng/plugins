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

</example>

<example name="rejected-design-flaw">

Auditing `product/orders/` for a web service.

````json
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
          "message": "Predict/verify: `process_orders` is predicted to compute and return order results, but the body computes totals AND sends confirmation emails via `sendgrid.send()`. IO is tangled with logic — the function cannot be tested without an email server. Extract `compute_order_totals` as a pure function and move sending behind an injected `EmailSender` protocol. Correct approach:\n\n```python\nfrom typing import Protocol\n\n\nclass EmailSender(Protocol):\n    async def send(self, to: str, subject: str, body: str) -> None: ...\n\n\ndef compute_order_totals(orders: list[Order]) -> list[OrderSummary]:\n    \"\"\"Pure computation -- no IO.\"\"\"\n    ...\n\n\nasync def process_orders(orders: list[Order], *, send_email: EmailSender) -> None:\n    for summary in compute_order_totals(orders):\n        await send_email.send(summary.to, summary.subject, summary.body)\n```"
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
          "message": "Core logic cannot be tested without IO; pure computation and the email side effect are not separated. Inject the email boundary via an `EmailSender` protocol parameter so the totals logic is exercisable in isolation. Correct approach:\n\n```python\ndef compute_order_totals(orders: list[Order]) -> list[OrderSummary]:\n    ...\n\n\nasync def process_orders(orders: list[Order], *, send_email: EmailSender) -> None:\n    for summary in compute_order_totals(orders):\n        await send_email.send(summary.to, summary.subject, summary.body)\n```"
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
          "message": "`from sendgrid import SendGridAPIClient` — the governing ADR requires external service calls to use dependency injection. A direct import creates a hard dependency. Accept an `EmailSender` protocol via parameter instead. Correct approach:\n\n```python\nfrom typing import Protocol\n\n\nclass EmailSender(Protocol):\n    async def send(self, to: str, subject: str, body: str) -> None: ...\n\n\nasync def process_orders(orders: list[Order], *, send_email: EmailSender) -> None:\n    ...\n```"
        }
      ]
    }
  ],
  "metadata": { "branch": "<branch>" }
}
````

</example>

</examples>
