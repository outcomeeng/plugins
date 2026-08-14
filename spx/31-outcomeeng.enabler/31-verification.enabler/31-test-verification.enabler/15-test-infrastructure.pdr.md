# Test Infrastructure

Every spec tree governed by the Spec Tree methodology governs harnesses, generators, and inert fixtures as infrastructure that is crucial to delivering value; places their implementations at predictable per-language homes outside `spx/` and outside any `tests/` directory; and audits the full evidence chain from a spec assertion through every imported test-infrastructure artifact. Methodology users rely on this as a product-surface guarantee: predictable implementation homes per language, consistent category semantics, and every test-infrastructure artifact governed as production code by a naturally placed spec node.

Methodology users observe and rely on this governance shape:

- A harness, generator, or inert fixture is infrastructure because it enables test assertions that establish product truth.
- The artifact's governing spec node sits wherever the product's Spec Tree naturally places that concern: a shared infrastructure node when category-wide policy is a real product concern, the node whose assertions depend on the artifact when the behavior is local to that node, or another ancestor or descendant selected by normal decomposition.
- The governing spec node declares the artifact's behavior or category contract, carries tests for that declaration when deterministic evidence exists, and inherits the decisions in its ancestry.
- A product may have nodes named `infrastructure`, `test`, `generators`, `fixtures`, or `harnesses` when those names express natural product concerns. The methodology does not require those slugs, a top-level `infrastructure` node, or a fixed category subtree.

The methodology uses the term **infrastructure** for this testing category. The terms "support", "helpers", "utilities", and "tools" are not category names for test infrastructure.

Test-infrastructure implementations live outside `spx/` and outside any `tests/` directory, in a home the build keeps off the product's shipped artifacts. Each language realizes that separation idiomatically: a sibling directory or package for TypeScript and Python, a separate workspace-member crate for Rust, and for Go a module-private `internal/` package — Go restricts `internal/` to importers within the same module, and importing it only from `_test.go` files keeps the toolchain from compiling it into any shipped binary. The per-language path methodology users can expect:

| Language       | Product code                                | Test-infrastructure home                                                                                                                                                                                                                                                                        |
| -------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TypeScript** | `src/` or product root                      | `testing/` at product root, path-mapped to `@testing/`: `@testing/harnesses/*`, `@testing/generators/*`, `@testing/fixtures/*`                                                                                                                                                                  |
| **Python**     | `<package>/`                                | `<package>_testing/`: `<package>_testing/harnesses/`, `<package>_testing/generators/`, `<package>_testing/fixtures/`. `<package>` is the product's importable Python package name declared by its packaging metadata; illustrative example: `outcomeeng/` paired with `outcomeeng_testing/`     |
| **Rust**       | `src/` of the product crate                 | A separate workspace-member crate at `<product>-testing/` (Cargo package `<product>-testing`, Rust import path `<product>_testing`), declared as a dev-dependency of consumers; modules `<product>_testing::harnesses::*`, `<product>_testing::generators::*`, `<product>_testing::fixtures::*` |
| **Go**         | Module packages (root, `internal/`, `cmd/`) | `internal/testinfra/` (package `testinfra` — not `test`, which collides with the standard library): `internal/testinfra/harnesses/`, `internal/testinfra/generators/`, `internal/testinfra/fixtures/`, imported as `<module>/internal/testinfra/...`                                            |

For Rust, Cargo normalizes hyphens to underscores in import paths: package `<product>-testing` is imported as `<product>_testing`.

Each language plugin declares its normative path in this table or in a PDR amendment that extends this table. Language ADRs govern implementation mechanics such as `tsconfig` path mapping, Python package discovery, Cargo workspace configuration, or Go module and `internal/` placement.

