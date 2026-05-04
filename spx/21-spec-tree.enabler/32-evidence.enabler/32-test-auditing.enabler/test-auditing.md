# Test Auditing

PROVIDES an audit methodology verifying tests provide genuine evidence for spec assertions
SO THAT all spec-tree projects
CAN eliminate phantom evidence (green CI with unfulfilled assertions)

## Testability Gate

The audit begins with a precondition: **can the spec assertion be verified given the shape of the source code?** Source code that hides the assertion-relevant behavior behind opaque internals — no seams, no injection points, no observable boundaries — cannot be evidenced by any test, regardless of test quality.

When testability fails, the finding targets the source file. Remediation is "refactor production for testability." Remaining evidence checks (coupling, falsifiability, alignment, coverage) are skipped — they cannot apply to an assertion the source cannot expose.

Testability findings target source code; coupling, falsifiability, alignment, and coverage findings target the test. Without the testability gate, an audit examining untestable source code can only reject the test, which mis-attributes the defect.

## Test Evidence Model

When testability passes, the audit checks four evidence properties in order:

1. **Coupling** — the test imports and exercises code from the codebase
2. **Falsifiability** — a breaking change to the implementation causes a test failure
3. **Alignment** — the test verifies what the spec assertion claims, not something adjacent
4. **Coverage** — the test measurably increases coverage of the code under test

A test missing any property has zero evidentiary value regardless of code quality.

## Coupling Taxonomy

The `/auditing-tests` skill in the spec-tree plugin classifies test coupling into distinct categories, each with a different audit response:

| Category           | Definition                                                                                      | Verdict                                |
| ------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------------- |
| Direct             | Test imports the module under test                                                              | Proceed to falsifiability              |
| Indirect           | Test imports a harness that wraps the module                                                    | Proceed — verify harness coupling      |
| Transitive         | Test imports something that depends on the module                                               | Review — may be legitimate integration |
| Laundered indirect | Test imports a test-support module that exists only to expose hardcoded values back to the test | REJECT — laundering                    |
| False              | Test imports the module but never exercises the assertion-relevant path                         | REJECT                                 |
| Partial            | Test exercises some paths but not the ones the assertion claims                                 | REJECT                                 |
| None               | Test imports only its test framework                                                            | REJECT — tautology                     |

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

## Literal Rule

Bare literals in test code launder coupling. A test that asserts `response.status === 200` declares the rule "the system returns 200" at the test site rather than importing the rule from the system under test. When the system changes its meaning of success, the test continues passing against the laundered constant.

The literal rule applies at every audit gate where coupling is examined: testability, coupling, falsifiability, and rejection criteria.

Allowlist of bare literals that need no sourced origin:

- **Numbers**: `-1`, `0`, `1`, `2` — universal sentinels (off-by-one boundaries, empty/single/pair).
- **Strings**: `""` (empty string), and any string inside a descriptive callsite (test title, `expect` message argument, comment).

Every other literal must come from one of three sources:

- **Library or platform origin** — imported directly from the library or runtime API. Production never re-exports a library constant; tests import from the same origin production imports from.
- **Production-owned constant object** — defined in production code, used internally by production at least once, and exported. Tests import the same exported symbol.
- **Generator** — `faker`, `hypothesis`, `fast-check`, or a harness function that produces values at call time.

Static-literal fixture files are not a valid source. A fixture that exports a hardcoded string or number recreates the laundered indirect coupling pattern under a fixture name.

## Positive Pattern

The legitimate pattern: production defines a typed constant (object, dict, frozen dataclass, or platform-canonical equivalent), uses it internally at least once, and exports it. The test imports the same symbol. One definition, one point of change.

When the value originates outside the codebase — an HTTP status, a POSIX errno, a protocol opcode — both production and test import directly from the platform or library origin. Production never re-exports a library constant; tests import from where production imports from.

When the audit rejects bare literals, the verdict reports the positive pattern as the remediation. Language-specific structural rules (the constant-object syntax, the type derivation, the no-enums policy) live in `/standardizing-typescript`, `/standardizing-python`, and `/standardizing-rust`.

