---
id: 01a0ebba-5f64-73f1-8795-b556d633527b
malleability: spec
---

# Authoring

PROVIDES an operator-facing specification workflow backed by a decision-ready artifact-writing protocol
SO THAT spec authors and implementation workflows
CAN change durable declarations through one context-complete boundary without duplicating placement, drafting, or validation behavior

## Assertions

### Audit: authoring boundary

- spec-entry: Operator-driven creation, modification, or removal of durable declarations enters through `/spec`, which owns requirements convergence and delegates decision-ready writes to `/author`.
- context-preserved: `/spec` and `/author` preserve the loaded context, structure ownership, templates, durable-map voice, and downstream alignment rules across every declaration change.
- no-second-workflow: `/author` is no second operator-facing specification workflow; it is an internal protocol invoked with a decision-ready artifact packet.

### Audit: assertion form

- writes-typed-rows: `/author` writes each spec Assertion outside a Mapping or Evaluate subsection opened by its slug and a colon under the group heading that names its verification type, a Scenario Assertion with only its slug and the colon on its first line and indented Given, When, Then and And lines after it; writes each Mapping or Evaluate Assertion as its own `Test.Mapping:` or `Evaluate:` subsection headed by its slug, holding one sentence and one table whose first cell in each row holds the slug of its case; writes no tag; and keeps the group or subsection heading a Change's Declarations line states for that Assertion.
