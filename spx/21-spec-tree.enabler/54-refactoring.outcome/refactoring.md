# Refactoring

WE BELIEVE THAT safe tree restructuring operations (move, re-scope, extract, consolidate)
WILL keep the spec tree organized as the product evolves without losing context or breaking references
CONTRIBUTING TO sustained navigability and reduced spec discovery friction

The `/refactoring` skill handles node moves between parents, assertion re-scoping across nodes, shared enabler extraction, and duplicate consolidation.

## Assertions

### Scenarios

- Given a node being moved to a new parent, when refactoring runs, then cross-references in other specs are updated to reflect the new path ([test](tests/test_refactoring.unit.py))
- Given two sibling nodes sharing the same infrastructure concern, when refactoring runs, then the shared concern is extracted into a lower-index enabler ([test](tests/test_refactoring.unit.py))

### Compliance

- ALWAYS: update all cross-references when moving a node — stale paths break deterministic context loading ([review])
- NEVER: change assertion semantics during a refactoring operation — refactoring moves structure, not meaning ([review])
