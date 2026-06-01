# Decisions

PROVIDES the decision record lifecycle — creation, auditing, and downstream enforcement of ADRs and PDRs
SO THAT all spec-tree projects
CAN govern architecture and product behavior through enforceable, auditable decision records

## Assertions

### Compliance

- ALWAYS: verify that compliance rules in decision records flow into spec assertions somewhere in the governed subtree ([review])
- ALWAYS: every decision-record compliance rule declares a single evidence mode — one of scenario, mapping, conformance, property, compliance — chosen via /testing from the rule's claim shape ([review])
- NEVER: approve a decision record whose constraints have zero downstream enforcement ([review])
