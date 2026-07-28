# Refactoring

PROVIDES safe tree restructuring operations that apply composition decisions from `/decompose`
SO THAT all spec authors
CAN reorganize the spec tree without losing context, breaking references, or duplicating composition logic

## Assertions

### Compliance

- ALWAYS: update all cross-references when moving a node — stale paths break deterministic context loading ([audit])
- ALWAYS: delegate shared enabler extraction, consolidation boundaries, and new index assignment to `/decompose` before applying tree surgery ([audit])
- ALWAYS: preserve node-local `PLAN.md` and `ISSUES.md` when moving nodes — coordination notes belong to the node they describe ([audit])
- ALWAYS: reference nodes, ADRs, and PDRs by full path from `spx/` in refactor plans and reports — bare names and bare decision filenames are ambiguous because numeric prefixes are sibling-local ([audit])
- NEVER: change assertion semantics during a refactoring operation — refactoring moves structure, not meaning ([audit])
- NEVER: choose lower-index survivors or create lower-index enablers by default — index changes come from `/decompose` ordering evidence ([audit])
