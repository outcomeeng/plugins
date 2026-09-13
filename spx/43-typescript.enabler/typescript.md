# TypeScript

PROVIDES the complete TypeScript development workflow — architecture, testing, implementation, and review
SO THAT TypeScript projects using spec-tree
CAN produce implementations governed by ADRs, verified by evidence-based tests, and audited for quality

The TypeScript plugin composes foundational methodology with language-specific standards and workflows. Its `typescript-simplifier` definition invokes `/simplify-typescript` and relays its result. The `audit-typescript-{code|tests|architecture}` skills carry no language-specific auditor agent and are composed by the generic artifact-type auditors, per `spx/21-spec-tree.enabler/17-audit.adr.md`.

## Assertions

- ALWAYS: `/simplify-typescript` owns the simplification contract for changed TypeScript implementation: independently discover scope and governing evidence, preserve behavior and type safety, invoke `/code-typescript` for edits, and report changed paths and verification results. Its instructions preserve tests and evidence, block changes lacking behavioral coverage, and limit recovery to its own edits. The coding workflow requires RED evidence when behavior changes and uses unchanged passing evidence for behavior-preserving work ([audit])

### Compliance

- ALWAYS: the `audit-typescript-{code|tests|architecture}` skills carry no TypeScript-specific auditor agent, name no caller, and stay invocable on their own; an artifact-type auditor composes them for the TypeScript concerns in scope, and the author-context isolation an audit verdict requires binds the author context per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
- ALWAYS: follow the foundational + language-specific pattern — core principles in `/test`, TypeScript-specific patterns in `/test-typescript` ([audit])
- ALWAYS: the TypeScript plugin's test standards cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the language-neutral seam rules, and the `25-typescript-standards.enabler` subtree declares only the TypeScript delta ([audit])
- NEVER: the TypeScript plugin's skills teach or recommend `tests/support/`, `tests/_support/`, `tests/helpers/`, `tests/fixtures/`, or any inside-`tests/` location for harnesses, generators, or fixtures ([audit])
- NEVER: reference specs or decisions from code — no `ADR-21` or `PDR-13` in code comments or docstrings ([audit])
