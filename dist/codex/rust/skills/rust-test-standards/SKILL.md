---
name: rust-test-standards
user-invocable: false
description: Rust test standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The canonical Rust test standards — filename conventions, level mapping, acceptable test doubles, native tooling, property testing, compile-fail testing, snapshot boundaries, shared fixtures, script testing, and coverage.
</objective>

<success_criteria>
Rust test guidance follows this standard when:

- `/test` determines the assertion type, execution level, and exception path before implementation
- `/rust-standards` is loaded before this reference
- co-located spec tests use `<subject>.<evidence>.<level>[.<runner>].rs` or the repo-local overlay
- executed `#[test]`/`#[tokio::test]` functions own every predicate and assertion macro; harnesses and collaborators expose observations without verdict logic
- test-file bindings introduce no data or policy — `let`/`const`/`static`/parameter bindings are valid only when they receive values selected by their semantic owner
- every case and expected result passes the assertion-type provenance and oracle-independence litmus in `<predicate_and_oracle_litmus>`
- doubles preserve coupling to the real trait, function, protocol, or binary seam
- property assertions run through a harness that owns `proptest` / `quickcheck` runner policy and emits replay evidence
- compile-time claims use compile-fail evidence
- shared harnesses, generators, and fixtures live in a separate workspace-member crate as test-infrastructure production code
- deterministic coverage measurement uses the repository's real coverage tool or records that measurement as unavailable; audit-time evidence coverage is a structural reachability judgment made by reading

</success_criteria>

<reference_note>
This is a reference skill. Composing Rust test skills load these standards explicitly before producing tests or judging their evidence quality. It is not a standalone workflow.
</reference_note>

<portable_test_crate>
Use `<product>-testing` for the workspace directory and Cargo package, and
`<product>_testing` for its Rust import path. Cargo maps package hyphens to
underscores in crate imports. Every occurrence of these forms is a placeholder
for the consumer repository's product-owned test-infrastructure crate.
</portable_test_crate>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/rust.md` and `spx/local/rust-tests.md` at the repository root. Read each file that exists after this reference and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<core_model>
Every co-located Rust spec test file name encodes two orthogonal dimensions: the assertion type (what kind of claim is being tested) and the execution level (what infrastructure is required to run it). The canonical pattern is:

```text
spx/.../tests/<subject>.<evidence>.<level>[.<runner>].rs
```

**Evidence tokens** — the assertion type from `/test`:

| Token         | Assertion type | Meaning                                                                      |
| ------------- | -------------- | ---------------------------------------------------------------------------- |
| `scenario`    | Scenario       | Concrete inputs and outputs through the governed function, module, or binary |
| `mapping`     | Mapping        | Table-driven or parameterized cases over a finite input/output mapping       |
| `conformance` | Conformance    | Parser, schema, protocol, CLI contract, or `trybuild` compile-time check     |
| `property`    | Property       | Harness-owned property invariant over a generated domain                     |
| `compliance`  | Compliance     | Violating fixture, lint harness, or rule oracle                              |

**Level tokens** — the execution level, whose infrastructure `<level_tooling>` details:

| Token | Level |
| ----- | ----- |
| `l1`  | 1     |
| `l2`  | 2     |
| `l3`  | 3     |

**Optional runner token** — appended after the level token when the test requires a specific async executor or test harness (e.g., `tokio`, `actix`).

Examples:

```text
spx/55-example.enabler/21-auth.outcome/tests/session_token.scenario.l1.rs
spx/55-example.enabler/21-auth.outcome/tests/registry_fetch.conformance.l2.rs
spx/55-example.enabler/21-auth.outcome/tests/login_flow.scenario.l3.rs
```

Product specs or decisions may restrict which levels the product supports. Follow the repo-local Rust test overlay when it points to the governing spec or decision.
</core_model>

<level_tooling>
Choose the level from execution pain and dependency availability:

| Level | Infrastructure                                                                 | Typical mechanisms                                              |
| ----- | ------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| 1     | Rust stdlib, `cargo test`, temp dirs, repo-required dev tools                  | `#[test]`, pure functions, trait seams, `tempfile`, `rstest`    |
| 2     | Workspace binaries, local services, Docker, databases, local browser harnesses | `assert_cmd`, real adapters, `tokio::test`, `testcontainers`    |
| 3     | External network, deployed systems, SaaS APIs, browser UI, shared environments | live API probes, browser automation, deployed CLI/API workflows |

