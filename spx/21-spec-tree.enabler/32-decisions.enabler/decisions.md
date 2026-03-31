# Decisions

PROVIDES the decision record lifecycle — creation, auditing, and downstream enforcement of ADRs and PDRs
SO THAT all spec-tree projects
CAN govern architecture and product behavior through enforceable, auditable decision records

## Assertions

### Compliance

- ALWAYS: verify that compliance rules in decision records flow into spec assertions somewhere in the governed subtree ([review])
- NEVER: approve a decision record whose constraints have zero downstream enforcement ([review])
