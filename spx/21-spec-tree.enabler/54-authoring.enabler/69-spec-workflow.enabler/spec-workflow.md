# Spec Workflow

PROVIDES an operator-driven `/spec` lifecycle for creating and modifying durable declarations whose ownership is unambiguous
SO THAT product operators
CAN move from intent to aligned Spec Tree truth through one interactive, context-complete workflow

## Assertions

### Compliance

- ALWAYS: `/spec` invokes `/understand`, resolves the affected tree area, and invokes `/contextualize` before proposing or mutating a declaration ([audit])
- ALWAYS: `/spec` researches existing declarations and implementation before invoking `/interview`, asks only unsettled operator-owned questions, and produces a decision-ready artifact packet before invoking `/author` ([audit])
- ALWAYS: `/spec` stops before mutation when node boundaries, ordering, indices, shared enablers, decision ownership, moving, or re-scoping remain unsettled, and returns the exact `/decompose` or `/refactor` handoff required to continue ([audit])
- ALWAYS: `/spec` invokes `/align` after changing a product spec, decision record, or ancestor assertion, aligns the first affected lower declarations in the same change, and records remaining delivery work in the first affected node's `PLAN.md` ([audit])
- ALWAYS: `/spec` presents the resulting declaration paths, validation state, unresolved decisions, and next executable handoff to `/slice` or `/apply` ([audit])
- NEVER: `/spec` selects an assertion's verification type or assertion type governed by the inline `/understand` `<assertion_model>` → `<verification_selection>`, writes tests or implementation, or treats implementation structure as the durable-map structure declared in `<truth_hierarchy>` ([audit])
