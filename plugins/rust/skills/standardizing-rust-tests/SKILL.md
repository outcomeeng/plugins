---
name: standardizing-rust-tests
disable-model-invocation: true
description: Rust test standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Canonical Rust test standards loaded after `/standardizing-rust`. Defines filename conventions, level mapping, acceptable test doubles, Rust-native testing tools, property-testing requirements, compile-fail testing, snapshot boundaries, shared fixture policy, script testing, and coverage expectations for Rust projects.
</objective>

<success_criteria>
Rust test guidance follows this standard when:

- `/testing` determines evidence mode, execution level, and exception path before implementation
- `/standardizing-rust` is loaded before this reference
- co-located spec tests use `<subject>.<evidence>.<level>[.<runner>].rs` or the repo-local overlay
- doubles preserve coupling to the real trait, function, protocol, or binary seam
- property assertions use meaningful `proptest` or `quickcheck` properties
- compile-time claims use compile-fail evidence
- shared harnesses and fixtures live in test-owned support code
- coverage claims are measured with the repository's real coverage tool or recorded as unavailable

</success_criteria>

<reference_note>
This is a reference skill. `/testing-rust` uses it to produce tests and `/auditing-rust-tests` uses it to judge their evidence quality.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/rust.md` and `spx/local/rust-tests.md` at the repository root. Read each file that exists after this reference and apply them as repo-local specializations.
</repo_local_overlay>

<core_model>
Every co-located Rust spec test file name encodes two orthogonal dimensions: the evidence type (what kind of claim is being tested) and the execution level (what infrastructure is required to run it). The canonical pattern is:

```text
spx/.../tests/<subject>.<evidence>.<level>[.<runner>].rs
```

**Evidence tokens** — the assertion type from `/testing`:

| Token         | Assertion type | Meaning                                                                      |
| ------------- | -------------- | ---------------------------------------------------------------------------- |
| `scenario`    | Scenario       | Concrete inputs and outputs through the governed function, module, or binary |
| `mapping`     | Mapping        | Table-driven or parameterized cases over a finite input/output mapping       |
| `conformance` | Conformance    | Parser, schema, protocol, CLI contract, or `trybuild` compile-time check     |
| `property`    | Property       | `proptest` or `quickcheck` invariant over a generated domain                 |
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
spx/32-api.enabler/54-auth.outcome/tests/session_token.scenario.l1.rs
spx/32-api.enabler/54-auth.outcome/tests/registry_fetch.conformance.l2.rs
spx/32-api.enabler/54-auth.outcome/tests/login_flow.scenario.l3.rs
```

Repository overlays may restrict which levels the project supports. Follow the repo-local Rust test convention when it exists.
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
- Project overlays may disable Level 3 when the suite cannot safely stand up or isolate those collaborators

</level_tooling>

<router_mapping>
After `/testing` chooses the evidence and level, implement it with these Rust patterns:

| Router Decision                            | Rust implementation                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------------------ |
| Stage 2 -> Level 1                         | `#[test]`, pure functions, `tempfile`, hand-written trait impls                      |
| Stage 2 -> Level 2                         | `assert_cmd`, real local adapters, `tokio::test`, local services                     |
| Stage 2 -> Level 3                         | live API probes, deployed workflow tests, browser automation, remote contract checks |
| Stage 3A: pure computation                 | direct function tests with structural assertions                                     |
| Stage 3B: extract pure part                | pure helper at Level 1, boundary at the outer level                                  |
| Stage 5 exception 1: failure simulation    | trait impl returning deterministic errors                                            |
| Stage 5 exception 2: interaction protocols | recorder struct capturing calls                                                      |
| Stage 5 exception 3: time/concurrency      | injected clock, paused runtime time, deterministic channels                          |
| Stage 5 exception 4: safety                | recorder or no-op implementation preserving the seam                                 |
| Stage 5 exception 5: combinatorial cost    | configurable in-memory implementation with real-shaped behavior                      |
| Stage 5 exception 6: observability         | capture struct for spans, logs, events, or serialized output                         |
| Stage 5 exception 7: contract probes       | local stub validated against the same contract schema                                |
| compile-time contract                      | `trybuild`                                                                           |
| universal invariant                        | `proptest` or `quickcheck`                                                           |

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

If `/testing` reaches a Stage 5 exception, the double must still preserve coupling to the real interface or protocol. The exception explains why a controlled implementation is needed; it does not justify severing the seam.
</acceptable_doubles>

<tooling>
Use the lightest Rust-native tool that preserves evidence:

| Need                          | Preferred tooling                                             |
| ----------------------------- | ------------------------------------------------------------- |
| L1 scenario and mapping tests | `#[test]`, `assert_eq!`, `rstest` when parameterization helps |
| temp files or dirs            | `tempfile`                                                    |
| async tests                   | `#[tokio::test]` or runtime-specific test macro               |
| property testing              | `proptest` or `quickcheck`                                    |
| CLI binaries                  | `assert_cmd` and `predicates`                                 |
| textual golden output         | `insta` when the output surface itself is the assertion       |
| compile-fail or diagnostics   | `trybuild`                                                    |
| local services or containers  | `testcontainers` or repo-native harnesses                     |
| coverage                      | `cargo llvm-cov` when available                               |

Snapshot tests are valid only when the textual or structured output surface is itself the contract. They are weak evidence for business logic that has a stronger structural assertion available.
</tooling>

<test_data_policy>
Use source-owned values when the production system owns them.

- Import command names, rule names, matcher tokens, public constants, and domain identifiers from the owning production module
- Keep descriptive test titles and assertion diagnostics inline
- Put stable test-only strings, ids, dates, and expected-output snippets in test fixture support
- Put shared harnesses, generated data, and Stage 5 doubles in test-owned support modules
- Use co-located helper modules only when the helper serves one test file
- Do not read production source files as test input to prove behavior

