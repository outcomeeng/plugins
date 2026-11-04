---
id: 01a0ebba-5f65-7730-9254-ec88ba8d41af
malleability: spec
---

# Refactoring

PROVIDES safe tree restructuring operations that apply composition decisions from `/decompose`
SO THAT all spec authors
CAN reorganize the Product Tree without losing context, breaking references, or duplicating composition logic

## Assertions

- ALWAYS: load context through `/contextualize` for every node an operation touches, the parent that gains or loses a child included, before reading or moving any file; a live context marker for each exact path is the input of impact analysis
- ALWAYS: run the product's verify command for the spec lane after a move, re-scope, extraction, or consolidation, and stop on a nonzero exit before reporting a restructured tree

### Compliance

- ALWAYS: update all cross-references when moving a node — stale paths break deterministic context loading ([audit])
- ALWAYS: delegate shared enabler extraction, consolidation boundaries, and new index assignment to `/decompose` before applying tree surgery ([audit])
- ALWAYS: preserve node-local `PLAN.md` and `ISSUES.md` when moving nodes — coordination notes belong to the node they describe ([audit])
- ALWAYS: reference nodes, ADRs, and PDRs by full path from `spx/` in refactor plans and reports — bare names and bare decision filenames are ambiguous because numeric prefixes are sibling-local ([audit])
- NEVER: change assertion semantics during a refactoring operation — refactoring moves structure, not meaning ([audit])
- NEVER: choose lower-index survivors, create lower-index enablers, or move a node to a new parent or index by default — an index change is read from the matrix file `/decompose` wrote for the target parent, and a move with no such file does not run ([audit])
