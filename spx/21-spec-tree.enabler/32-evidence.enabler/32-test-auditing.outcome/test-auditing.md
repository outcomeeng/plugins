# Test Auditing

WE BELIEVE THAT an audit methodology verifying tests provide genuine evidence for spec assertions
WILL eliminate phantom evidence (green CI with unfulfilled assertions) across all spec-tree projects
CONTRIBUTING TO reduced rework and higher confidence in spec-driven development

## Test Evidence Model

The audit answers one question: **does this test provide evidence that the spec assertion is fulfilled?**

Evidence requires four properties:

1. **Coupling** — the test imports and exercises code from the codebase
2. **Falsifiability** — a breaking change to the implementation causes a test failure
3. **Alignment** — the test verifies what the spec assertion claims, not something adjacent
4. **Coverage** — the test measurably increases coverage of the code under test

A test missing any property has zero evidentiary value regardless of code quality.

## Coupling Taxonomy

The `/auditing-tests` skill in the spec-tree plugin classifies test coupling into distinct categories, each with a different audit response:

| Category   | Definition                                                              | Verdict                                |
| ---------- | ----------------------------------------------------------------------- | -------------------------------------- |
| Direct     | Test imports the module under test                                      | Proceed to falsifiability              |
| Indirect   | Test imports a harness that wraps the module                            | Proceed — verify harness coupling      |
| Transitive | Test imports something that depends on the module                       | Review — may be legitimate integration |
| False      | Test imports the module but never exercises the assertion-relevant path | REJECT                                 |
| Partial    | Test exercises some paths but not the ones the assertion claims         | REJECT                                 |
| None       | Test imports only its test framework                                    | REJECT — tautology                     |

## Falsifiability Model

For each codebase import, the auditor names a concrete mutation to the imported module that would cause the test to fail. If no such mutation exists, the test is unfalsifiable — it provides no evidence regardless of coupling.

Mocking severs coupling. A test that imports a module then replaces it with a mock is equivalent to importing nothing.

## Coverage Verification

The auditor does not guess what code paths a test exercises.

1. Read the project's CLAUDE.md for the test and coverage command (e.g., `just run test`, `pnpm vitest --coverage`)
2. Run coverage **without** the test file under audit — this is the baseline
3. Run coverage **with** the test file under audit
4. Compare: if coverage of the assertion-relevant source files did not increase, the test provides no new evidence

The auditor reports actual numbers, not estimates:

```text
Baseline: src/tokens.ts — 43.2% (without test under audit)
With test: src/tokens.ts — 67.8% (with test under audit)
Delta: +24.6% — test provides new coverage
```

A test that produces zero coverage delta on the files it claims to verify is REJECT regardless of coupling, falsifiability, and alignment.

## Assertions

### Scenarios

- Given a test file that imports only its test framework, when audited by `/auditing-tests`, then the verdict is REJECT with finding category "no coupling" ([test](tests/test-auditing.unit.test.ts))
- Given a test file that imports a codebase module but mocks it entirely, when audited, then the verdict is REJECT with finding category "coupling severed" ([test](tests/test-auditing.unit.test.ts))
- Given a test file that imports the correct module and verifies behavior matching the spec assertion, when audited and all properties hold, then the verdict is APPROVED ([test](tests/test-auditing.unit.test.ts))
- Given a test file that imports the correct module but asserts on a property unrelated to the spec assertion, when audited, then the verdict is REJECT with finding category "misaligned" ([test](tests/test-auditing.unit.test.ts))
- Given a test file where no mutation to the imported module would cause a failure, when audited, then the verdict is REJECT with finding category "unfalsifiable" ([test](tests/test-auditing.unit.test.ts))
- Given a test file that produces zero coverage delta on the assertion-relevant source files, when audited, then the verdict is REJECT with finding category "no coverage increase" ([test](tests/test-auditing.unit.test.ts))
- Given a test file under audit, when coverage is measured with and without the test, then the auditor reports actual percentage deltas per source file, not estimates ([test](tests/test-auditing.unit.test.ts))

### Properties

- The audit methodology classifies coupling into at least the six categories defined in the Coupling Taxonomy — distinct failure modes require distinct audit responses ([test](tests/test-auditing.unit.test.ts))

### Conformance

- The `/auditing-tests` skill invokes `/contextualizing` on the target spec node before any audit phase ([test](tests/test-auditing.unit.test.ts))

### Compliance

- ALWAYS: check what the test imports from the codebase as the first audit phase — coupling is prerequisite to all other analysis ([review])
- ALWAYS: run the project's coverage command to measure actual coverage delta — read CLAUDE.md for the correct command ([review])
- ALWAYS: provide falsifiability analysis by naming concrete mutations that would break each test — "can this test fail?" is not a judgment call ([review])
- NEVER: use grep patterns for mechanical detection (mocking patterns, skip patterns, type annotations) — these are static analysis concerns delegated to tooling ([review])
- NEVER: approve a test with zero codebase coupling regardless of code quality — a well-typed, well-structured tautology is still a tautology ([review])
- NEVER: estimate or reason about what code paths a test "probably" covers — run coverage and report actual numbers ([review])
