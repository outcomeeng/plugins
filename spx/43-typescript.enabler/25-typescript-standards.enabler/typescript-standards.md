# TypeScript Standards

PROVIDES TypeScript-specific architecture, test, and code standards grouped under a single parent enabler
SO THAT downstream TypeScript skills, auditors, and consumers
CAN read one cohesive standards subtree rather than three independent enabler branches

The three children of this enabler — `21-typescript-architecture.enabler` (ADR conventions and DI patterns), `25-typescript-tests.enabler` (test data ownership, source testability, test-infrastructure auditing, execution-level guidance), `29-typescript-code.enabler` (code-style standards) — partition the TypeScript-standards concern by axis.

## Assertions

### Compliance

- ALWAYS: the three child enablers cover non-overlapping facets of TypeScript standards: architecture decisions, test evidence rules, and code-style rules — facet overlap forces standards to drift between sibling specs ([review])
- ALWAYS: TypeScript-specific standards live here, while marketplace-wide methodology (atemporal voice, ADR section structure, evidence mechanisms) lives at the spec-tree root or under `spx/21-spec-tree.enabler/` — duplication would force language-specific specs to restate the methodology ([review])
- NEVER: place execution-lane or methodology rules under this enabler — those are governed by `spx/16-evidence-execution-lanes.adr.md` and the spec-tree methodology references; this enabler scopes only TypeScript-specific concerns ([review])
