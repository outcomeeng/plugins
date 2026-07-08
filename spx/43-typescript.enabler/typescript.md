# TypeScript

PROVIDES the complete TypeScript development workflow — architecture, testing, implementation, and review
SO THAT TypeScript projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality

The typescript plugin contains 9 skills following the foundational + language-specific pattern: `/typescript-standards` (reference), `/typescript-architecture-standards` (reference), `/typescript-test-standards` (reference), `/test-typescript`, `/code-typescript`, `/audit-typescript-code`, `/audit-typescript-tests`, `/architect-typescript`, `/audit-typescript-architecture`. The `typescript-simplifier` agent preloads its skill; the `audit-typescript-{code|tests|architecture}` skills carry no language-specific auditor agent and are composed by the generic artifact-type auditors. `implementation-auditor` composes the code, test, and architecture concern skills for implementation audits; `adr-auditor` and `test-evidence-auditor` compose the matching concern skills for decision and test-evidence audits, per `spx/21-spec-tree.enabler/17-audit.adr.md`.

## Assertions

### Compliance

- ALWAYS: the `audit-typescript-{code|tests|architecture}` skills carry no TypeScript-specific auditor agent and are composed by the generic artifact-type auditor for the TypeScript concerns in scope; the main conversation does not invoke them in place — the dispatched verifier's isolated context produces the verdict, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, TypeScript-specific patterns in `/test-typescript` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- ALWAYS: the TypeScript plugin's testing skills (`/typescript-test-standards`, `/test-typescript`, `/audit-typescript-tests`) teach the `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` contract: source contracts come first, test infrastructure lives at the path-mapped `@testing/` root (`@testing/harnesses/*`, `@testing/generators/*`, `@testing/fixtures/*`), generators vary, fixtures stay inert, harnesses manage resources, and audits inspect the full test-infrastructure chain ([review])
- NEVER: the TypeScript plugin's skills teach or recommend `tests/support/`, `tests/_support/`, `tests/helpers/`, `tests/fixtures/`, or any inside-`tests/` location for harnesses, generators, or fixtures ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
