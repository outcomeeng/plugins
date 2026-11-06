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

- pdr-form: ALWAYS: a PDR states its decision in the opening of the PDR template and every rule as the PDR template writes it, and its rules awaiting verification selection stay ungrouped directly under `## Verification`.
- adr-form: ALWAYS: an ADR states its decision in the opening of the ADR template and every rule as the ADR template writes it, its invariants are rules of a Property group, and its rules awaiting verification selection stay ungrouped directly under `## Verification`.
