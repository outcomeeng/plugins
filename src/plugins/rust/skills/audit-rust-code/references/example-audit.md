<examples>

The skill's entire output is the JSON verdict (see `<verdict_format>` in the skill). These examples show the verdict shape for an approved change and a design rejection; the audit runs no deterministic verification, so there is no automated-gates or test-execution row. A scope with no `unsafe` sites reports the `unsafe-soundness` row as `UNKNOWN`.

<example name="approved">
Auditing `src/config/` for a CLI crate.

```json
{
  "schema_version": 1,
  "skill": "audit-rust-code",
  "target": "src/config/",
  "overall": "PASS",
  "rows": [
    { "name": "function-comprehension", "status": "PASS", "findings": [] },
    { "name": "design-coherence", "status": "PASS", "findings": [] },
    { "name": "import-structure", "status": "PASS", "findings": [] },
    {
      "name": "unsafe-soundness",
      "status": "UNKNOWN",
      "explanation": "scope contains no unsafe blocks, unsafe functions, unsafe impls, extern C boundaries, or no_mangle exports",
      "findings": []
    },
    { "name": "adr-pdr-compliance", "status": "PASS", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

</example>

<example name="rejected-design-flaw">
Auditing `src/orders/`.

````json
{
  "schema_version": 1,
  "skill": "audit-rust-code",
  "target": "src/orders/",
  "overall": "FAIL",
  "rows": [
    {
      "name": "function-comprehension",
      "status": "FAIL",
      "findings": [
        {
          "id": "f-001",
          "file": "src/orders/processor.rs",
          "line": 42,
          "rule": "io-logic-tangle",
          "severity": "REJECT",
          "message": "Predict/verify: `process_orders` is predicted to compute and return order summaries, but the body computes totals, persists state, and sends emails through a concrete client. The boundary call prevents isolated verification of the pricing logic. Extract `compute_order_summaries` as a pure function and move sending behind an injected `EmailSender` trait. Correct approach:\n\n```rust\ntrait EmailSender {\n    fn send(&self, summary: &OrderSummary) -> Result<(), EmailError>;\n}\n\nfn compute_order_summaries(orders: &[Order]) -> Vec<OrderSummary> {\n    orders.iter().map(OrderSummary::from).collect()\n}\n\nfn process_orders<S: EmailSender>(orders: &[Order], sender: &S) -> Result<(), ProcessOrdersError> {\n    for summary in compute_order_summaries(orders) {\n        sender.send(&summary)?;\n    }\n    Ok(())\n}\n```"
        }
      ]
    },
    {
      "name": "design-coherence",
      "status": "FAIL",
      "findings": [
        {
          "id": "f-002",
          "file": "src/orders/processor.rs",
          "line": 42,
          "rule": "io-logic-separation",
          "severity": "REJECT",
          "message": "Pure computation and boundary calls are tangled; the pricing logic cannot be exercised without the email client. Inject the email boundary through a trait or narrow function seam. Correct approach:\n\n```rust\nfn compute_order_summaries(orders: &[Order]) -> Vec<OrderSummary> {\n    orders.iter().map(OrderSummary::from).collect()\n}\n\nfn process_orders<S: EmailSender>(orders: &[Order], sender: &S) -> Result<(), ProcessOrdersError> {\n    for summary in compute_order_summaries(orders) {\n        sender.send(&summary)?;\n    }\n    Ok(())\n}\n```"
        }
      ]
    },
    { "name": "import-structure", "status": "PASS", "findings": [] },
    {
      "name": "unsafe-soundness",
      "status": "UNKNOWN",
      "explanation": "scope contains no unsafe blocks, unsafe functions, unsafe impls, extern C boundaries, or no_mangle exports",
      "findings": []
    },
    {
      "name": "adr-pdr-compliance",
      "status": "FAIL",
      "findings": [
        {
          "id": "f-003",
          "file": "src/orders/processor.rs",
          "line": 3,
          "rule": "dependency-injection",
          "severity": "REJECT",
          "message": "The module imports a concrete email client directly, while the governing ADR requires an injected seam for external services. Depend on an `EmailSender` trait passed in instead. Correct approach:\n\n```rust\ntrait EmailSender {\n    fn send(&self, summary: &OrderSummary) -> Result<(), EmailError>;\n}\n\nfn process_orders<S: EmailSender>(orders: &[Order], sender: &S) -> Result<(), ProcessOrdersError> {\n    ...\n}\n```"
        }
      ]
    }
  ],
  "metadata": { "branch": "<branch>" }
}
````

</example>

</examples>
