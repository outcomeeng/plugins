# Refactoring

PROVIDES safe tree restructuring operations that apply composition decisions from `/decomposing`
SO THAT all spec authors
CAN reorganize the spec tree without losing context, breaking references, or duplicating composition logic

## Assertions

### Scenarios

- Given a node being moved to a new parent, when refactoring runs, then cross-references in other specs are updated to reflect the new path ([test](tests/test_refactoring.unit.py))
- Given two sibling nodes sharing the same infrastructure concern, when refactoring runs, then `/decomposing` defines the shared enabler structure before refactoring applies the tree changes ([test](tests/test_refactoring.unit.py))

### Compliance

- ALWAYS: update all cross-references when moving a node — stale paths break deterministic context loading ([review])
- ALWAYS: delegate shared enabler extraction, consolidation boundaries, and new index assignment to `/decomposing` before applying tree surgery ([review])
- ALWAYS: preserve node-local `PLAN.md` and `ISSUES.md` when moving nodes — escape hatches belong to the node they describe ([review])
- ALWAYS: reference nodes, ADRs, and PDRs by full path from `spx/` in refactor plans and reports — bare names and bare decision filenames are ambiguous because numeric prefixes are sibling-local ([review])
- NEVER: change assertion semantics during a refactoring operation — refactoring moves structure, not meaning ([review])
- NEVER: choose lower-index survivors or create lower-index enablers by default — index changes come from `/decomposing` ordering evidence ([review])