</test_data_policy>

<script_testing>
Checked-in Rust script or helper binary entrypoints get thin tests:

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
| Property       | `proptest` or `quickcheck` with meaningful invariants                 |
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
    let result = validate_config(ConfigInput {
        url_sets: BTreeMap::new(),
    });

    assert!(result.is_err());
}
```

Dependency seam example:

```rust
trait CommandRunner {
    fn run(&self, program: &str, args: &[&str]) -> Result<CommandOutput, CommandError>;
}

struct SuccessRunner;

impl CommandRunner for SuccessRunner {
    fn run(&self, _: &str, _: &[&str]) -> Result<CommandOutput, CommandError> {
        Ok(CommandOutput::success("done"))
    }
}

#[test]
fn command_builder_reports_success() {
    let runner = SuccessRunner;
    let result = sync_repo(Path::new("/src"), "origin", &runner).unwrap();

    assert!(result.success);
}
```

Tempdir example:

```rust
#[test]
fn loads_yaml_from_temp_dir() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("config.yaml");
    std::fs::write(&path, "site_dir: ./site\n").unwrap();

    let config = load_config(&path).unwrap();

    assert_eq!(config.site_dir, PathBuf::from("./site"));
}
```

</level_1_patterns>

<property_and_compile_time_patterns>
Use `proptest` for universal invariants:

```rust
proptest! {
    #[test]
    fn config_roundtrips(input in valid_config_strategy()) {
        let encoded = encode_config(&input).unwrap();
        let decoded = decode_config(&encoded).unwrap();

        prop_assert_eq!(decoded, input);
    }
}
```

Use `trybuild` for compile-time guarantees:

```rust
#[test]
fn ui_contracts_hold() {
    let cases = trybuild::TestCases::new();

    cases.pass("tests/ui/valid_builder.rs");
    cases.compile_fail("tests/ui/missing_required_field.rs");
}
```

</property_and_compile_time_patterns>

<level_2_patterns>
Use Level 2 when governed behavior needs a real binary, runtime, adapter, or local collaborator.

CLI binary example:

```rust
#[test]
fn init_command_writes_project_files() {
    let temp = tempfile::tempdir().unwrap();

    assert_cmd::Command::cargo_bin("herder")
        .unwrap()
        .current_dir(temp.path())
        .args(["init", "demo"])
        .assert()
        .success();

    assert!(temp.path().join("demo/Cargo.toml").exists());
}
```

Async L2 example:

```rust
#[tokio::test]
async fn repository_persists_and_loads_user() {
    let db = test_database().await;
    let repo = UserRepository::new(db.pool());

    repo.save(&user_fixture()).await.unwrap();
    let loaded = repo.find(UserId::new(1)).await.unwrap();

    assert_eq!(loaded.email(), "user@example.com");
}
```

</level_2_patterns>

<level_3_patterns>
Use Level 3 when governed behavior depends on a real remote collaborator, deployed environment, external network, SaaS system, browser UI, or shared runtime that cannot be replaced by a local Level 2 harness without changing the claim.

Remote API example:

```rust
#[tokio::test]
#[ignore = "requires credentialed sandbox"]
async fn published_package_is_fetchable_from_registry() {
    let client = registry_client_from_env().unwrap();

    let package = client.fetch_package("example-package").await.unwrap();

    assert_eq!(package.name, "example-package");
}
```

Browser workflow example:

```rust
#[tokio::test]
#[ignore = "requires browser service and deployed app"]
async fn login_flow_reaches_dashboard() {
    let browser = browser_session_from_env().await.unwrap();

    browser.goto("/login").await.unwrap();
    browser.fill("#email", "user@example.com").await.unwrap();
    browser.click("button[type=submit]").await.unwrap();

    assert!(browser.text("main").await.unwrap().contains("Dashboard"));
}
```

Level 3 tests must declare their isolation boundary, credentials, cleanup behavior, and expected runtime. If the repository has no safe Level 3 lane, stop and surface that product decision rather than hiding the dependency behind a skipped test.
</level_3_patterns>

<coverage_rules>
Coverage is evidence only when measured against the exercised module:

- Prefer `cargo llvm-cov` for per-file and per-function coverage deltas
- Compare baseline coverage without the test under audit against coverage with the test included
- Report the actual delta; do not infer coverage from reading the file
- If the repository lacks usable coverage tooling, state that limitation explicitly and do not fabricate a coverage pass

</coverage_rules>

<anti_patterns>
Reject or rewrite these patterns:

| Anti-pattern                           | Why it fails                                                 |
| -------------------------------------- | ------------------------------------------------------------ |
| generated mocks for the main seam      | severs evidence from the real interface                      |
| snapshots of hand-written values       | proves serialization of the fixture more than governed logic |
| example-only tests for property claims | misses the universal claim stated by the spec                |
| async tests holding locks across await | creates deadlocks and hides the real concurrency design      |
| browser tooling for non-browser code   | adds cost without stronger evidence                          |
| compile-time claims tested at runtime  | misses the actual contract                                   |
| source text read from tests            | proves implementation text rather than behavior              |
| missing harness cleanup                | leaves shared state that changes later test outcomes         |

</anti_patterns>

<reference_guides>
Use these level guides when concrete Rust-native examples beyond the inline patterns are needed:

- `levels/level-1.md` - pure computation, tempdir, trait seams, and property tests
- `levels/level-2.md` - CLI binaries, async adapters, local services, and containerized collaborators
- `levels/level-3.md` - remote systems, browser flows, credentials, isolation, and cleanup

</reference_guides>
