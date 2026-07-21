# Test Data Ownership

PROVIDES ownership rules for TypeScript test values, generators, harnesses, and fixtures
SO THAT TypeScript tests
CAN distinguish source contracts from generated input domains and avoid hiding literals in test-infrastructure modules

## Assertions

### Compliance

- ALWAYS: TypeScript test-data-ownership specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the case-provenance, predicate-ownership, oracle-independence, value-ownership, generator, fixture, and semantic-binding seam rules and declare only the TypeScript delta below ([audit])
- ALWAYS: TypeScript variable input domains come from `fast-check` `fc.Arbitrary<T>` generators that vary, compose, and shrink; TypeScript source-owned values come from exported registries, enums, discriminated-union constructors, typed factories, or schemas; harnesses and inert fixtures live at the `@testing/` path-mapped home (`@testing/harnesses/*`, `@testing/fixtures/*`); and an executed test binds observations through `const`, `let`, or destructuring while owning every `expect` matcher ([audit])
- NEVER: a TypeScript generator whose only behavior is `fc.constant(...)` around a source-owned singleton, or a TypeScript constant bag named `TEST_FIXTURES`, `SAMPLE_PATHS`, `TYPICAL`, or `EDGES` standing in for source-owned values — the owning source module provides the constructor, registry, or typed factory ([audit])
