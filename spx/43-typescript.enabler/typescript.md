# TypeScript

PROVIDES the complete TypeScript development workflow — architecture, testing, implementation, and review
SO THAT TypeScript projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality

The typescript plugin contains 9 skills following the foundational + language-specific pattern: `/typescript-standards` (reference), `/typescript-architecture-standards` (reference), `/typescript-test-standards` (reference), `/test-typescript`, `/code-typescript`, `/audit-typescript`, `/audit-typescript-tests`, `/architect-typescript`, `/audit-typescript-architecture`. Four agents (`typescript-code-auditor`, `typescript-architecture-auditor`, `typescript-test-auditor`, `typescript-simplifier`) preload the corresponding skills.

## Assertions

### Compliance

- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, TypeScript-specific patterns in `/test-typescript` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- ALWAYS: the TypeScript plugin's testing skills (`/typescript-test-standards`, `/test-typescript`, `/audit-typescript-tests`) teach the `spx/15-test-infrastructure.pdr.md` contract: source contracts come first, test infrastructure lives at the path-mapped `@testing/` root (`@testing/harnesses/*`, `@testing/generators/*`, `@testing/fixtures/*`), generators vary, fixtures stay inert, harnesses manage resources, and audits inspect the full test-infrastructure chain ([review])
- NEVER: the TypeScript plugin's skills teach or recommend `tests/support/`, `tests/_support/`, `tests/helpers/`, `tests/fixtures/`, or any inside-`tests/` location for harnesses, generators, or fixtures ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
