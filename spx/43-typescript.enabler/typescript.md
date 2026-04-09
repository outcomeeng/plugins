# TypeScript

PROVIDES the complete TypeScript development workflow — architecture, testing, implementation, and review
SO THAT TypeScript projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality

The typescript plugin contains 8 skills following the foundational + language-specific pattern: `/standardizing-typescript` (reference), `/standardizing-typescript-architecture` (reference), `/testing-typescript`, `/coding-typescript`, `/auditing-typescript`, `/auditing-typescript-tests`, `/architecting-typescript`, `/auditing-typescript-architecture`. Four agents (`typescript-code-auditor`, `typescript-architecture-auditor`, `typescript-test-auditor`, `typescript-simplifier`) preload the corresponding skills.

## Assertions

### Compliance

- ALWAYS: follow the foundational + language-specific pattern — core principles in `/testing`, TypeScript-specific patterns in `/testing-typescript` ([review])
- ALWAYS: use dependency injection instead of mocking — reality is the oracle ([review])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([review])
