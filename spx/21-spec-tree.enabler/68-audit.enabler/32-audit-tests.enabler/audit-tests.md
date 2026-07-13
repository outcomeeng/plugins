# Audit Tests

PROVIDES an audit methodology verifying tests provide behavior-coupled evidence for spec assertions
SO THAT all spec-tree projects
CAN eliminate phantom evidence (green CI with unfulfilled assertions)

## Testability Gate

The audit begins with a precondition: **can the spec assertion be verified given the shape of the source code?** Source code that hides the assertion-relevant behavior behind opaque internals — no seams, no injection points, no observable boundaries — cannot be evidenced by any test, regardless of test quality.

When testability fails, the finding targets the source file. Remediation is "refactor production for testability." Remaining evidence checks (coupling, falsifiability, alignment, coverage) are skipped — they cannot apply to an assertion the source cannot expose.

Testability findings target source code; coupling, falsifiability, alignment, and coverage findings target the test. Without the testability gate, an audit examining untestable source code can only reject the test, which mis-attributes the defect.

## Test Evidence Model

When testability passes, the audit reconstructs the evidence design independently before checking the four established evidence properties. The authoring packet is audit context and never proof. Reconstruction determines the assertion quantifier and domain, independent oracle, execution level, source-contract needs, harness needs, generator variation, fixture suitability and approval, replay path, and the concrete condition under which the evidence could pass while the assertion remained false.

Every local artifact reference is validated by role. A governing reference is a product-root-relative Markdown link to the exact assertion-bearing spec file or full decision path under `spx/`. A source contract, harness, generator, or fixture also links its implementation when that implementation exists, but implementation-only traceability fails. Test evidence links resolve to typed files under the governing node's `tests/`; eval links resolve to `eval.toml`; external authorities use stable canonical identifiers paired with a product-root-relative Markdown link to the local spec or full decision that adopts them; runtime seeds and run tokens remain verbatim source-emitted identities paired with product-root-relative Markdown links to the harness or run-journal implementation and its exact governing spec or full decision. Bare paths, inline-code paths, absolute paths, `file://` URIs, traversal paths, directories, and broken planned-implementation links fail validation.

The audit then checks four evidence properties in order:

1. **Coupling** — the test imports and exercises code from the codebase
2. **Falsifiability** — a breaking change to the implementation causes a test failure
3. **Alignment** — the test verifies what the spec assertion claims, not something adjacent
4. **Coverage** — the test drives execution into the assertion-relevant code path, established by reading the test against the production code, not by re-running coverage tooling

A test missing any property has zero evidentiary value regardless of code quality.

## Coupling Taxonomy

The `/audit-tests` skill in the spec-tree plugin classifies test coupling into distinct categories, each with a different audit response:

| Category           | Definition                                                                                                                                              | Verdict                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Direct             | Test imports the module under test                                                                                                                      | Proceed to falsifiability                                                               |
| Indirect           | Test imports a harness that wraps the module                                                                                                            | Proceed — verify harness coupling                                                       |
| Transitive         | Test imports something that depends on the module                                                                                                       | Review — may be legitimate cross-module evidence at L2                                  |
| Laundered indirect | Test imports a test-infrastructure module that exists only to expose hardcoded values back to the test                                                  | REJECT — laundering                                                                     |
| False              | Test imports the module but never exercises the assertion-relevant path                                                                                 | REJECT                                                                                  |
| Partial            | Test exercises some paths but not the ones the assertion claims                                                                                         | REJECT                                                                                  |
| None               | Test imports only its test framework                                                                                                                    | REJECT — tautology                                                                      |
| Severed            | Test imports the module under test and replaces the imported behavior with a mock, fake, stub, monkeypatch, or equivalent replacement                   | REJECT — coupling severed                                                               |
| Prose-coupling     | Test reads an authored prose or documentation body (skill, spec, prompt) and asserts on its content — directly or laundered through test infrastructure | REJECT — couples to authored text, not behavior; retag the assertion `[eval]`/`[audit]` |

## Falsifiability Model

For each codebase import, the auditor names a concrete mutation to the imported module that would cause the test to fail. If no such mutation exists, the test is unfalsifiable — it provides no evidence regardless of coupling.

Mocking severs coupling. A test that imports a module then replaces it with a mock is equivalent to importing nothing.

## Coverage Verification

The auditor establishes coverage by reading, never by running coverage tooling. A dispatched agentic audit runs no deterministic verification — the caller brings the project's tests and coverage gate to passing on the changeset before dispatch, and CI re-runs them over the whole repository, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` and `spx/21-spec-tree.enabler/17-audit.adr.md`. Re-running the project's coverage command inside the audit re-pays a cost already paid and is the duplication that rule prohibits.