Level rules:

- Pure computation, parsing, serialization, config loading, command building, and cheap temp-dir filesystem behavior belong at Level 1
- Real workspace binaries, local DBs, local queues, local HTTP services, and containerized collaborators belong at Level 2
- Remote APIs, deployed systems, SaaS collaborators, browser UI, and shared environments belong at Level 3
- Product specs or decisions may disable Level 3 when the suite cannot safely stand up or isolate those collaborators; repo-local overlays only route skills to those declarations

</level_tooling>

<router_mapping>
After `/test` chooses the evidence and level, implement it with these Rust patterns:

| Router Decision                            | Rust implementation                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------------------ |
| Stage 2 -> Level 1                         | `#[test]`, pure functions, `tempfile`, hand-written trait impls                      |
| Stage 2 -> Level 2                         | `assert_cmd`, real local adapters, `tokio::test`, local services                     |
| Stage 2 -> Level 3                         | live API probes, deployed workflow tests, browser automation, remote contract checks |
| Stage 3A: pure computation                 | direct function tests with structural assertions                                     |
| Stage 3B: extract pure part                | pure function at Level 1, boundary at the outer level                                |
| Stage 5 exception 1: failure simulation    | trait impl returning deterministic errors                                            |
| Stage 5 exception 2: interaction protocols | recorder struct capturing calls                                                      |
| Stage 5 exception 3: time/concurrency      | injected clock, paused runtime time, deterministic channels                          |
| Stage 5 exception 4: safety                | recorder or no-op implementation preserving the seam                                 |
| Stage 5 exception 5: combinatorial cost    | configurable in-memory implementation with real-shaped behavior                      |
| Stage 5 exception 6: observability         | capture struct for spans, logs, events, or serialized output                         |
| Stage 5 exception 7: contract probes       | local stub validated against the same contract schema                                |
| compile-time contract                      | `trybuild`                                                                           |
| universal invariant                        | property harness backed by `proptest` or `quickcheck`                                |

</router_mapping>

<acceptable_doubles>
Rust tests preserve evidence quality when they keep coupling to the real seam.

Preferred controlled implementations:

- small hand-written structs implementing the same trait
- recorder structs that capture inputs for later assertions
- deterministic closures passed into function-based seams
- local harness services that exercise the real protocol

Reject by default:

- `mockall`, `faux`, or generated mocks as the primary strategy
- spying on the function or method under test instead of exercising it
- replacing the module under test with a fake implementation

A controlled implementation or recording collaborator implements the same trait boundary as production and exposes observations only. It NEVER accepts an expected outcome, calls an assertion macro, exposes a matcher-style verdict method (`is_valid`, `succeeds`, `was_called_with`), or returns a pass/fail verdict — the linked test asserts against the observations it exposes.

If `/test` reaches a Stage 5 exception, the double must still preserve coupling to the real interface or protocol. The exception explains why a controlled implementation is needed; it does not justify severing the seam.
</acceptable_doubles>

<predicate_and_oracle_litmus>

Apply every question in `/test-evidence-standards` `<common_litmus_questions>`, every per-assertion-type source-and-oracle rule in its `<assertion_type_litmus>`, and every mutation in its `<mutation_litmus>`. That shared set is the complete list; the items below render the ones whose form is Rust-specific and never replace or bound it.

