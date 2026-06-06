# Test Infrastructure

## Purpose

This decision governs what every product built on the Spec Tree methodology observably presents for test infrastructure: where harnesses, generators, and inert fixtures live; what each category means; how tests stay coupled to source behavior; and how audits inspect the full evidence chain. Methodology users — developers and agents building products against this methodology — see this as a guarantee about the product surface: every spec tree exposes the same canonical subtree, every language has a predictable implementation home, and every test-infrastructure artifact is governed as production code.

## Context

**Business impact:** Methodology users decide where to put a harness, generator, or fixture every time they extend their product. If the methodology leaves placement, ownership, or artifact semantics to local convention, every product invents its own answer, audits cannot detect drift, and skill-driven workflows generate contradictory guidance across languages. A single canonical answer turns the decision into a lookup and gives audits the authority to reject literal laundering, severed coupling, and helper directories masquerading as evidence.

**Technical constraints:**

- The canonical filename model `<subject>.<evidence>.<level>[.<runner>]` declares one evidence type per test file. The contents of `spx/<node>/tests/` are typed assertion files. Harnesses, generators, and inert fixtures have no assertions of their own inside `tests/` — they enable assertions and therefore live elsewhere.
- Test infrastructure is production code for the methodology: it implements behavior, exposes interfaces that tests depend on, and can invalidate downstream evidence when it drifts. It differs from product code only in purpose: it enables test assertions instead of shipping product behavior.
- Methodology users are language-diverse. The same product guarantee holds for TypeScript, Python, Rust, and additional language plugins; per-language paths and examples are predictable from each language's package conventions.
- Literal laundering moves easily from a test file into a generator, harness, fixture, or shared constant module. Audits therefore treat the complete imported test-infrastructure chain as part of the evidence, not as trusted scaffolding.
- Source code under test owns its protocol values, registries, constructors, schemas, and observable contracts. A test that cannot consume those contracts exposes a source-testability gap; test infrastructure does not repair that gap by copying values.

## Decision

Every spec tree governed by this methodology presents a canonical test-infrastructure subtree at the top level. Methodology users observe and rely on this shape:

- A top-level enabler with slug `infrastructure`.
- Under it, an enabler with slug `testing`.
- Under that, exactly three enabler children with slugs `generators`, `fixtures`, `harnesses`.

The slugs are normative. The methodology uses the term **infrastructure** for this testing category. The terms "support", "helpers", "utilities", and "tools" are not category names for test infrastructure.

Test-infrastructure implementations live outside `spx/` and outside any `tests/` directory, in a home the build keeps off the product's shipped artifacts. Each language realizes that separation idiomatically: a sibling directory or package for TypeScript and Python, a separate workspace-member crate for Rust, and for Go a module-private `internal/` package — Go restricts `internal/` to importers within the same module, and importing it only from `_test.go` files keeps the toolchain from compiling it into any shipped binary. The per-language path methodology users can expect:

| Language       | Product code                                | Test-infrastructure home                                                                                                                                                                                                                                                                        |
| -------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TypeScript** | `src/` or product root                      | `testing/` at product root, path-mapped to `@testing/`: `@testing/harnesses/*`, `@testing/generators/*`, `@testing/fixtures/*`                                                                                                                                                                  |
| **Python**     | `<package>/`                                | `<package>_testing/`: `<package>_testing/harnesses/`, `<package>_testing/generators/`, `<package>_testing/fixtures/`. `<package>` is the product's importable Python package name declared by its packaging metadata; illustrative example: `outcomeeng/` paired with `outcomeeng_testing/`     |
| **Rust**       | `src/` of the product crate                 | A separate workspace-member crate at `<product>-testing/` (Cargo package `<product>-testing`, Rust import path `<product>_testing`), declared as a dev-dependency of consumers; modules `<product>_testing::harnesses::*`, `<product>_testing::generators::*`, `<product>_testing::fixtures::*` |
| **Go**         | Module packages (root, `internal/`, `cmd/`) | `internal/testinfra/` (package `testinfra` — not `testing`, which collides with the standard library): `internal/testinfra/harnesses/`, `internal/testinfra/generators/`, `internal/testinfra/fixtures/`, imported as `<module>/internal/testinfra/...`                                         |

Each language plugin declares its normative path in this table or in a PDR amendment that extends this table. Language ADRs govern implementation mechanics such as `tsconfig` path mapping, Python package discovery, Cargo workspace configuration, or Go module and `internal/` placement.

### Category Semantics

**Source contracts come first.** Source modules expose the domain contracts tests need: protocol values, command names, status values, rule identifiers, message identifiers, schemas, registries, constructors, typed factories, or other observable source-owned APIs. When a test for existing behavior can only pass by copying source literals, pinning arbitrary example objects, mocking away the behavior under test, or hiding values in test infrastructure, the source code under test is improved first.