The auditor traces, by reading, whether the test drives execution into the assertion-relevant code path:

1. Read the production code the assertion governs and identify the assertion-relevant functions, branches, and lines.
2. Read the test and follow what it calls into that production code.
3. Judge whether the test's execution reaches the assertion-relevant path — the lines whose behavior the assertion claims.

A test that imports the module but never drives execution into the assertion-relevant path provides no coverage evidence — REJECT regardless of coupling, falsifiability, and alignment. The finding names the specific assertion-relevant path the test fails to reach, traced from the code, not a measured percentage.

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

## Test File Declaration Rule

Executed test files are typed assertion files only. They do not own test data, expected outputs, runner settings, property-test configuration, setup policy, reusable cases, fixtures, generators, or harness behavior. Any variable, constant, framework fixture parameter, or property-generated parameter in a test file is evidence that the test is owning a value the evidence chain should source elsewhere. The audit records the binding before applying the literal rule, then names the proper owner: source contract, spec-governed harness, spec-governed generator, inert whole-payload fixture, or curated eval case data when generation is wasteful and not tractable.

Renaming a declaration to evade a case-based validation rule does not change ownership. A runner setting such as a property-test run count is test configuration and belongs in a harness. A boundary value or expected output belongs in a generator, source contract, or justified fixture/eval case. The test file keeps the assertion flow; infrastructure owns reusable choices.

## Positive Pattern

The legitimate pattern: production defines a typed constant (object, dict, frozen dataclass, or platform-canonical equivalent), uses it internally at least once, and exports it. The test imports the same symbol. One definition, one point of change.

When the value originates outside the codebase — an HTTP status, a POSIX errno, a protocol opcode — both production and test import directly from the platform or library origin. Production never re-exports a library constant; tests import from where production imports from.

When the audit rejects bare literals, the verdict reports the positive pattern as the remediation. Language-specific structural rules (the constant-object syntax, the type derivation, the no-enums policy) live in `/typescript-standards`, `/python-standards`, and `/rust-standards`.

## Assertions

### Scenarios

- Given evidence that cites a harness only by implementation path or prose name, when audited, then the verdict reports `missing-governing-reference` even when the implementation exists ([test](tests/test_test_auditing.scenario.l1.py))
- Given an evidence-design packet whose local references use product-root-relative Markdown links to exact role-compatible targets, including both governing spec and existing implementation for infrastructure, when audited, then reference validation passes ([test](tests/test_test_auditing.scenario.l1.py))
- Given a local reference that is prose-only, inline code, absolute, URI-shaped, traversal-shaped, directory-shaped, missing, or role-incompatible, when audited, then reference validation rejects it and reports `invalid-reference`, except an implementation-only governed artifact reports `missing-governing-reference` ([test](tests/test_test_auditing.scenario.l1.py))
- Given an open or composable input domain represented by deterministic fixture examples or a constant-only generator, when audited, then the verdict reports `insufficient-domain-variation`; fixture approval cannot upgrade finite examples into property evidence ([test](tests/test_test_auditing.scenario.l1.py))
- Given a fixture candidate that is not an inert whole-payload input or lacks scoped operator approval, when audited, then the verdict reports `fixture-not-whole-payload` or `fixture-approval-missing` as applicable ([test](tests/test_test_auditing.scenario.l1.py))
- Given a property test without a harness-owned seed, replay input, and failure diagnostics, when audited, then the verdict reports `missing-replay-harness` ([test](tests/test_test_auditing.scenario.l1.py))
- Given expected output derived from the implementation under test rather than an independent oracle, when audited, then the verdict reports `missing-independent-oracle` ([test](tests/test_test_auditing.scenario.l1.py))

