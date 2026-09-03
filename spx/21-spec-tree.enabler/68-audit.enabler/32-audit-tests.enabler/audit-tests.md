# Audit Tests

PROVIDES an audit methodology verifying tests provide behavior-coupled evidence for spec assertions
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
4. **Coverage** — the test drives execution into the assertion-relevant code path, established by reading the test against the production code, not by re-running coverage tooling

A test missing any property has zero evidentiary value regardless of code quality.

## Coupling Taxonomy

The `/audit-tests` skill loads the same test-evidence standards as `/test`, then classifies test coupling into distinct categories, each with a different audit response:

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

The rule governs values production owns. It never governs a case the assertion's own type assigns elsewhere, and the shared test-evidence standard's assertion-type litmus is what assigns it: a scenario's case is the interaction the spec declares, transcribed into the test; a conformance expectation comes from the external oracle; a compliance case is the violating input the governing rule names. A literal arriving from one of those three sources is correct where it sits, and moving it into a production module to satisfy this rule is source laundering.

## Test Predicate and Binding Rule

Executed test files are typed assertion files whose functions or callbacks own every behavioral predicate and assertion API call. Harnesses, generators, fixtures, and controlled collaborators expose observations, generated values, or resource handles; they never accept expected outcomes, return pass/fail verdicts, call assertion APIs, or expose verdict-shaped helpers.

Bindings are classified by semantic choice. A binding that only receives or renames an imported source contract, generated value, harness observation, callback input, or fixture-path handle is valid when it introduces no data or policy. A binding that chooses a case, expected output, runner setting, seed, retry policy, setup policy, fixture payload, generator domain, or verdict rule is rejected and routed to its proper owner. Renaming never changes ownership.

## Positive Pattern

The legitimate pattern: production defines a typed constant (object, dict, frozen dataclass, or platform-canonical equivalent), uses it internally at least once, and exports it. The test imports the same symbol. One definition, one point of change.

When the value originates outside the codebase — an HTTP status, a POSIX errno, a protocol opcode — both production and test import directly from the platform or library origin. Production never re-exports a library constant; tests import from where production imports from.

When the audit rejects bare literals, the verdict reports the positive pattern as the remediation. Language-specific structural rules (the constant-object syntax, the type derivation, the no-enums policy) live in `/typescript-standards`, `/python-standards`, and `/rust-standards`.

## Assertions

### Compliance

- ALWAYS: given successful required language-concern composition, the language-neutral `/audit-tests` methodology inspects every artifact in a non-Python evidence chain before approval, rejects unsourced protocol vocabulary in imported test infrastructure, and identifies the transitive artifact and required ownership target in its structured verdict ([eval](evals/full-chain-ownership/eval.toml))
- ALWAYS: the Codex runtime rendering of `/audit-tests` satisfies the same non-Python full-chain ownership verdict contract as the shared authored skill ([eval](evals/full-chain-ownership-codex/eval.toml))
- ALWAYS: `/audit-tests` names no caller and stays invocable on its own; the author context produces a verdict by dispatching the audit to a separate verifier context rather than grading its own work in place, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
- ALWAYS: `/audit-tests` invokes `/contextualize` on the target spec node before any audit phase ([audit])
- ALWAYS: when the audit inputs carry no language partition, `/audit-tests` derives one for every test-file extension an installed language plugin's test standards declare, and rejects with `unsupported-language` and remediation target `language-partition` only an extension no installed plugin claims ([audit])
- ALWAYS: check testability before coupling — a test cannot evidence an assertion the source code cannot expose ([audit])
- ALWAYS: target findings against the source file when testability fails — the test cannot remediate untestable source ([audit])
- ALWAYS: screen executed test files for test-owned declarations before the coupling check — coupling remains prerequisite to falsifiability, alignment, and coverage analysis ([audit])
- ALWAYS: load and apply the same shared test-evidence standard used by `/test` before judging predicate ownership, semantic bindings, assertion-type case provenance, or oracle independence ([audit])
- ALWAYS: require every behavioral predicate and assertion API call to remain lexically in the linked executed test function or callback; reject verdict logic in harnesses, generators, fixtures, controlled implementations, and recording collaborators ([audit])
- ALWAYS: establish coverage by reading whether the test drives execution into the assertion-relevant code path — the caller and CI own coverage measurement, per `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
- ALWAYS: provide falsifiability analysis by naming concrete mutations that would break each test — "can this test fail?" is not a judgment call ([audit])
- ALWAYS: apply the literal rule at testability, coupling, falsifiability, and rejection — a literal standing in for a value production owns severs evidence quality regardless of test structure, outside `{-1, 0, 1, 2}` for numbers and `{""}` plus descriptive callsites for strings ([audit])
- ALWAYS: resolve a literal that the assertion type assigns to the test — a spec-declared scenario case, an external conformance expectation, or the violating input a compliance rule names — through the assertion-type litmus before the literal rule, so the audit never demands that such a case be moved into a production module ([audit])
- ALWAYS: judge a source symbol the test cites by declared-contract ownership, inspecting the declared surfaces the checkout carries — packaging entry points and export declarations, plugin and protocol implementations, registry and reflective lookups, generated use, and declared schemas — before reporting it as laundered, so an absent in-repository caller opens the ownership question rather than settling it while the bare possibility of a consumer outside the checkout never withholds a supported finding ([audit])
- ALWAYS: classify every test-file binding by what it chooses; permit observation and handle aliases that introduce no data or policy, reject bindings that choose data, expectations, configuration, setup policy, or verdict rules, and name the proper semantic owner ([audit])
- ALWAYS: apply assertion-type litmus questions to scenario, mapping, property, conformance, and compliance cases, including whether the case source and oracle are independent of the implementation author and production path under test ([audit])
- ALWAYS: report the positive pattern as the remediation when bare literals are rejected — name a library origin, a production-owned constant, or a generator that the test should import from ([audit])
- NEVER: use grep patterns for mechanical detection (mocking patterns, skip patterns, type annotations) — these are static analysis concerns delegated to tooling ([audit])
- NEVER: approve a test with zero codebase coupling regardless of code quality — a well-typed, well-structured tautology is still a tautology ([audit])
- NEVER: run the project's coverage command, test command, or any other deterministic verification inside the audit — re-running what the caller passed before dispatch is the duplication prohibited by `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` and `spx/21-spec-tree.enabler/17-audit.adr.md`; trace the exercised path by reading instead ([audit])
- NEVER: accept static-literal fixture files as a valid origin — fixtures that export hardcoded literals recreate laundered indirect coupling under a fixture name ([audit])
