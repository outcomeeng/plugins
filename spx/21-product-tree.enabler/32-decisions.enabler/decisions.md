---
id: 01a0ebba-5f61-73ed-9937-4479d0d25e40
malleability: spec
---

# Decisions

PROVIDES the decision record lifecycle — creation and auditing of ADRs and PDRs
SO THAT all product-tree projects
CAN govern architecture and product behavior through enforceable, auditable decision records

## Assertions

### Compliance

- pdr-form: ALWAYS: a PDR states its decision in the opening of the PDR template and every rule as the PDR template writes it, and its rules awaiting verification selection stay ungrouped directly under `## Verification`. [audit]
- adr-form: ALWAYS: an ADR keeps rules awaiting verification selection untagged directly under `## Verification`; selected rules are grouped by verification type — `### Testing`, `### Eval`, `### Audit`; `/verify` selects the verification type, a `### Testing` rule carries an assertion type that `/test` selects from the rule's quantifier (scenario, mapping, conformance, property, compliance), an `### Eval` rule carries `[eval]`, and an `### Audit` rule carries `[audit]` led by its slug, unique within its record. [audit]
