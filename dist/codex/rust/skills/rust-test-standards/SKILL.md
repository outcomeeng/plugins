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
The standards artifact is complete when it defines:

- the canonical `<subject>.<evidence>.<level>[.<runner>].rs` filename contract and independent evidence, level, and runner axes
- the level mapping for local Rust, local infrastructure, and remote or credentialed dependencies
- source-owned data, zero-declaration evidence files, and separate workspace-member ownership for harnesses, generators, and fixtures
- controlled implementations that preserve coupling to the real trait, function, protocol, or binary seam
- harness-owned property runner policy with replay evidence and compile-fail evidence for compile-time claims
- the boundary between external deterministic coverage measurement and relevant-path coverage established by reading the complete evidence chain

</success_criteria>

<reference_note>
This is a reference skill. `/test-rust` uses it to produce tests and `/audit-rust-tests` uses it to judge their evidence quality. Consuming workflows load `/rust-standards` before this reference and use `/test` to determine assertion type, execution level, and exception path.

Rust code examples use `acme_testing` as the compilable stand-in for the consumer package's `<package>_testing` dev-dependency crate.
</reference_note>

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
| `compliance`  | Compliance     | Violating fixture, lint harness, or architecture review marker               |

**Level tokens** — the infrastructure required to run the test:

| Token | Level | Infrastructure                                                                 |
| ----- | ----- | ------------------------------------------------------------------------------ |
| `l1`  | 1     | Rust stdlib, `cargo test`, temp dirs, repo-required dev tools                  |
| `l2`  | 2     | Workspace binaries, local services, Docker, databases, local browser harnesses |
| `l3`  | 3     | External network, deployed systems, SaaS APIs, browser UI, shared environments |

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

If `/test` reaches a Stage 5 exception, the double must still preserve coupling to the real interface or protocol. The exception explains why a controlled implementation is needed; it does not justify severing the seam.
</acceptable_doubles>

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
| deterministic coverage gate   | the repository-declared command, such as `cargo llvm-cov`     |

Snapshot tests are valid only when the textual or structured output surface is itself the contract. They are weak evidence for business logic that has a stronger structural assertion available.
</tooling>

<test_data_policy>

**Every value in a test has exactly one valid origin.** Run through this table for each test value before writing it.

| Origin             | What it means                                                 | Where it lives                      |
| ------------------ | ------------------------------------------------------------- | ----------------------------------- |
| Source-owned       | The production module defines and exports the value           | Import from that module             |
| Generator-produced | Pure code emits varied values each run                        | `<package>-testing/src/generators/` |
| Harness-managed    | Infrastructure mediates interaction with an external resource | `<package>-testing/src/harnesses/`  |
| Descriptive inline | Human-readable text in the test name or assertion message     | Inline in the test file             |

**THERE ARE NO VALID TEST-OWNED CONSTANTS.** A named constant in a test file that duplicates a value the production module should own means the production code needs refactoring.

Executed Rust test files are typed assertion files. They do not declare `const`, `static`, or `let` bindings; every value or configuration choice those declarations would bind belongs in the `<package>-testing` workspace crate, source contracts, inert whole-payload fixtures, or justified eval case data.

**1. Source-owned values**

ALWAYS import command names, rule names, matcher tokens, status values, domain identifiers, and public constants from the owning production module. If the module does not export them yet, refactor it to export them before writing the test.

```rust
// ❌ rejected: duplicates a value the production module should own
const PASS_STATUS: &str = "pass";

// ✅ preferred: import from the production module
use product::audit::GateStatus;
assert_eq!(GateStatus::Pass.as_str(), product::audit::PASS_STATUS_TOKEN);
```

**2. Generator-produced values**

Use generators for inputs that vary per run. A generator is a pure function — it emits values, holds no state, and has no side effects.

- Use generator strategies for randomized inputs consumed by the property harness
- Write strategy factories for domain-shaped values

```rust
// <package>-testing/src/generators/audit.rs

fn valid_gate_statuses() -> impl Strategy<Value = GateStatus> {
    prop_oneof![
        Just(GateStatus::Pass),
        Just(GateStatus::Fail),
        Just(GateStatus::Skipped),
    ]
}
```

**3. Harness-managed**

Use harnesses for tests that interact with external systems — filesystems, APIs, binaries, testcontainers. A harness manages setup and teardown; it is not self-contained.

```rust
// <package>-testing/src/harnesses/spec_tree.rs

pub struct TestEnv {
    pub root: tempfile::TempDir,
}

impl TestEnv {
    pub fn new() -> Self {
        TestEnv { root: tempfile::tempdir().expect("temp dir") }
    }
}
```

Consumers depend on the workspace-member crate via `[dev-dependencies]`; the examples import it as `use acme_testing::harnesses::spec_tree::TestEnv;`.