**Harnesses manage context and resources.** A harness mediates access to real behavior or real local/remote infrastructure. It owns setup, teardown, lifecycle, cleanup, mandatory dependency checks, and diagnostics for resources such as temporary filesystems, browsers, product binaries, local services, APIs, databases, Docker containers, and remote credentialed endpoints. It does not own arbitrary domain data and does not replace the behavior an assertion claims to verify.

Language skills may teach these examples:

| Language       | Acceptable harness shape                                                                                                                                                                 | Rejected shape                                                                                                                  |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **TypeScript** | `withTestEnv(...)`, `withTempDir(...)`, or a typed factory such as `createPostgresHarness()` that creates resources, passes a typed handle to the test, and cleans up on every exit path | A module that exports `TYPICAL_CASES`, stubs the module under test with `vi.mock(...)`, or hides protocol values in setup       |
| **Python**     | A context manager, pytest fixture, or factory that creates a `TemporaryDirectory`, starts a local service, yields a typed handle, and performs cleanup in `finally`                      | A fixture module that stores expected strings, copies production constants, or monkeypatches away the behavior under test       |
| **Rust**       | A RAII guard or factory that creates a `tempfile::TempDir`, starts a local process, returns a typed handle, and releases resources through `Drop` or explicit teardown                   | A testing crate module that exports static example cases, expected outputs, or fake implementations for the behavior under test |

**Generators produce variable input domains.** A generator represents a domain with meaningful variation, composition, shrinking, or systematic exploration. It is appropriate for paths, names, identifiers, content, syntax trees, option sets, structured request shapes, and other inputs where evidence improves because the test searches a space rather than naming one example.

Language skills may teach these examples:

| Language       | Acceptable generator shape                                                                                                       | Rejected shape                                                                                                   |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **TypeScript** | `fast-check` `fc.Arbitrary<T>` values that vary and shrink, including boundary branches that come from source-owned constructors | `fc.constant(...)` around a source-owned singleton shape or `fc.oneof(...)` over two hand-picked copied literals |
| **Python**     | Hypothesis strategies that compose meaningful values and shrink counterexamples                                                  | `st.just(...)` around a source-owned singleton shape or a strategy module that only renames constants            |
| **Rust**       | `proptest` strategies that explore a type/value space and shrink counterexamples                                                 | `Just(...)` around a source-owned singleton shape or a strategy containing only hand-picked copied literals      |

A constant branch inside a larger generator is valid only when it expands boundary coverage and any source-owned value still comes from the owning source module. A generator whose whole behavior is a constant source-owned singleton is not a generator; the owning source module provides the constructor, registry, or typed factory.

**Fixtures are inert whole-payload inputs.** A fixture is a real input artifact whose complete shape matters to the behavior under test: a document, captured payload, recorded transcript, source file for a parser/linter/scanner, binary sample, serialized request, or directory tree. Executed tests read fixtures from disk, copy them into temporary products, or pass fixture paths to the code or tool under test. Executed tests do not import fixtures as modules, require them as dependencies, or consume fixture exports.

Language skills may teach these examples:

| Language       | Acceptable fixture use                                                                                                 | Rejected fixture use                                                             |
| -------------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **TypeScript** | A `.ts` file under `testing/fixtures/` passed by path to ESLint, TypeScript, a parser, a scanner, or a pre-commit tool | `import { VALID_CASES } from "@testing/fixtures/rule-cases"` in an executed test |
| **Python**     | A `.py`, `.json`, `.yaml`, or directory fixture read by path, copied into `tmp_path`, or passed to a validator         | `from package_testing.fixtures.cases import EXPECTED_VALUES` in an executed test |
| **Rust**       | A `.rs`, `.toml`, `.json`, or directory fixture copied into a `tempfile::TempDir` or passed as a path to a parser/tool | `use product_testing::fixtures::VALID_CASES;` from executed test code            |

Strings and numbers are never valid fixtures by themselves. Protocol tokens, status values, command names, rule identifiers, message identifiers, expected outputs, and edge-case sets come from source-owned contracts or generators, not from fixture files.

### Evidence Chain

Evidence includes the full chain from a spec assertion to the executed test file and every imported test-infrastructure artifact. A test audit opens imported harnesses, generators, and fixture references before approving the assertion. Findings name the exact artifact and the evidence property affected: source ownership, coupling, falsifiability, domain variation, oracle independence, cleanup safety, or coverage.

Test infrastructure cannot make a weaker evidence shape impersonate a stronger one:

- A Property assertion requires a generator or source-owned enumerable domain with meaningful variation; property-framework syntax around one example is scenario evidence.
- A Mapping assertion requires a finite source-owned mapping or a generated finite domain with independently derived expectations; a copied expected-output table is a tautology.
- A Scenario assertion requires a behavior-relevant case whose inputs and expected outputs are owned by source contracts, generated domains, or whole-payload fixtures; arbitrary example bags do not establish domain truth.
- A Compliance assertion with `[test]` evidence exercises a real violating case or rule oracle; a passing-only example does not prove enforcement.

### Spec Traceability

The three category nodes `generators`, `fixtures`, and `harnesses` are mandatory. They govern category-wide rules even before a product has many artifacts. A test-infrastructure artifact is traceable to the spec tree in one of two ways:

- The artifact is covered by the category node's assertions because it only participates in that category's standard contract.
- The artifact exposes behavior, policy, lifecycle, or reusable semantics that materially affect evidence; it has a child spec under the relevant category node or is named by an assertion there.

Methodology users can derive the governing node from an artifact path and can derive the artifact category from the governing node.

## Rationale

Methodology users rely on four predictable properties: where to find a harness, generator, or fixture; what category of artifact it is; who owns the values it carries; and how audits judge the evidence chain. The decision gives each property a single answer that holds across products and languages.

**Why a separate home, not inside `tests/`.** Putting harnesses, generators, or fixtures in `tests/support/`, `tests/_support/`, `tests/helpers/`, `tests/fixtures/`, `conftest.py` as a helper home, or equivalent inside-test paths mixes production-grade test infrastructure into a directory whose canonical filename model declares typed assertion files only. Methodology users lose the per-file evidence guarantee, and audit findings can no longer distinguish an assertion from scaffolding that changes the assertion's meaning.

**Why a home the build excludes, not the product ship path.** Putting test infrastructure on the product's shipped build path — `src/testing/`, `product/testing/`, or similar in languages that compile every reachable module into the artifact — makes bundle minimization, dead-code analysis, packaging, dependency audits, and public API review conflate product behavior with test-enabling behavior. The separation is realized per language: a sibling directory or package for TypeScript and Python, a separate workspace-member crate for Rust, and for Go a module-private `internal/` package — Go restricts `internal/` to importers within the same module, and importing it only from `_test.go` files keeps the toolchain from compiling it into any shipped binary.

**Why source contracts come first.** Copying protocol values into tests or infrastructure decouples evidence from the code under test. If a status value, command name, diagnostic code, registry member, schema, or constructor belongs to source behavior, source exports it through a semantically named API. Tests import that API. When the API does not exist, the source shape changes before the test is accepted.

**Why generators must vary.** A property test or generated scenario earns evidence value by searching an input space, shrinking counterexamples, and composing valid domain values. A constant-only generator hides a named constant behind a framework call and makes review harder without adding evidence. Source-owned singleton shapes are source contracts, not generated domains.

**Why fixtures stay inert.** Whole-payload fixtures are useful because their complete shape exercises parsers, linters, scanners, validators, file walkers, and external contracts. Imported fixture modules are different: they execute as test dependencies and export test-owned values. That turns fixtures into shared constant bags and hides the evidence boundary.

**Why harnesses manage resources, not truth.** A harness removes repetition around lifecycle and external systems. It must not own domain truth or replace the behavior under test. A context manager, RAII guard, or typed factory that cleans up resources increases evidence quality; a harness that mocks the asserted behavior or stores expected outputs severs evidence.

**Why audits traverse the chain.** A test file can look clean while the defect lives in `@testing/generators/*`, `<package>_testing/fixtures/*`, or `<product>_testing::harnesses::*`. Full-chain inspection is the only way to reject literal laundering and coupling camouflage reliably.

## Trade-offs accepted

| Trade-off                                                                        | Mitigation / reasoning                                                                                                                                                                            |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Methodology users remember a different implementation path per language          | Each language's testing and auditing skills document the path and examples for that language; the category subtree and artifact semantics remain identical across languages.                      |
| Products with inside-`tests/` helper directories or fixture modules move files   | The move preserves behavior while restoring the evidence boundary: assertion files stay in `spx/<node>/tests/`, and test infrastructure moves to the language's normative home.                   |
| The methodology mandates artifact semantics, not only paths                      | Audits can reject laundering even when files sit in the right directory; correct placement alone does not make a generator variable, a fixture inert, or a harness coupled to source behavior.    |
| Source modules may need architecture changes before tests become acceptable      | This is the intended forcing function. Tests that require copied source literals or replacement mocks expose missing source contracts; improving source testability produces better product APIs. |
| Rust workspace-member test infrastructure requires Cargo workspace configuration | Rust products pay the setup cost once and gain a package boundary that keeps product crates from importing test infrastructure as shipping code.                                                  |