- Invert the `assert!`/`assert_eq!` expression. Only the linked `#[test]` changes; no harness, generator, or collaborator code changes.
- Read the test function alone. Every pass/fail predicate is visible there.
- Trace each case to the spec scenario, complete source-owned enumeration, `proptest`/`quickcheck` domain, external conformance oracle, governing compliance rule, or inert whole-payload fixture.
- Trace each expected result to an oracle outside the production table, algorithm, parser, branch logic, or collaborator verdict method under test.
- Mutate the assertion-relevant production behavior. The test fails.
- Read each fixture and harness. It returns observations, state, or handles — never a verdict, and never an `is_valid`, `succeeds`, `was_called_with`, or `assert_*` method.
- Read a failure message. It reports actual against expected at the `assert_eq!` site, not `assert!(helper(...))`.
- Ask whether the same fixture or harness could serve a test claiming the opposite about the same observation. It can when the predicate is test-owned.

</predicate_and_oracle_litmus>

<tooling>
Use the lightest Rust-native tool that preserves evidence:

| Need                          | Preferred tooling                                             |
| ----------------------------- | ------------------------------------------------------------- |
| L1 scenario and mapping tests | `#[test]`, `assert_eq!`, `rstest` when parameterization helps |
| temp files or dirs            | `tempfile`                                                    |
| async tests                   | `#[tokio::test]` or runtime-specific test macro               |
| property testing              | harness wrapper backed by `proptest` or `quickcheck`          |
| CLI binaries                  | `assert_cmd` and `predicates`                                 |
| textual golden output         | `insta` when the output surface itself is the assertion       |
| compile-fail or diagnostics   | `trybuild`                                                    |
| local services or containers  | `testcontainers` or repo-native harnesses                     |
| coverage                      | `cargo llvm-cov` when available                               |

Snapshot tests are valid only when the textual or structured output surface is itself the contract. They are weak evidence for business logic that has a stronger structural assertion available.
</tooling>

<test_data_policy>

**Every value in a test has exactly one valid origin.** Run through this table for each test value before writing it.

| Origin             | What it means                                                 | Where it lives                      |
| ------------------ | ------------------------------------------------------------- | ----------------------------------- |
| Source-owned       | The production module defines and exports the value           | Import from that module             |
| Generator-produced | Pure code emits varied values each run                        | `<product>-testing/src/generators/` |
| Harness-managed    | Infrastructure mediates interaction with an external resource | `<product>-testing/src/harnesses/`  |
| Fixture files      | An inert whole payload the code under test reads by path      | `<product>-testing/fixtures/`       |
| Descriptive inline | Human-readable text in the test name or assertion message     | Inline in the test file             |

Each origin below has its own section. Descriptive inline is the one exception and needs none. `<test_infrastructure_layout>` is a layout note, not an origin: it closes the section by placing harnesses, generators, and fixtures inside the infrastructure crate, with fixtures split into loader code and data.

**TEST FILES OWN NO DATA OR POLICY.** A named constant in a test file that duplicates a value the production module should own means the production code needs refactoring.

Executed Rust test files are typed assertion files: the `#[test]`/`#[tokio::test]` function or its callbacks own every behavioral predicate and assertion macro. A `let`, `const`, `static`, closure parameter, or macro parameter is valid when it only receives or renames an actual result, source-owned contract, generated value, harness observation, or resource handle and introduces no data or policy. A binding that chooses case data, an expected output, a runner setting, a seed, setup policy, a fixture payload, or a generator domain belongs in the `<product>-testing` workspace crate, source contracts, inert whole-payload fixtures, or justified eval case data.

<source_owned_values>
ALWAYS import command names, rule names, matcher tokens, status values, domain identifiers, and public constants from the owning production module. If the module does not export them yet, refactor it to export them before writing the test.

```rust
// ❌ rejected: duplicates a value the production module should own
const PASS_STATUS: &str = "pass";

// ✅ preferred: import from the production module
use product::audit::GateStatus;
assert_eq!(GateStatus::Pass.as_str(), product::audit::PASS_STATUS_TOKEN);
```

</source_owned_values>

<generator_produced_values>
Use generators for inputs that vary per run. A generator is a pure function — it emits values, holds no state, and has no side effects.

- Use generator strategies for randomized inputs consumed by the property harness
- Write strategy factories for domain-shaped values