**4. Fixture files**

Use fixture files for real-world data the code under test would encounter: a captured JSONL from a chat session, a saved API response, a document the parser must handle. Fixture files live in the `<package>-testing/` workspace-member crate under `<package>-testing/fixtures/` and are read from disk by path — never compiled in or imported as modules. This is the cross-language test-infrastructure rule.

Strings and numbers are never valid fixtures. A string literal representing a domain value belongs in the production module or a generator, not a static file.

**5. Test infrastructure layout**

Harnesses, generators, and inert fixtures are production code. They live in a separate workspace-member crate (`<package>-testing/` directory at workspace root, Cargo package `<package>-testing`, Rust import path `<package>_testing`), declared as a `[dev-dependencies]` entry of consumers:

- `<package>-testing/src/harnesses/<name>.rs` — modules that mediate access to external resources.
- `<package>-testing/src/generators/<name>.rs` — factories producing valid inputs for proptest/quickcheck/parameterized tests.
- `<package>-testing/src/fixtures/<name>.rs` — fixture-loading code that reads inert data files by path.
- `<package>-testing/fixtures/` (data subdirectory) — inert input files.

Do not create co-located test-infrastructure modules as homes for setup, data, generator selection, fixture loading, harness behavior, diagnostics, credentials, or source vocabulary. Those concerns belong in `<package>-testing/` even when one test file consumes them today. Never use `tests/support/`, `crate::test_support`, `super::tests`, or `#[cfg(test)] mod` patterns as homes for shared test infrastructure — those keep ungoverned utility code inside production crates or under `tests/`.

- Do not read production source files as test input to prove behavior

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
| Compliance     | targeted assertions, lint harnesses, or architecture review markers   |

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
use acme_testing::harnesses::commands::success_runner;
use acme_testing::generators::repos::source_checkout_path;

#[test]
fn command_builder_reports_success() {
    assert!(sync_repo(&source_checkout_path(), "origin", &success_runner()).unwrap().success);
}
```

Tempdir example:

```rust
use acme_testing::fixtures::configs::valid_site_config;
use acme_testing::harnesses::filesystem::assert_loads_yaml_from_temp_config;

#[test]
fn loads_yaml_from_temp_dir() {
    assert_loads_yaml_from_temp_config(valid_site_config(), load_config);
}
```

</level_1_patterns>

<property_and_compile_time_patterns>
Use the product property harness for universal invariants:

```rust
use acme_testing::generators::configs::valid_config_strategy;
use acme_testing::harnesses::properties::assert_config_roundtrips;

#[test]
fn config_roundtrips() {
    assert_config_roundtrips(valid_config_strategy(), encode_config, decode_config);
}
```

Property tests MUST run through a harness or wrapper that owns `proptest` / `quickcheck` configuration, seed policy, case count, failure persistence, and replay diagnostics. The test file supplies the invariant and imports generated domains; it does not declare runner tuning or seed policy. On failure, output must include the seed, regression file path, or replay command needed to reproduce the generated case.

Use `trybuild` for compile-time guarantees:

```rust
#[test]
fn ui_contracts_hold() {
    acme_testing::harnesses::trybuild::assert_ui_contracts(
        acme_testing::fixtures::ui::valid_builders(),
        acme_testing::fixtures::ui::invalid_builders(),
    );
}
```

</property_and_compile_time_patterns>

<level_2_patterns>
Use Level 2 when governed behavior needs a real binary, runtime, adapter, or local collaborator.

CLI binary example:

```rust
use acme_testing::fixtures::projects::empty_project;
use acme_testing::harnesses::commands::assert_init_command_writes_project_files;

#[test]
fn init_command_writes_project_files() {
    assert_init_command_writes_project_files(empty_project());
}
```

Async L2 example:

```rust
use acme_testing::fixtures::users::valid_user;
use acme_testing::harnesses::database::assert_user_repository_roundtrip;

