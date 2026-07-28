# Python Standards

PROVIDES Python-specific architecture, test, and code standards grouped under a single parent enabler
SO THAT downstream Python skills, auditors, and consumers
CAN read one cohesive standards subtree rather than independent guidance branches

The three children of this enabler — `21-python-architecture.enabler` (ADR conventions and dependency-injection patterns), `25-python-tests.enabler` (test data ownership, source testability, test-infrastructure auditing, execution-level guidance), `29-python-code.enabler` (implementation and remediation workflows) — partition the Python-standards concern by axis.

## Assertions

### Compliance

- ALWAYS: the three child enablers cover non-overlapping facets of Python standards: architecture decisions, test evidence rules, and code workflow rules — facet overlap forces standards to drift between sibling specs ([audit])
- ALWAYS: Python-specific standards live here, while marketplace-wide methodology (atemporal voice, ADR section structure, evidence mechanisms, and test-infrastructure semantics) lives at the spec-tree root or in cross-language decision records — duplication would force language-specific specs to restate methodology ([audit])
- NEVER: place execution-lane or methodology rules under this enabler — those are governed by product-level decisions and spec-tree methodology references; this enabler scopes only Python-specific concerns ([audit])