```rust
// <product>-testing/src/generators/audit.rs

fn valid_gate_statuses() -> impl Strategy<Value = GateStatus> {
    prop_oneof![
        Just(GateStatus::Pass),
        Just(GateStatus::Fail),
        Just(GateStatus::Skipped),
    ]
}
```

</generator_produced_values>

<harness_managed_values>
Use harnesses for tests that interact with external systems — filesystems, APIs, binaries, testcontainers. A harness manages setup and teardown; it is not self-contained.

```rust
// <product>-testing/src/harnesses/spec_tree.rs

pub struct TestEnv {
    pub root: tempfile::TempDir,
}

impl TestEnv {
    pub fn new() -> Self {
        TestEnv { root: tempfile::tempdir().expect("temp dir") }
    }
}
```

Consumers depend on the workspace-member crate via `[dev-dependencies]` and import as `use <product>_testing::harnesses::spec_tree::TestEnv;`.

</harness_managed_values>

<fixture_files>
Use fixture files for real-world data the code under test would encounter: a captured JSONL from a chat session, a saved API response, a document the parser must handle. Fixture files live in the `<product>-testing/` workspace-member crate under `<product>-testing/fixtures/` and are read from disk by path — never compiled in or imported as modules. This is the cross-language test-infrastructure rule.

Strings and numbers are never valid fixtures. A string literal representing a domain value belongs in the production module or a generator, not a static file.

</fixture_files>

<test_infrastructure_layout>
Harnesses, generators, and inert fixtures are production code. They live in the separate workspace-member crate named in `<portable_test_crate>`, declared as a `[dev-dependencies]` entry of consumers:

- `<product>-testing/src/harnesses/<name>.rs` — modules that mediate access to external resources.
- `<product>-testing/src/generators/<name>.rs` — factories producing valid inputs for proptest/quickcheck/parameterized tests.
- `<product>-testing/src/fixtures/<name>.rs` — fixture-loading code that reads inert data files by path.
- `<product>-testing/fixtures/` (data subdirectory) — inert input files.

Do not create co-located test-infrastructure modules as homes for setup, data, generator selection, fixture loading, harness behavior, diagnostics, credentials, or source vocabulary. Those concerns belong in `<product>-testing/` even when one test file consumes them today. Never use `tests/support/`, `crate::test_support`, `super::tests`, or `#[cfg(test)] mod` patterns as homes for shared test infrastructure — those keep ungoverned utility code inside production crates or under `tests/`.

</test_infrastructure_layout>

</test_data_policy>

<script_testing>
Checked-in Rust script or utility binary entrypoints get thin tests:

- argument parsing through the repository's canonical parser
- dispatch into the imported orchestrator
- exit-code mapping and observable terminal output

The orchestrator carries the main behavioral evidence. Entry files stay small and route to tested modules.
</script_testing>

<alignment_rules>
Match test strategy to assertion type:

| Assertion Type | Rust testing shape                                                    |
| -------------- | --------------------------------------------------------------------- |
| Scenario       | example-based tests with concrete inputs and outputs                  |
| Mapping        | table-driven tests or `rstest` case matrices                          |
| Property       | property harness over generated domains with meaningful invariants    |
| Conformance    | validator tooling, parsers, schema checks, `trybuild` if compile-time |
| Compliance     | targeted assertions, lint harnesses, or rule oracles                  |

Property claims about parsers, serializers, math, ordering, or invariants require property-based tests unless the spec itself narrows the claim to a finite example set.

Compile-time contracts such as trait bounds, derive behavior, or diagnostic guarantees require `trybuild` or equivalent compile-fail evidence.
</alignment_rules>

<level_1_patterns>
Use Level 1 when the governed logic can run with Rust stdlib, normal developer tooling, and temporary local fixtures.

Pure function example:

```rust
#[test]
fn rejects_empty_url_sets() {
    assert!(validate_config(ConfigInput {
        url_sets: BTreeMap::new(),
    }).is_err());
}
```

Dependency seam example:

```rust
use <product>_testing::harnesses::commands::success_runner;
use <product>_testing::generators::repos::source_checkout_path;

#[test]
fn command_builder_reports_success() {
    assert!(sync_repo(&source_checkout_path(), "origin", &success_runner()).unwrap().success);
}
```