## Product invariants

- For every product governed by this methodology, a canonical spec subtree exists at `<root>/<NN>-infrastructure.enabler/<NN>-testing.enabler/<NN>-{generators|fixtures|harnesses}.enabler/`. Methodology users can derive a node path from an artifact category and derive an artifact category from the node path.
- For every test file matching `<subject>.<evidence>.<level>[.<runner>]` that uses a test-infrastructure artifact, the reference resolves to the language's normative path outside `spx/` and outside any `tests/` directory. Methodology users can scan a test's imports and know whether each imported artifact is governed by this PDR.
- For every assertion, source-owned domain truth comes from source modules; generated values come from variable input domains; fixtures remain inert whole-payload inputs; harnesses manage resources and access to behavior. Methodology users can inspect the evidence chain and identify which layer owns each value.
- The dependency direction is one-way: test assertion files depend on test infrastructure, and test infrastructure depends on product behavior only as a consumer. Product modules never import test-infrastructure modules. Methodology users can rely on a product's shipping code containing no references to its test infrastructure.
- Test audits inspect the full test-infrastructure chain before approving evidence. Methodology users receive findings against the artifact that weakens evidence, not only against the visible test file.

## Verification

### Audit

- ALWAYS: every spec tree governed by this methodology contains the canonical subtree `infrastructure → testing → {generators, fixtures, harnesses}` with these exact slugs ([audit])
- ALWAYS: test harness, generator, and fixture implementations live at the language's normative path, outside `spx/` and outside any `tests/` directory ([audit])
- ALWAYS: source modules expose the protocol values, registries, constructors, schemas, typed factories, or other observable contracts that tests need; tests and test infrastructure consume those source contracts instead of recreating them ([audit])
- ALWAYS: harnesses manage setup, teardown, cleanup, resource lifecycle, dependency checks, and access to real behavior, preserving coupling to the behavior an assertion claims to verify ([audit])
- ALWAYS: generators represent variable input domains with meaningful variation, composition, shrinking, or systematic exploration; source-owned singleton shapes come from source constructors, registries, or typed factories ([audit])
- ALWAYS: fixtures are inert whole-payload inputs read from disk, copied into temporary products, or passed by path to the code or tool under test; executed tests do not consume fixture exports ([audit])
- ALWAYS: test audits inspect imported harnesses, generators, and fixture references before approving evidence, and findings name the exact test-infrastructure artifact plus the evidence property affected ([audit])
- ALWAYS: spec assertions for test-infrastructure artifacts pass the same code audit, test evidence audit, and architecture audit as any other production-code node ([audit])
- ALWAYS: language testing, standardizing, and auditing skills teach the path, ownership, generator, fixture, harness, and full-chain audit rules from this decision for their language surface ([audit])
- ALWAYS: the methodology — across skills, references, templates, examples, and audit findings — uses the term "infrastructure" for this category and never "support" as the category name ([audit])
- NEVER: a `tests/` directory at any level of any spec tree contains a test harness, generator, fixture, or any non-test-assertion code — `tests/` contains only typed assertion files matching `<subject>.<evidence>.<level>[.<runner>]` ([audit])
- NEVER: the terms "test support", "test helpers", "test utilities", or "test tools" appear in the methodology, language standards, examples, paths, or audit skills as governing categories for harnesses, generators, or fixtures ([audit])
- NEVER: a test-infrastructure module is imported into a product module — the dependency direction is `tests → infrastructure`, never `product → infrastructure` ([audit])
- NEVER: a test file, harness, generator, fixture, shared test module, or example bag declares a value and asserts against it as if it were source-owned domain truth ([audit])
- NEVER: a generator's whole behavior is `fc.constant(...)`, `st.just(...)`, `Just(...)`, or an equivalent constant-only wrapper for a source-owned singleton shape ([audit])
- NEVER: a fixture file stores isolated strings, numbers, protocol tokens, expected outputs, command names, status values, rule identifiers, message identifiers, or edge-case sets as test data ([audit])
- NEVER: an executed test imports, requires, or consumes exports from fixture modules; fixtures are read, copied, or passed by path as inert input artifacts ([audit])
- NEVER: a harness replaces the behavior under test with a mock, fake, stub, monkeypatch, intercepted network response, or equivalent mechanism while the assertion claims to verify that behavior ([audit])
- NEVER: a property, mapping, scenario, or compliance assertion relies on test infrastructure that weakens the evidence type it names; framework syntax or directory placement cannot upgrade example evidence into property, mapping, or compliance evidence ([audit])