The contents of `spx/<node>/tests/` are typed assertion files only, one evidence type per file, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`. The executed test owns every behavioral predicate and assertion API call. Harnesses, generators, and inert fixtures carry no predicates or assertions of their own and live elsewhere. Test infrastructure is production code for the methodology — it implements behavior, exposes interfaces that tests depend on, and can invalidate downstream evidence when it drifts — differing from product code only in purpose: it enables test assertions instead of shipping product behavior.

## Category Semantics

**Source contracts come first.** Source modules expose the domain contracts tests need: protocol values, command names, status values, rule identifiers, message identifiers, schemas, registries, constructors, typed factories, or other observable source-owned APIs. When a test for existing behavior can only pass by copying source literals, pinning arbitrary example objects, mocking away the behavior under test, or hiding values in test infrastructure, the source code under test is improved first.

**Harnesses manage context and resources.** A harness mediates access to real behavior or real local/remote infrastructure. It owns setup, teardown, lifecycle, cleanup, mandatory dependency checks, and diagnostics for resources such as temporary filesystems, browsers, product binaries, local services, APIs, databases, Docker containers, and remote credentialed endpoints. It does not own arbitrary domain data and does not replace the behavior an assertion claims to verify.

Harnesses expose observations, resource handles, or callback inputs to the executed test. They never call an assertion API, return a pass/fail verdict, accept an expected outcome, or expose verdict-shaped helpers such as `*_succeeds`, `is_valid`, `was_called_with`, or `assert_called`. Controlled implementations and recording collaborators preserve the real dependency boundary and expose observations; the linked test states what those observations mean.

**Bindings are judged by semantic ownership.** A variable, parameter, destructuring binding, or local alias in an executed test is valid when it only receives or renames an observation, source-owned contract, generated value, or resource handle selected elsewhere and introduces no data, expected result, setup policy, runner configuration, or verdict rule. A binding is invalid when it chooses a domain member, case, expected result, seed, retry count, fixture payload, setup policy, or assertion policy. Syntax never decides ownership by itself.

Property-based test harnesses own execution configuration: seed selection, run counts, replay input, and failure diagnostics. A failing property run reports enough replay data for the same generated case to run again, and the executed test file does not own those settings through local variables, constants, or framework options.

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

## Evidence Chain

Evidence includes the full chain from a spec assertion to the executed test file and every imported test-infrastructure artifact. A test audit opens imported harnesses, generators, and fixture references before approving the assertion. Findings name the exact artifact and the evidence property affected: source ownership, coupling, falsifiability, domain variation, oracle independence, cleanup safety, or coverage.

Test infrastructure cannot make a weaker evidence shape impersonate a stronger one:

- A Property assertion requires a generator or source-owned enumerable domain with meaningful variation and a replayable property-run harness; property-framework syntax around one example is scenario evidence.
- A Mapping assertion requires a finite source-owned mapping or a generated finite domain with independently derived expectations; a copied expected-output table is a tautology.
- A Scenario assertion requires a behavior-relevant case whose inputs and expected outputs are owned by source contracts, generated domains, or whole-payload fixtures; arbitrary example bags do not establish domain truth.
- A Compliance assertion with `[test]` evidence exercises a real violating case or rule oracle; a passing-only example does not prove enforcement.

The case source and oracle remain independent of the implementation author and the code path under test:

- A Scenario case is the concrete interaction declared by the spec or a real whole-payload fixture; an implementation-derived example bag is invalid.
- A Mapping case set is the complete finite source-owned domain, with expectations derived independently from the implementation mapping.
- A Property case set comes from a generator over the declared domain, while the invariant lives in the executed test and the generator does not reuse the production acceptance function.
- A Conformance oracle is external to the implementation under test: a schema, reference implementation, standard tool, or separately owned contract.
- A Compliance case follows the governing rule and includes a real violating input; disabling the enforcement makes the linked test fail.

Two mutation checks expose invalid seams and oracles. Inverting the predicate changes only the linked test; any required harness change means the harness encodes the assertion. Mutating or disabling the production behavior makes the evidence fail; continued success means the case source, oracle, or execution path is not independent.

## Spec Traceability

A test-infrastructure artifact is traceable to the spec tree through the same declaration path as any other infrastructure artifact. Category names are semantics, not required node slugs. A test-infrastructure artifact is traceable in one of two ways:

- The artifact is covered by a naturally placed spec node's assertions because it only participates in that category's standard contract.
- The artifact exposes behavior, policy, lifecycle, or reusable semantics that materially affect evidence; it has its own natural child spec or is named by an assertion in the governing node.

Methodology users derive the artifact category from its implementation home or behavior, and derive the governing node by following the evidence chain from the spec assertion to the executed test file and the imported test-infrastructure artifact. A fixed tree path is never the source of governance.

## Rationale

Methodology users rely on four predictable properties: where implementation files live, what category of artifact each file is, who owns the values it carries, and how audits judge the evidence chain. The decision gives those properties one answer that holds across products and languages while preserving natural Spec Tree placement for the governing node. Leaving implementation homes, ownership, or artifact semantics to local convention would make every product invent its own answer, defeat drift detection across audits, and produce contradictory skill-driven guidance across languages; forcing every product into the same root subtree would make the tree less true by moving local or shared evidence concerns away from the product area they actually serve. Natural placement keeps the truth hierarchy intact while category semantics and audit traversal give audits the authority to reject literal laundering, severed coupling, and helper directories masquerading as evidence.

**Why a separate home, not inside `tests/`.** Putting harnesses, generators, or fixtures in `tests/support/`, `tests/_support/`, `tests/helpers/`, `tests/fixtures/`, `conftest.py` as a helper home, or equivalent inside-test paths mixes production-grade test infrastructure into a directory whose contents are typed assertion files only per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md`. Methodology users lose the per-file evidence guarantee, and audit findings can no longer distinguish an assertion from scaffolding that changes the assertion's meaning.