Tempdir example. The harness owns the temporary product and its cleanup; the fixture arrives by path; the `#[test]` calls the governed function and asserts:

```rust
use <product>_testing::fixtures::configs::valid_site_config_path;
use <product>_testing::harnesses::filesystem::TempProduct;

#[test]
fn loads_yaml_from_temp_dir() {
    let product = TempProduct::seeded_from(valid_site_config_path());

    let config = load_config(product.path()).unwrap();

    assert_eq!(config.base_url, product::config::DEFAULT_BASE_URL);
}
```

</level_1_patterns>

<property_and_compile_time_patterns>
Use the product property harness for universal invariants. The harness runs the domain; the invariant and its `prop_assert*` macro stay in the `#[test]` closure:

```rust
use <product>_testing::generators::configs::valid_config_strategy;
use <product>_testing::harnesses::properties::run_property;

#[test]
fn config_roundtrips() {
    run_property(valid_config_strategy(), |config| {
        let encoded = encode_config(&config);

        prop_assert_eq!(decode_config(&encoded).unwrap(), config);
        Ok(())
    });
}
```

Property tests MUST run through a harness or wrapper that owns `proptest` / `quickcheck` configuration, seed policy, case count, failure persistence, and replay diagnostics. The test file supplies the invariant and imports generated domains; it does not declare runner tuning or seed policy. On failure, output must include the seed, regression file path, or replay command needed to reproduce the generated case.

That split is exact: the harness owns everything about *how many* cases run and *which* seed produced a failure, and the `#[test]` closure owns *what makes a case pass*. A harness signature that accepts the encode and decode functions and asserts inside itself moves the invariant out of the test and fails the seam.

Use `trybuild` for compile-time guarantees. This is the one shape whose `#[test]` body ends in no assertion macro, and it is a named exception rather than a delegated predicate: `pass` and `compile_fail` are themselves the assertion API for a compile-time claim, they are called in the test where a reader sees them, and the verdict comes from the compiler — an oracle outside the product — against an inert `.stderr` fixture. Inverting the claim still changes only the test, by moving a path between the two calls. A harness that wrapped both calls and reported success would be the delegation this standard rejects.

```rust
#[test]
fn ui_contracts_hold() {
    let cases = trybuild::TestCases::new();

    for builder in <product>_testing::fixtures::ui::valid_builder_paths() {
        cases.pass(builder);
    }
    for builder in <product>_testing::fixtures::ui::invalid_builder_paths() {
        cases.compile_fail(builder);
    }
}
```

</property_and_compile_time_patterns>

<level_2_patterns>
Use Level 2 when governed behavior needs a real binary, runtime, adapter, or local collaborator. The harness starts the binary, container, or service and hands back a handle; the `#[test]` drives the governed behavior through that handle and asserts on what it observes. Worked CLI, async-adapter, and containerized-collaborator examples are in `${SKILL_DIR}/references/level-2.md`.
</level_2_patterns>

<level_3_patterns>
Use Level 3 when governed behavior depends on a real remote collaborator, deployed environment, external network, SaaS system, browser UI, or shared runtime that cannot be replaced by a local Level 2 harness without changing the claim. The harness owns credential resolution, sandbox isolation, and cleanup; the `#[test]` owns the contract claim. Worked remote-API, sandboxed-CLI, and browser-workflow examples are in `${SKILL_DIR}/references/level-3.md`.

Level 3 tests must declare their isolation boundary, credentials, cleanup behavior, and expected runtime. If the repository has no safe Level 3 lane, stop and surface that product decision rather than hiding the dependency behind a skipped test.
</level_3_patterns>

<coverage_rules>
Keep deterministic measurement and audit-time evidence judgment distinct:

- The caller's deterministic gate prefers `cargo llvm-cov`, compares the baseline without the test against the run with the test, and reports the actual per-file or per-function delta. When tooling is unavailable, the caller records that limitation.
- `/audit-rust-tests` runs no coverage command. It reads the evidence chain and judges whether the test drives execution into the assertion-relevant source path, marking trivially total paths `saturated`.
- A structural reachability judgment never claims a measured percentage or replaces the caller's deterministic coverage result.

