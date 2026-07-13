# Authoring

PROVIDES an operator-facing specification workflow backed by a decision-ready artifact-writing protocol
SO THAT spec authors and implementation workflows
CAN change durable declarations through one context-complete boundary without duplicating placement, drafting, or validation behavior

## Assertions

### Compliance

- ALWAYS: operator-driven creation, modification, or removal of durable declarations enters through `/spec`, which owns requirements convergence and delegates decision-ready writes to `/author` ([audit])
- ALWAYS: `/spec` and `/author` preserve the loaded context, structure ownership, templates, durable-map voice, and downstream alignment rules across every declaration change ([audit])
- NEVER: `/author` acts as a second operator-facing specification workflow — it is an internal protocol invoked with a decision-ready artifact packet ([audit])
