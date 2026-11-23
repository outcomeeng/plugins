# Context Enumeration via the SPX CLI

CONSTRAINS the derivation of the Context Subgraph that context loading reads for a Query on a product-tree target
TO the structured output of `spx spec context show --json`, with `/contextualize` deriving the same members, views, and order from the tree itself where the consuming floor's output does not give them
SO THAT the completeness, order, and determinism of each Context Subgraph are properties of tested code wherever a published SPX release provides them

## Verification

### Audit: derivation

- cli-derivation: ALWAYS: where the consuming floor is a published SPX release whose `spx spec context show --json` output gives a target's Work Context in its Routine and its Authoring mode, each member at its view, `/contextualize` derives the Context Subgraph from that output and enumerates no member by agent-executed globbing.
- fallback-derivation: ALWAYS: where the consuming floor's `spx spec context show --json` output does not give that Work Context, `/contextualize` derives the same members, views, and order from the tree itself, and its context manifest names the fallback.
- pre-4-context: ALWAYS: where the repository declares a methodology version before 4.0, `/contextualize` loads the context that version states, the 3.x walk for a 3.2 declaration, in place of the Work Context, and its context manifest names the declared version whose context it loaded.
- citation-provenance: ALWAYS: each cross-subtree or transitive Decision Record citation enters the Context Subgraph once, at Complete, with provenance that names the citing file.
- methodology-declaration: ALWAYS: the context manifest states the methodology source and exact version from the `methodology` block of the SPX CLI's structured output, never from a plugin distribution version, a changelog, or prose.
- no-note-scan: NEVER: context loading adds a member from a reference in `PLAN.md`, `ISSUES.md`, or other note prose.

### Audit: read order

- total-order: ALWAYS: the read order is total and byte-identical for the same tree contents, target, Query, and mode, and places every member: the Product spec, then each ancestor top-down, then the target; within a level, the spec precedes its governing Decision Records, which precede its `ISSUES.md`, which precedes its lower-Index sibling specs; at the target, its lower-Index sibling specs precede its Outcome record and its Knowledge `index.md`, and in Authoring mode those precede its immediate children, which precede its same-Index and higher-Index siblings; members that share an Index follow in slug order; each cited Decision Record follows in the order of its first citation in the order so far, then each linked contract file in the order of its first link, then each pinned implementation file in path order.
- distinct-sets: ALWAYS: the active root harness instruction file, each on-path subdirectory instruction file of that harness in path order from the root, and the local overlays are enumerated as sets apart from the read order, and `spx/CLAUDE.md` and `spx/AGENTS.md` are no instruction input.