**Why a home the build excludes, not the product ship path.** Putting test infrastructure on the product's shipped build path — `src/test/`, `product/test/`, or similar in languages that compile every reachable module into the artifact — makes bundle minimization, dead-code analysis, packaging, dependency audits, and public API review conflate product behavior with test-enabling behavior. The separation is realized per language: a sibling directory or package for TypeScript and Python, a separate workspace-member crate for Rust, and for Go a module-private `internal/` package — Go restricts `internal/` to importers within the same module, and importing it only from `_test.go` files keeps the toolchain from compiling it into any shipped binary.

**Why source contracts come first.** Copying protocol values into tests or infrastructure decouples evidence from the code under test. If a status value, command name, diagnostic code, registry member, schema, or constructor belongs to source behavior, source exports it through a semantically named API. Tests import that API. When the API does not exist, the source shape changes before the test is accepted.

**Why generators must vary.** A property test or generated scenario earns evidence value by searching an input space, shrinking counterexamples, and composing valid domain values. A constant-only generator hides a named constant behind a framework call and makes review harder without adding evidence. Source-owned singleton shapes are source contracts, not generated domains.

**Why fixtures stay inert.** Whole-payload fixtures are useful because their complete shape exercises parsers, linters, scanners, validators, file walkers, and external contracts. Imported fixture modules are different: they execute as test dependencies and export test-owned values. That turns fixtures into shared constant bags and hides the evidence boundary.

**Why harnesses manage resources, not truth.** A harness removes repetition around lifecycle and external systems. It must not own domain truth or replace the behavior under test. A context manager, RAII guard, or typed factory that cleans up resources increases evidence quality; a harness that mocks the asserted behavior or stores expected outputs severs evidence.

**Why audits traverse the chain.** A test file can look clean while the defect lives in `@testing/generators/*`, `<package>_testing/fixtures/*`, or `<product>_testing::harnesses::*`. Full-chain inspection is the only way to reject literal laundering and coupling camouflage reliably.

The decision accepts these trade-offs:

| Trade-off                                                                                               | Mitigation / reasoning                                                                                                                                                                            |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Methodology users remember a different implementation path per language                                 | Each language's test and audit skills document the path and examples for that language; the category semantics remain identical across languages.                                                 |
| Natural spec placement requires following the evidence chain instead of looking for one fixed node path | Test audits already traverse assertion files, imports, and test-infrastructure artifacts; the same traversal identifies the governing node and keeps local concerns local.                        |
| Products with inside-`tests/` helper directories or fixture modules move files                          | The move preserves behavior while restoring the evidence boundary: assertion files stay in `spx/<node>/tests/`, and test infrastructure moves to the language's normative home.                   |
| The methodology mandates artifact semantics, not only paths                                             | Audits can reject laundering even when files sit in the right directory; correct placement alone does not make a generator variable, a fixture inert, or a harness coupled to source behavior.    |
| Source modules may need architecture changes before tests become acceptable                             | This is the intended forcing function. Tests that require copied source literals or replacement mocks expose missing source contracts; improving source testability produces better product APIs. |
| Rust workspace-member test infrastructure requires Cargo workspace configuration                        | Rust products pay the setup cost once and gain a package boundary that keeps product crates from importing test infrastructure as shipping code.                                                  |

## Product properties

- **Placement and derivability**: every test-infrastructure artifact lives at the language's normative path outside `spx/` and outside any `tests/` directory, and every such artifact is governed by a naturally placed spec node — so a methodology user derives the category from the implementation home or artifact behavior, derives the governing node from the evidence chain, and scans a test's imports to know whether each imported artifact is governed by this PDR.
- **Ownership and one-way dependency**: source-owned domain truth comes from source modules, generated values from variable input domains, fixtures stay inert whole-payload inputs, harnesses manage resources and expose observations, and the linked test alone owns predicates and assertion calls; the dependency direction is one-way (test assertion files depend on test infrastructure; product modules never import it) — so a methodology user inspects the evidence chain to identify which layer owns each value and relies on shipping code carrying no test-infrastructure references.
- **Full-chain audit**: test audits inspect the complete test-infrastructure chain, semantic binding ownership, case provenance, and oracle independence before approving evidence, naming the exact artifact that weakens evidence and the evidence property affected — not only the visible test file.

## Verification

### Audit

- ALWAYS: every test harness, generator, and fixture is governed by a naturally placed spec node whose assertions or child specs cover the artifact's behavior, policy, lifecycle, reusable semantics, or category contract ([audit])
- ALWAYS: test harness, generator, and fixture implementations live at the language's normative path, outside `spx/` and outside any `tests/` directory ([audit])
- ALWAYS: spec assertions for test-infrastructure artifacts pass the same code audit, test evidence audit, and architecture audit as any other production-code node ([audit])
- ALWAYS: language test, standards, and audit skills teach the path, ownership, generator, fixture, harness, and full-chain audit rules from this decision for their language surface ([audit])
- ALWAYS: the methodology — across skills, references, templates, examples, and audit findings — uses the term "infrastructure" for this category and never "support" as the category name ([audit])
- NEVER: require or fabricate a top-level `infrastructure → testing → {generators, fixtures, harnesses}` subtree solely to govern test infrastructure — nodes with those slugs exist only when normal Spec Tree composition selects them for a real product concern ([audit])
- NEVER: a `tests/` directory at any level of any spec tree contains a test harness, generator, fixture, or any non-test-assertion code — `tests/` contains only typed assertion files per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/21-evidence-types.pdr.md` ([audit])
- NEVER: the terms "test support", "test helpers", "test utilities", or "test tools" appear in the methodology, language standards, examples, paths, or audit skills as governing categories for harnesses, generators, or fixtures ([audit])
- NEVER: a test-infrastructure module is imported into a product module — the dependency direction is `tests → infrastructure`, never `product → infrastructure` ([audit])
- NEVER: a property, mapping, scenario, or compliance assertion relies on test infrastructure that weakens the evidence type it names; framework syntax or directory placement cannot upgrade example evidence into property, mapping, or compliance evidence ([audit])
