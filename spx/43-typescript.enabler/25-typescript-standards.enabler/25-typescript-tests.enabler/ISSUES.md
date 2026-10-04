# Issues: TypeScript tests

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The TypeScript delta of the source-laundering rule is unauthored

`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` carries the language-neutral source-laundering rule: a case, example or expectation table placed inside a module under test so a test can cite a production path as its provenance, with ownership following consumption rather than address. `spx/43-python.enabler/25-python-standards.enabler/25-python-tests.enabler/` declares the Python discriminator. TypeScript has no delta, and `32-test-data-ownership.enabler`, where its constant-bag sibling lives, is the natural home.

The TypeScript delta is the discriminator in TypeScript terms: an export from `src/` whose only importers are `spx/**/tests/` and `testing/`, reached because a barrel re-export and an `export const` case array read as ordinary module surface. Tree-shaking removes a symbol from a bundle without making it source-owned, so bundle absence is not the discriminator; importer identity is.

**Settlement condition.** The delta is authored in `32-test-data-ownership.enabler` and its evidence exists. Nothing blocks it.

## The standards the skill teaches have no TypeScript-specific child node

`docs/cross-language-test-standards-drift-audit.md` records TypeScript test-standard follow-ups. The skill `typescript-test-standards` teaches file naming, level tooling, property-based testing and Playwright request context, and this node has children for source testability, test-data ownership, test-infrastructure auditing and execution-level guidance only. Marketplace-wide methodology restatements remain in the TypeScript-specific standards, where shared Spec Tree guidance owns them.

**Settlement condition.** `/decompose` and `/author` add TypeScript-specific child nodes for file naming, level tooling, property-based testing and Playwright request context, and the restatements either move into shared Spec Tree guidance or cite the canonical source directly. The changeset passes `spx validation markdown`, `spx spec status --format json`, `just check-skills`, `just docs-check` and `typescript:audit-typescript-tests`.

**Related.** The legacy wording audit against the vocabulary for production-grade test infrastructure under `testing/`, path-mapped to `@testing/`, folds into the same changeset.