</coverage_rules>

<failure_modes>

**Failure 1: Placed shared generated domains under `tests/`.** Claude wrote `tests/generators/audit.rs` because the file was only imported by tests. Why it failed: a reusable generator is test-infrastructure production code, so placing it under `tests/` hides ownership and discovery behind an executed-test tree. How to avoid: put reusable Rust generators in `<product>-testing/src/generators/` and import them through the `<product>_testing` dev-dependency crate.

**Failure 2: Copied an owned example into an async harness.** Claude passed `user` by value into `save(user)` and then read `user.id()` and `user.email()` afterward. Why it failed: the example no longer compiled for normal non-`Copy` data and taught consumers to work around ownership rather than express the tested behavior. How to avoid: write Rust examples as executable ownership models; borrow shared generated values when later assertions still need them.

**Failure 3: Taught the predicate seam in prose and broke it in every example.** Claude stated the seam correctly in `<success_criteria>`, `<acceptable_doubles>`, `<predicate_and_oracle_litmus>`, and `<anti_patterns>`, then wrote every worked example as a single call to an `assert_*` harness function with no assertion macro in the `#[test]` body. Why it failed: a reader copies the example, not the prose, so the shipped guidance taught the exact pattern the standard rejects — and the resulting tests pass the reader's own reading of this skill. How to avoid: read each example as the artifact it will become. Every `#[test]` body ends in an `assert!`, `assert_eq!`, `assert_ne!`, `matches!`, or `prop_assert*` the reader can see, or — for a compile-time claim alone — in the `trybuild` `pass` and `compile_fail` registrations that are themselves that claim's assertion API. A harness call that both acts and judges is the defect, whatever it is named.

**Failure 4: Accepted property runner tuning in a test file.** Claude treated a local `const CASES` or seed setting as harmless test configuration. Why it failed: property seed policy, case count, persistence, and replay diagnostics belong to the harness or wrapper, while the test file owns only the invariant. How to avoid: route property assertions through the `<product>-testing` property harness and require reproducible failure output.

</failure_modes>

<anti_patterns>
Reject or rewrite these patterns:

| Anti-pattern                                                                       | Why it fails                                                                                        |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| generated mocks for the main seam                                                  | severs evidence from the real interface                                                             |
| snapshots of hand-written values                                                   | proves serialization of the fixture more than governed logic                                        |
| example-only tests for property claims                                             | misses the universal claim stated by the spec                                                       |
| async tests holding locks across await                                             | creates deadlocks and hides the real concurrency design                                             |
| browser tooling for non-browser code                                               | adds cost without stronger evidence                                                                 |
| compile-time claims tested at runtime                                              | misses the actual contract                                                                          |
| source text read from tests                                                        | proves implementation text rather than behavior                                                     |
| missing harness cleanup                                                            | leaves shared state that changes later test outcomes                                                |
| test-file bindings that choose data, expectations, configuration, or verdict rules | valid bindings only receive values selected by source contracts, harnesses, generators, or fixtures |
| predicate or assertion macro moved into a harness, generator, or collaborator      | the linked `#[test]` function owns every predicate and assertion macro                              |
| property runner tuning in a test file                                              | the property harness owns seed, case count, persistence, and replay diagnostics                     |

Do not require `spx validation literal` for Rust tests. The literal validator is TypeScript-only. Enforce source-owned values through review and Rust test standards instead.

</anti_patterns>

<reference_guides>
Levels 2 and 3 carry no inline examples — their reference files are the only worked examples for those levels.

- `${SKILL_DIR}/references/level-1.md` - the trait-seam and recording-collaborator shapes beyond the inline patterns
- `${SKILL_DIR}/references/level-2.md` - the worked CLI binary, async adapter, and containerized collaborator examples
- `${SKILL_DIR}/references/level-3.md` - the worked remote API, sandboxed CLI, and browser workflow examples, with credentials, isolation, and cleanup

</reference_guides>
