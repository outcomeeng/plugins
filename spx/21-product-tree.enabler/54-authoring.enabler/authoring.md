---
id: 01a0ebba-5f64-73f1-8795-b556d633527b
malleability: spec
---

# Authoring

PROVIDES an operator-facing specification workflow backed by a decision-ready artifact-writing protocol
SO THAT spec authors and implementation workflows
CAN change durable declarations through one context-complete boundary without duplicating placement, drafting, or validation behavior

## Assertions

- authoring-slug-grammar: `/author` opens each Assertion and decision it writes with a slug of lowercase letters, digits, and hyphens, unique within its file, never `malleability`, `path`, or `title`, and holds no opening square bracket in the Assertion text before the tags
- authoring-closing-tags: `/author` closes a Testing rule with its assertion type and an Audit rule with the bare audit tag, writes no audit tag that carries a rule slug, and states each compliance rule as an ALWAYS or NEVER rule

### Compliance

- ALWAYS: operator-driven creation, modification, or removal of durable declarations enters through `/spec`, which owns requirements convergence and delegates decision-ready writes to `/author` ([audit])
- ALWAYS: `/spec` and `/author` preserve the loaded context, structure ownership, templates, durable-map voice, and downstream alignment rules across every declaration change ([audit])
- NEVER: `/author` acts as a second operator-facing specification workflow — it is an internal protocol invoked with a decision-ready artifact packet ([audit])