## Assertions

### Scenarios

- Given source code that does not expose a seam for the spec assertion, when audited, then the verdict targets the source file with finding category "untestable source" and remaining evidence checks are skipped ([test](tests/test_test_auditing.scenario.l1.py))
- Given source code that exposes a seam for the spec assertion, when audited, then testability passes and the audit proceeds to coupling ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that imports only its test framework, when audited by `/auditing-tests`, then the verdict is REJECT with finding category "no coupling" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that imports a codebase module but mocks it entirely, when audited, then the verdict is REJECT with finding category "coupling severed" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file where testability passes, the test imports the correct module, and the test verifies behavior matching the spec assertion, when audited and all four evidence properties hold, then the verdict is APPROVED ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that imports the correct module but asserts on a property unrelated to the spec assertion, when audited, then the verdict is REJECT with finding category "misaligned" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file where no mutation to the imported module would cause a failure, when audited, then the verdict is REJECT with finding category "unfalsifiable" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that produces zero coverage delta on the assertion-relevant source files, when audited, then the verdict is REJECT with finding category "no coverage increase" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file under audit, when coverage is measured with and without the test, then the auditor reports actual percentage deltas per source file, not estimates ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file with a bare numeric literal outside the allowlist `{-1, 0, 1, 2}`, when audited, then the verdict is REJECT with finding category "unsourced literal" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file with a bare string literal outside `""` and descriptive callsites, when audited, then the verdict is REJECT with finding category "unsourced literal" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that sources every non-allowlist literal from a library origin, a production-owned constant object, or a generator, when audited, then the literal rule passes ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file importing literals from a static-literal fixture file, when audited, then the verdict is REJECT with finding category "fixture laundering" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file importing literals from a test-support module that exists only to re-export hardcoded values, when audited, then the verdict is REJECT with finding category "laundered indirect" ([test](tests/test_test_auditing.scenario.l1.py))
- Given production defines and exports a typed constant used internally and the test imports the same symbol, when audited, then the literal rule passes and the verdict reports the positive pattern as the remediation reference ([test](tests/test_test_auditing.scenario.l1.py))

### Properties

- The audit methodology classifies coupling into at least the seven categories defined in the Coupling Taxonomy — distinct failure modes require distinct audit responses ([test](tests/test_test_auditing.property.l1.py))

### Conformance

- The `/auditing-tests` skill invokes `/contextualizing` on the target spec node before any audit phase ([test](tests/test_test_auditing.conformance.l1.py))

### Compliance

- ALWAYS: check testability before coupling — a test cannot evidence an assertion the source code cannot expose ([review])
- ALWAYS: target findings against the source file when testability fails — the test cannot remediate untestable source ([review])
- ALWAYS: check what the test imports from the codebase as the first audit phase after testability passes — coupling is prerequisite to all other evidence analysis ([review])
- ALWAYS: run the project's coverage command to measure actual coverage delta — read CLAUDE.md for the correct command ([review])
- ALWAYS: provide falsifiability analysis by naming concrete mutations that would break each test — "can this test fail?" is not a judgment call ([review])
- ALWAYS: apply the literal rule at testability, coupling, falsifiability, and rejection — bare literals outside `{-1, 0, 1, 2}` for numbers and `{""}` plus descriptive callsites for strings sever evidence quality regardless of test structure ([review])
- ALWAYS: report the positive pattern as the remediation when bare literals are rejected — name a library origin, a production-owned constant, or a generator that the test should import from ([review])
- NEVER: use grep patterns for mechanical detection (mocking patterns, skip patterns, type annotations) — these are static analysis concerns delegated to tooling ([review])
- NEVER: approve a test with zero codebase coupling regardless of code quality — a well-typed, well-structured tautology is still a tautology ([review])
- NEVER: estimate or reason about what code paths a test "probably" covers — run coverage and report actual numbers ([review])
- NEVER: accept static-literal fixture files as a valid origin — fixtures that export hardcoded literals recreate laundered indirect coupling under a fixture name ([review])
