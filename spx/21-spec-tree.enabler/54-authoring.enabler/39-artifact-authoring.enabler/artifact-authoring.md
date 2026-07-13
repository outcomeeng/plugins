# Artifact Authoring

PROVIDES deterministic creation and modification of decision-ready Spec Tree artifacts
SO THAT specification, decomposition, refactoring, and implementation workflows
CAN persist declarations without duplicating template, placement, voice, reference, or validation rules

## Assertions

### Compliance

- ALWAYS: `/author` is hidden from operator autocomplete while remaining model-invocable by parent workflows ([audit])
- ALWAYS: `/author` accepts a decision-ready artifact packet containing the operation, artifact type, full target path, loaded context target, settled content, and any structure decision that governs placement ([audit])
- ALWAYS: `/author` reads the appropriate foundation template before writing and validates artifact structure, atemporal voice, full-path references, content placement, and node-type constraints after writing ([audit])
- ALWAYS: outcome-node writes preserve the three-part output, outcome, and impact hypothesis ([audit])
- ALWAYS: create operations require a collision-free path and index already settled by loaded context or `/decompose`; update operations require an existing full artifact path ([audit])
- ALWAYS: `/author` returns the changed artifact paths and validation result to its calling workflow so that the caller can perform downstream alignment and delivery ([audit])
- NEVER: `/author` interviews the operator, chooses product scope, resolves structure, assigns evidence types, writes tests or implementation, or initiates delivery ([audit])
- NEVER: `/author` accepts proposed sibling sets or dependency order as authority when `/decompose` has not settled the structure ([audit])