#[tokio::test]
async fn repository_persists_and_loads_user() {
    assert_user_repository_roundtrip(valid_user(), UserRepository::new).await;
}
```

</level_2_patterns>

<level_3_patterns>
Use Level 3 when governed behavior depends on a real remote collaborator, deployed environment, external network, SaaS system, browser UI, or shared runtime that cannot be replaced by a local Level 2 harness without changing the claim.

Remote API example:

```rust
#[tokio::test]
async fn published_package_is_fetchable_from_registry() {
    acme_testing::harnesses::registry::assert_sandbox_package_publish_and_fetch().await;
}
```

Browser workflow example:

```rust
#[tokio::test]
async fn login_flow_reaches_dashboard() {
    acme_testing::harnesses::browser::assert_login_flow_reaches_dashboard().await;
}
```

Level 3 tests must declare their isolation boundary, credentials, cleanup behavior, and expected runtime. If the repository has no safe Level 3 lane, stop and surface that product decision rather than hiding the dependency behind a skipped test.
</level_3_patterns>

<specified_node_verification>
A specified node is the one narrow exception to all-green Rust compile-bearing gates. Apply it only in Write mode after source-contract inspection establishes that the owning production module or item does not exist yet.

- The focused test MUST fail only because that declared production module or owned item is missing. Syntax, harness, workspace, manifest, configuration, and unrelated compilation failures remain failures.
- `cargo fmt` or the repository's canonical formatting command MUST exit zero.
- `cargo clippy`, `cargo check`, and repository equivalents may exit nonzero only when every diagnostic is the direct compiler consequence of that same missing production module or item. Actual lint diagnostics and unrelated compiler diagnostics fail the gate.
- Deterministic coverage is not applicable until the implementation exists; record that state instead of running a coverage command that can only repeat the missing-item failure.
- Record the exact missing owner and diagnostics, and add the node path relative to `spx/` to `spx/EXCLUDE`.
- Once implementation exists, the exception ends and the normal passing lint, compile, and applicable coverage gates apply.

</specified_node_verification>

<coverage_rules>
Coverage has separate deterministic and agentic responsibilities:

- The caller runs the repository-declared coverage command when one exists; `cargo llvm-cov` is the direct fallback only when the repository declares no wrapper and requires a coverage gate.
- The test-evidence audit never runs a coverage tool. It reads the complete evidence chain and passes coverage only when the test drives execution into every assertion-relevant source path, or when the path is trivially total and marked `saturated`.
- A passing deterministic coverage percentage does not replace relevant-path tracing, and relevant-path tracing does not claim a measured percentage.
- When the repository declares no deterministic coverage gate, record that absence without weakening the audit's read-based coverage requirement.

</coverage_rules>

<failure_modes>

**Failure 1: Placed shared generated domains under `tests/`.** Claude wrote `tests/generators/audit.rs` because the file was only imported by tests. Why it failed: a reusable generator is test-infrastructure production code, so placing it under `tests/` hides ownership and discovery behind an executed-test tree. How to avoid: put reusable Rust generators in `<package>-testing/src/generators/` and import them through the package's underscore-normalized dev-dependency crate name, represented as `acme_testing` in these examples.

**Failure 2: Copied an owned example into an async harness.** Claude passed `user` by value into `save(user)` and then read `user.id()` and `user.email()` afterward. Why it failed: the example no longer compiled for normal non-`Copy` data and taught consumers to work around ownership rather than express the tested behavior. How to avoid: write Rust examples as executable ownership models; borrow shared generated values when later assertions still need them.

**Failure 3: Accepted property runner tuning in a test file.** Claude treated a local `const CASES` or seed setting as harmless test configuration. Why it failed: property seed policy, case count, persistence, and replay diagnostics belong to the harness or wrapper, while the test file owns only the invariant. How to avoid: route property assertions through the `<package>-testing` property harness and require reproducible failure output.

</failure_modes>

<anti_patterns>
Reject or rewrite these patterns:

| Anti-pattern                            | Why it fails                                                                     |
| --------------------------------------- | -------------------------------------------------------------------------------- |
| generated mocks for the main seam       | severs evidence from the real interface                                          |
| snapshots of hand-written values        | proves serialization of the fixture more than governed logic                     |
| example-only tests for property claims  | misses the universal claim stated by the spec                                    |
| async tests holding locks across await  | creates deadlocks and hides the real concurrency design                          |
| browser tooling for non-browser code    | adds cost without stronger evidence                                              |
| compile-time claims tested at runtime   | misses the actual contract                                                       |
| source text read from tests             | proves implementation text rather than behavior                                  |
| missing harness cleanup                 | leaves shared state that changes later test outcomes                             |
| test-file-local bindings and parameters | source contracts, harnesses, generators, inert fixtures, or eval data own values |
| property runner tuning in a test file   | the property harness owns seed, case count, persistence, and replay diagnostics  |

Do not require `spx validation literal` for Rust tests. The literal validator is TypeScript-only. Enforce source-owned values through review and Rust test standards instead.

</anti_patterns>

<reference_guides>
Use these level guides when concrete Rust-native examples beyond the inline patterns are needed:

- `${SKILL_DIR}/references/level-1.md` - pure computation, tempdir, trait seams, and property tests
- `${SKILL_DIR}/references/level-2.md` - CLI binaries, async adapters, local services, and containerized collaborators
- `${SKILL_DIR}/references/level-3.md` - remote systems, browser flows, credentials, isolation, and cleanup

</reference_guides>