- Given source code that does not expose a seam for the spec assertion, when audited, then the verdict targets the source file with finding category "untestable source" and remaining evidence checks are skipped ([test](tests/test_test_auditing.scenario.l1.py))
- Given source code that exposes a seam for the spec assertion, when audited, then testability passes and the audit proceeds to coupling ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that imports only its test framework, when audited by `/audit-tests`, then the verdict is REJECT with finding category "no coupling" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that imports a codebase module but mocks it entirely, when audited, then the verdict is REJECT with finding category "coupling severed" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file where testability passes, the test imports the correct module, and the test verifies behavior matching the spec assertion, when audited and all four evidence properties hold, then the verdict is APPROVED ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that imports the correct module but asserts on a property unrelated to the spec assertion, when audited, then the verdict is REJECT with finding category "misaligned" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file where no mutation to the imported module would cause a failure, when audited, then the verdict is REJECT with finding category "unfalsifiable" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that does not drive execution into the assertion-relevant source path, established by reading the test against the production code, when audited, then the verdict is REJECT with finding category "no coverage" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file under audit, when coverage is judged, then the auditor names the assertion-relevant code path the test drives execution into — traced by reading the test against the production code, never by running the project's coverage tooling ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file with a bare numeric literal outside the allowlist `{-1, 0, 1, 2}`, when audited, then the verdict is REJECT with finding category "unsourced literal" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file with a bare string literal outside `""` and descriptive callsites, when audited, then the verdict is REJECT with finding category "unsourced literal" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that sources every non-allowlist literal from a library origin, a production-owned constant object, or a generator, when audited, then the literal rule passes ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file importing literals from a static-literal fixture file, when audited, then the verdict is REJECT with finding category "fixture laundering" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file importing literals from a test-infrastructure module that exists only to re-export hardcoded values, when audited, then the verdict is REJECT with finding category "laundered indirect" ([test](tests/test_test_auditing.scenario.l1.py))
- Given a test file that reads an authored prose or documentation body (a skill body, a spec, a prompt) and asserts on its content, when audited by `/audit-tests`, then the verdict is REJECT with finding category "prose-coupling" ([test](tests/test_test_auditing.scenario.l1.py))
- Given an executed test file declaring any variable, constant, framework fixture parameter, or property-generated parameter, when audited by `/audit-tests`, then the verdict is REJECT with finding category "test-owned declaration" and names the proper owner for the value or configuration ([test](tests/test_test_auditing.scenario.l1.py))
- Given production defines and exports a typed constant used internally and the test imports the same symbol, when audited, then the literal rule passes and the verdict reports the positive pattern as the remediation reference ([test](tests/test_test_auditing.scenario.l1.py))

### Properties

- The audit methodology classifies coupling into at least the nine categories defined in the Coupling Taxonomy — distinct failure modes require distinct audit responses ([test](tests/test_test_auditing.property.l1.py))

### Compliance

- ALWAYS: `/audit-tests` is reached only by dispatching the `test-evidence-auditor` agent; the main conversation does not invoke `/audit-tests` in place — the agent's isolated context produces the verdict, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- ALWAYS: `/audit-tests` invokes `/contextualize` on the target spec node before any audit phase ([review])
- ALWAYS: check testability before coupling — a test cannot evidence an assertion the source code cannot expose ([review])
- ALWAYS: target findings against the source file when testability fails — the test cannot remediate untestable source ([review])
- ALWAYS: screen executed test files for test-owned declarations before the coupling check — coupling remains prerequisite to falsifiability, alignment, and coverage analysis ([review])
- ALWAYS: reconstruct the evidence design independently, validate every reference by role, and report every observable evidence-design defect class in the first verdict; the authoring packet supplies context and never supplies proof ([review])
- ALWAYS: establish coverage by reading whether the test drives execution into the assertion-relevant code path — the caller and CI own coverage measurement, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([review])
- ALWAYS: provide falsifiability analysis by naming concrete mutations that would break each test — "can this test fail?" is not a judgment call ([review])
- ALWAYS: apply the literal rule at testability, coupling, falsifiability, and rejection — bare literals outside `{-1, 0, 1, 2}` for numbers and `{""}` plus descriptive callsites for strings sever evidence quality regardless of test structure ([review])
- ALWAYS: detect every variable, constant, framework fixture parameter, and property-generated parameter in executed test files before approving evidence, reject every such binding, and name the proper owner for the value or configuration: source contract, spec-governed harness, spec-governed generator, inert whole-payload fixture, or curated eval case data when generation is wasteful and not tractable ([review])
- ALWAYS: report the positive pattern as the remediation when bare literals are rejected — name a library origin, a production-owned constant, or a generator that the test should import from ([review])
- NEVER: use grep patterns for mechanical detection (mocking patterns, skip patterns, type annotations) — these are static analysis concerns delegated to tooling ([review])
- NEVER: approve a test with zero codebase coupling regardless of code quality — a well-typed, well-structured tautology is still a tautology ([review])
- NEVER: run the project's coverage command, test command, or any other deterministic verification inside the audit — re-running what the caller passed before dispatch is the duplication prohibited by `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` and `spx/21-spec-tree.enabler/17-audit.adr.md`; trace the exercised path by reading instead ([review])
- NEVER: accept static-literal fixture files as a valid origin — fixtures that export hardcoded literals recreate laundered indirect coupling under a fixture name ([review])
