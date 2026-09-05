---
name: go-test-standards
user-invocable: false
description: >-
  Go test standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The canonical Go test standards — filename conventions, level mapping and build constraints, acceptable test doubles, native tooling, property testing, compile-time and toolchain-oracle testing, golden-file boundaries, shared infrastructure, and coverage.
</objective>

<success_criteria>
Go test guidance follows this standard when:

- `/test` determines the assertion type, execution level, and exception path before implementation
- `/go-standards` is loaded before this reference
- co-located spec tests use `<subject>.<evidence>.<level>[.<runner>]_test.go` or the repo-local overlay
- executed `Test*` functions and their `t.Run` subtests own every predicate and `testing.T` failure call; harnesses, `t.Helper()`-marked functions, and collaborators expose observations without verdict logic
- test-file bindings introduce no data or policy — `:=`, `var`, `const`, table-row, and closure-parameter bindings are valid only when they receive values selected by their semantic owner
- every case and expected result passes the assertion-type provenance and oracle-independence litmus in `<predicate_and_oracle_litmus>`
- doubles preserve coupling to the real interface, function, protocol, or binary seam
- property assertions run through a harness that owns `rapid` checks, seed, and replay policy
- compile-time claims use the Go toolchain as the oracle
- shared harnesses, generators, and fixtures live in `internal/testinfra/` as test-infrastructure production code
- deterministic coverage measurement uses `go test -cover` or records that measurement as unavailable; audit-time evidence coverage is a structural reachability judgment made by reading

</success_criteria>

<reference_note>
This is a reference skill. Composing Go test skills load these standards explicitly before producing tests or judging their evidence quality. It is not a standalone workflow.
</reference_note>

<portable_infrastructure_home>
Use `internal/testinfra/` at the module root for test infrastructure — package `testinfra` with subpackages `harnesses`, `generators`, and `fixtures`, imported as `<module>/internal/testinfra/<subpackage>`. Every occurrence of `<module>` is a placeholder for the consumer repository's module path from `go.mod`. Go's `internal/` rule keeps the packages importable only within that module, and importing them only from `_test.go` files keeps them out of every shipped binary.
</portable_infrastructure_home>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/go.md` and `spx/local/go-tests.md` at the repository root. Read each file that exists after this reference and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<core_model>
Every co-located Go spec test file name encodes two orthogonal dimensions: the assertion type (what kind of claim is being tested) and the execution level (what infrastructure is required to run it). The canonical pattern instantiates the methodology's `<subject>.<evidence>.<level>[.<runner>]` model with Go's mandatory `_test.go` suffix:

```text
spx/.../tests/<subject>.<evidence>.<level>[.<runner>]_test.go
```

The subject — the text before the first dot — never ends in a Go operating-system or architecture name as its last underscore-separated word: `linux`, `darwin`, `windows`, `amd64`, `arm64`, any other `GOOS` or `GOARCH` value, or a `GOOS_GOARCH` pair. The toolchain reads that trailing word as an implicit build constraint and silently excludes the file on every other platform; the evidence, level, and runner tokens after the first dot carry no such risk. A subject such as `parser_linux` becomes `linux_parser` or `parser_linux_support`.

**Evidence tokens** — the assertion type from `/test`:

| Token         | Assertion type | Meaning                                                                        |
| ------------- | -------------- | ------------------------------------------------------------------------------ |
| `scenario`    | Scenario       | Concrete inputs and outputs through the governed function, package, or binary  |
| `mapping`     | Mapping        | Table-driven `t.Run` cases over a finite, source-owned input/output mapping    |
| `conformance` | Conformance    | Parser, schema, protocol, CLI contract, or toolchain-oracle compile-time check |
| `property`    | Property       | Harness-owned `rapid` invariant over a generated domain                        |
| `compliance`  | Compliance     | Violating fixture, analyzer harness, or rule oracle                            |

**Level tokens** — the execution level, whose infrastructure `<level_tooling>` details:

| Token | Level | Build constraint                         |
| ----- | ----- | ---------------------------------------- |
| `l1`  | 1     | none — `go test ./...` runs it           |
| `l2`  | 2     | `//go:build l2` as the file's first line |
| `l3`  | 3     | `//go:build l3` as the file's first line |

`go test` is the default runner an omitted `<runner>` token names. A runner token appears only when the product declares a non-default runner such as `ginkgo`.

Examples:

```text
spx/55-example.enabler/21-auth.outcome/tests/session_token.scenario.l1_test.go
spx/55-example.enabler/21-auth.outcome/tests/registry_fetch.conformance.l2_test.go
spx/55-example.enabler/21-auth.outcome/tests/login_flow.scenario.l3_test.go
```

The declared deterministic test command is `go test -race ./...` — the race detector runs on every Level 1 pass, so data-race safety is deterministic evidence rather than an audit-only claim. A `tests/` directory is its own package (`package tests` or `package <node>_test`); it holds only `_test.go` files and imports the module's packages by their import paths. One file declares one assertion type and one execution level; `t.Run` subtests partition cases inside that cell and never combine cells.

Product specs or decisions may restrict which levels the product supports. Follow the repo-local Go test overlay when it points to the governing spec or decision.
</core_model>

<level_tooling>
Choose the level from the heaviest dependency class among the behavior under test, the oracle, and the enforcement mechanism:

| Level | Infrastructure                                                                                          | Typical mechanisms                                                  |
| ----- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 1     | Go stdlib, `go test`, `t.TempDir()`, the toolchain itself, a product binary the harness builds in-cycle | `testing`, pure functions, interface seams, `httptest`, `os/exec`   |
| 2     | Local services, containers, databases, an installed or downloaded product binary, local browsers        | `testcontainers-go`, real adapters, harness-owned service lifecycle |
| 3     | External network, deployed systems, SaaS APIs, browser UI, shared environments                          | live API probes, browser automation, deployed CLI/API workflows     |

Level rules:

- Pure computation, parsing, encoding, config loading, command building, and cheap temp-dir filesystem behavior belong at Level 1
- A product binary the harness builds with `go build` inside the ordinary test cycle stays at Level 1; the same binary obtained by install, download, or bootstrap is Level 2
- Local databases, queues, HTTP services, and containerized collaborators belong at Level 2
- Remote APIs, deployed systems, SaaS collaborators, browser UI, and shared environments belong at Level 3
- `l2` and `l3` files carry the matching `//go:build` constraint, so `go test ./...` runs Level 1 alone and `go test -tags l2 ./...` adds Level 2
- Product specs or decisions may disable Level 3 when the suite cannot safely stand up or isolate those collaborators; repo-local overlays only route skills to those declarations

</level_tooling>

<router_mapping>
After `/test` chooses the evidence and level, implement it with these Go patterns:

| Router Decision                            | Go implementation                                                                    |
| ------------------------------------------ | ------------------------------------------------------------------------------------ |
| Stage 2 -> Level 1                         | `testing`, pure functions, `t.TempDir()`, hand-written interface implementations     |
| Stage 2 -> Level 2                         | container and service harnesses, real local adapters, installed binaries             |
| Stage 2 -> Level 3                         | live API probes, deployed workflow tests, browser automation, remote contract checks |
| Stage 3A: pure computation                 | direct function tests with structural assertions                                     |
| Stage 3B: extract pure part                | pure function at Level 1, boundary at the outer level                                |
| Stage 5 exception 1: failure simulation    | interface implementation returning deterministic errors                              |
| Stage 5 exception 2: interaction protocols | recording implementation capturing calls                                             |
| Stage 5 exception 3: time/concurrency      | injected clock, deterministic channels, `synctest` where the toolchain provides it   |
| Stage 5 exception 4: safety                | recording or no-op implementation preserving the seam                                |
| Stage 5 exception 5: combinatorial cost    | configurable in-memory implementation with real-shaped behavior                      |
| Stage 5 exception 6: observability         | capture implementation for `slog` handlers, events, or serialized output             |
| Stage 5 exception 7: contract probes       | `httptest` stub validated against the same contract schema                           |
| compile-time contract                      | toolchain oracle — `go vet` or `go build` on an inert fixture package                |
| universal invariant                        | property harness backed by `rapid`                                                   |

</router_mapping>

<acceptable_doubles>
Go tests preserve evidence quality when they keep coupling to the real seam.

Preferred controlled implementations:

- small hand-written structs implementing the same interface
- recording structs that capture inputs for later assertions
- deterministic function values passed into function-typed seams
- `httptest.Server` handlers that exercise the real protocol

Reject by default:

- `gomock`, `mockery`, `moq`, a `mock.Mock` embedding, or other generated or framework mocks as the primary strategy
- monkey-patching a package-level function variable to spy on the function under test
- replacing the package under test with a fake implementation

A controlled implementation or recording collaborator implements the same interface as production and exposes observations only. It NEVER accepts an expected outcome, calls a `testing.T` failure method, exposes a matcher-style verdict method (`IsValid`, `Succeeded`, `WasCalledWith`), or returns a pass/fail verdict — the linked test asserts against the observations it exposes.

If `/test` reaches a Stage 5 exception, the double must still preserve coupling to the real interface or protocol. The exception explains why a controlled implementation is needed; it does not justify severing the seam.
</acceptable_doubles>

<predicate_and_oracle_litmus>

Apply every question in `/test-evidence-standards` `<common_litmus_questions>`, every per-assertion-type source-and-oracle rule in its `<assertion_type_litmus>`, and every mutation in its `<mutation_litmus>`. That shared set is the complete list; the items below render the ones whose form is Go-specific and never replace or bound it.

- Invert the `if got != want` comparison. Only the linked `Test*` function changes; no harness, generator, or collaborator code changes.
- Read the test function alone. Every pass/fail predicate is visible there, including inside each `t.Run` subtest.
- Trace each case to the spec scenario, complete source-owned enumeration, `rapid` domain, external conformance oracle, governing compliance rule, or inert whole-payload fixture.
- Trace each expected result to an oracle outside the production table, algorithm, parser, branch logic, or collaborator verdict method under test.
- Mutate the assertion-relevant production behavior. The test fails.
- Read each fixture and harness. It returns observations, state, or handles — never a verdict, and never an `IsValid`, `Succeeded`, `WasCalledWith`, or `Assert*` method; a `t.Helper()` mark on a function that calls `t.Fatal` on the test's behalf is the seam violation, not an exemption.
- Read a failure message. It reports actual against expected at the comparison site (`t.Errorf("got %v, want %v", got, want)` or a `cmp.Diff`), not `if !helper(...) { t.Fatal() }`.
- Ask whether the same fixture or harness could serve a test claiming the opposite about the same observation. It can when the predicate is test-owned.

</predicate_and_oracle_litmus>

<tooling>
Use the lightest Go-native tool that preserves evidence:

| Need                          | Preferred tooling                                                                                          |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------- |
| L1 scenario and mapping tests | `testing`, `t.Run` tables, `cmp.Diff` for structured comparison                                            |
| temp files or dirs            | `t.TempDir()`                                                                                              |
| concurrency and time          | injected clock, `context.WithCancel`, `testing/synctest` where available                                   |
| property testing              | harness wrapper backed by `pgregory.net/rapid`                                                             |
| CLI binaries                  | harness-built binary through `os/exec`, `exec.Cmd.Output()` to the test                                    |
| HTTP boundaries               | `net/http/httptest`                                                                                        |
| textual golden output         | golden files under `internal/testinfra/fixtures/testdata/` when the output surface itself is the assertion |
| compile-time or diagnostics   | `go vet` or `go build` run by a harness on an inert fixture package                                        |
| local services or containers  | `testcontainers-go` or repo-native harnesses                                                               |
| coverage                      | `go test -race -cover -coverprofile` when the repository uses coverage as evidence                         |

Golden-file tests are valid only when the textual or structured output surface is itself the contract. They are weak evidence for business logic that has a stronger structural assertion available.
</tooling>

<test_data_policy>

**Every value in a test has exactly one valid origin.** Run through this table for each test value before writing it.

| Origin             | What it means                                                 | Where it lives                          |
| ------------------ | ------------------------------------------------------------- | --------------------------------------- |
| Source-owned       | The production package defines and exports the value          | Import from that package                |
| Generator-produced | Pure code emits varied values each run                        | `internal/testinfra/generators/`        |
| Harness-managed    | Infrastructure mediates interaction with an external resource | `internal/testinfra/harnesses/`         |
| Fixture files      | An inert whole payload the code under test reads by path      | `internal/testinfra/fixtures/testdata/` |
| Assertion-assigned | The case the assertion type fixes rather than the test author | Inline in the `Test*` body              |
| Descriptive inline | Human-readable text in the subtest name or failure message    | Inline in the test file                 |

Each origin below has its own section; assertion-assigned and descriptive inline are the two exceptions and need none. An assertion-assigned case is one the assertion type places in the test itself — a scenario's exact interaction as the spec declares it, a conformance expectation from the external oracle, or the violating input a compliance rule names. Such a literal is correct in the `Test*` body, and moving it into a production package so the test can import it gives the case a production address without a production contract. A vocabulary token inside that case — a command name, status value, or rule identifier — stays source-owned and is imported per `<source_owned_values>`; the origin covers the case, never the vocabulary the case is written in. `<test_infrastructure_layout>` is a layout note, not an origin: it closes the section by placing harnesses, generators, and fixtures inside `internal/testinfra/`, with fixtures split into loader code and data.

**TEST FILES OWN NO DATA OR POLICY.** A named constant in a test file that duplicates a value the production package should own means the production code needs refactoring.

Executed Go test files are typed assertion files: the `Test*` function and its `t.Run` subtests own every behavioral predicate and `testing.T` failure call. A `:=`, `var`, `const`, table-row literal, or closure parameter is valid when it only receives or renames an actual result, source-owned contract, generated value, harness observation, or resource handle and introduces no data or policy. A binding that chooses case data the assertion type does not assign to the test, an expected output, a runner setting, a seed, setup policy, a fixture payload, or a generator domain belongs in `internal/testinfra/`, source contracts, inert whole-payload fixtures, or justified eval case data. An assertion-assigned case is the exception the origin table names: it is chosen by the assertion type rather than the test author, so its binding stays in the `Test*` body. A table-driven test over a mapping iterates the source-owned enumeration; a table whose rows the author wrote is test-owned data.

<source_owned_values>
ALWAYS import command names, rule names, matcher tokens, status values, domain identifiers, and exported constants from the owning production package. If the package does not export them yet, refactor it to export them before writing the test.

```go
// ❌ rejected: duplicates a value the production package should own
const passStatus = "pass"

// ✅ preferred: import from the production package and assert against governed behavior
got := audit.RunGate(input).Status
if got != audit.GatePass {
    t.Errorf("status: got %v, want %v", got, audit.GatePass)
}
```

</source_owned_values>

<generator_produced_values>
Use generators for inputs that vary per run. A generator is a pure function — it emits values, holds no state, and has no side effects.

- Write `rapid` generators for randomized inputs consumed by the property harness
- Write generator factories for domain-shaped values

A generated value reaches an executed test only through the property harness, which owns the seed and the replay diagnostics. Drawing a generator once inside an ordinary `Test*` function produces evidence no one can reproduce: the failing value is never reported, and the next run draws a different one, so the failure disappears. A scenario at any level takes the case its assertion assigns instead, and a claim that genuinely ranges over a domain is a property assertion.

```go
// internal/testinfra/generators/audit.go
package generators

func ValidGateStatuses() *rapid.Generator[audit.GateStatus] {
    return rapid.SampledFrom(audit.AllGateStatuses)
}
```

</generator_produced_values>

<harness_managed_values>
Use harnesses for tests that interact with external systems — filesystems, APIs, binaries, containers. A harness manages setup and teardown through `t.Cleanup`; it is not self-contained.

```go
// internal/testinfra/harnesses/filesystem.go
package harnesses

type TempProduct struct {
    root string
}

func NewTempProduct(t *testing.T) *TempProduct {
    t.Helper()
    return &TempProduct{root: t.TempDir()}
}

func (p *TempProduct) Path() string { return p.root }
```

Consumers import `<module>/internal/testinfra/harnesses` from `_test.go` files only.

</harness_managed_values>

<fixture_files>
Use fixture files for real-world data the code under test would encounter: a captured JSONL from a chat session, a saved API response, a document the parser must handle, a Go source file an analyzer must reject. Fixture payloads live under `internal/testinfra/fixtures/testdata/` and are read from disk by path through the `fixtures` package — never compiled in with `embed` for a test or imported as a package. The `testdata` directory name keeps the Go toolchain from compiling a violating `.go` fixture during `go build ./...` or `go vet ./...`, so a fixture that intentionally breaks a rule never breaks the build.

Strings and numbers are never valid fixtures. A string literal representing a domain value belongs in the production package or a generator, not a static file.

</fixture_files>

<test_infrastructure_layout>
Harnesses, generators, and inert fixtures are production code. They live in the module-private `internal/testinfra/` package tree named in `<portable_infrastructure_home>`, imported only from `_test.go` files:

- `internal/testinfra/harnesses/<name>.go` — packages that mediate access to external resources.
- `internal/testinfra/generators/<name>.go` — `rapid` generators producing valid inputs for property tests.
- `internal/testinfra/fixtures/<name>.go` — fixture-resolving code that returns paths under `testdata/`.
- `internal/testinfra/fixtures/testdata/` — inert input files.

The package is `testinfra`, never `test`, which reads as the standard `testing` package and the `go test` verb. Do not create co-located test-infrastructure modules as homes for setup, data, generator selection, fixture loading, harness behavior, diagnostics, credentials, or source vocabulary. Those concerns belong in `internal/testinfra/` even when one test file consumes them today. Never use a file other than `_test.go` in a `tests/` directory, an in-package harness — a `testutil` or `testhelpers` package, or an `export_test.go` that hands a harness or fixture to a test — or a `testdata/` directory outside `internal/testinfra/fixtures/` as homes for shared test infrastructure — those keep ungoverned utility code beside executed tests or inside production packages.

</test_infrastructure_layout>

</test_data_policy>

<script_testing>
Checked-in Go command entrypoints (`cmd/<name>/main.go`) get thin tests:

- flag and argument parsing through the repository's canonical parser
- dispatch into the imported orchestrator
- exit-code mapping and observable terminal output

The orchestrator carries the main behavioral evidence. `main` stays small and routes to tested packages.
</script_testing>

<alignment_rules>
Match test strategy to assertion type:

| Assertion Type | Go testing shape                                                                 |
| -------------- | -------------------------------------------------------------------------------- |
| Scenario       | example-based tests with concrete inputs and outputs                             |
| Mapping        | table-driven `t.Run` tests iterating a source-owned enumeration                  |
| Property       | property harness over `rapid` domains with meaningful invariants                 |
| Conformance    | validator tooling, parsers, schema checks, toolchain oracle if compile-time      |
| Compliance     | targeted assertions, analyzer harnesses, or rule oracles over violating fixtures |

Property claims about parsers, encoders, math, ordering, or invariants require property-based tests unless the spec itself narrows the claim to a finite example set.

Compile-time contracts such as interface satisfaction, `go vet` diagnostics, or build-constraint behavior require toolchain-oracle evidence: the executed test runs `go vet` or `go build` on an inert fixture package and asserts on the diagnostic.
</alignment_rules>

<level_1_patterns>
Use Level 1 when the governed logic can run with the Go stdlib, normal developer tooling, a product binary built in-cycle, and temporary local fixtures. The pure-function, dependency-seam, and tempdir examples are worked in `${CLAUDE_SKILL_DIR}/references/level-1.md`: the harness owns the temporary product and `t.TempDir()` owns cleanup, the fixture arrives by path, and the `Test*` function calls the governed function and asserts.
</level_1_patterns>

<property_and_compile_time_patterns>
Use the product property harness for universal invariants. The harness runs the domain through `rapid.Check`; the invariant and its `t.Fatalf` stay in the closure the `Test*` function passes. Property tests MUST run through a harness or wrapper that owns `rapid` configuration, seed policy, check count, and replay diagnostics. The test file supplies the invariant and imports generated domains; it does not declare runner tuning or seed policy. On failure, output must include the seed or replay command needed to reproduce the generated case — `rapid` prints both when the harness leaves its reporting intact.

That split is exact: the harness owns everything about *how many* cases run and *which* seed produced a failure, and the closure owns *what makes a case pass*. A harness signature that accepts the encode and decode functions and fails inside itself moves the invariant out of the test and fails the seam.

Use the toolchain as the oracle for compile-time guarantees. The executed test runs `go vet` or `go build` on an inert fixture package under `internal/testinfra/fixtures/testdata/` and asserts on the diagnostic the toolchain reports; the compiler is an oracle outside the product, and inverting the claim changes only the test. Both patterns are worked in `${CLAUDE_SKILL_DIR}/references/level-1.md`.
</property_and_compile_time_patterns>

<level_2_patterns>
Use Level 2 when governed behavior needs a local service, container, or an installed binary. The harness starts the container or service, registers `t.Cleanup`, and hands back a handle; the `Test*` function drives the governed behavior through that handle and asserts on what it observes. Worked installed-binary, database-adapter, and containerized-collaborator examples are in `${CLAUDE_SKILL_DIR}/references/level-2.md`.
</level_2_patterns>

<level_3_patterns>
Use Level 3 when governed behavior depends on a real remote collaborator, deployed environment, external network, SaaS system, browser UI, or shared runtime that cannot be replaced by a local Level 2 harness without changing the claim. The harness owns credential resolution, sandbox isolation, and cleanup; the `Test*` function owns the contract claim. Worked remote-API, sandboxed-CLI, and browser-workflow examples are in `${CLAUDE_SKILL_DIR}/references/level-3.md`.

Level 3 tests must declare their isolation boundary, credentials, cleanup behavior, and expected runtime. A missing mandatory credential fails through `t.Fatal`; `t.Skip` is reserved for evidence the suite declares optional. If the repository has no safe Level 3 lane, stop and surface that product decision rather than hiding the dependency behind a skipped test.
</level_3_patterns>

<coverage_rules>
Keep deterministic measurement and audit-time evidence judgment distinct:

- The deterministic gate prefers `go test -race -cover -coverprofile`, compares the baseline without the test against the run with the test, and reports the actual per-file or per-function delta. When tooling is unavailable, the gate records that limitation.
- `/audit-go-tests` runs no coverage command. It reads the evidence chain and judges whether the test drives execution into the assertion-relevant source path, marking trivially total paths `saturated`.
- A structural reachability judgment never claims a measured percentage or replaces the deterministic gate's coverage result.

</coverage_rules>

<anti_patterns>
Reject or rewrite these patterns:

| Anti-pattern                                                                       | Why it fails                                                                                                                                 |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| generated mocks for the main seam                                                  | severs evidence from the real interface                                                                                                      |
| golden files of hand-written values                                                | proves encoding of the fixture more than governed logic                                                                                      |
| example-only tests for property claims                                             | misses the universal claim stated by the spec                                                                                                |
| a mutex held across a blocking call in a test harness                              | creates deadlocks and hides the real concurrency design                                                                                      |
| browser tooling for non-browser code                                               | adds cost without stronger evidence                                                                                                          |
| compile-time claims tested at runtime through reflection                           | misses the actual contract                                                                                                                   |
| source text read from tests                                                        | proves implementation text rather than behavior                                                                                              |
| missing `t.Cleanup` for a started service                                          | leaves shared state that changes later test outcomes                                                                                         |
| test-file bindings that choose data, expectations, configuration, or verdict rules | valid bindings receive values selected by source contracts, harnesses, generators, or fixtures, or carry the case the assertion type assigns |
| a case value moved into a production package so the test can cite that package     | a production address is not a production contract; nothing outside the test requires the symbol                                              |
| a `t.Helper()` function that calls `t.Fatal` on the test's behalf                  | the helper owns the verdict; the linked `Test*` function owns every predicate and failure call                                               |
| a command name, subcommand, or flag written as a literal in the test               | the binary's argument vocabulary is a source contract the owning package exports                                                             |
| `rapid` check count or seed set in a test file                                     | the property harness owns seed, check count, and replay diagnostics                                                                          |
| `t.Skip` on a missing mandatory dependency                                         | unavailable required evidence never passes; it fails through `t.Fatal`                                                                       |

Do not require `spx validation literal` for Go tests. The literal validator is TypeScript-only. Enforce source-owned values through review and Go test standards instead.

</anti_patterns>

<failure_modes>

**Failure 1: Taught the predicate seam in prose and broke it in a `t.Helper()`.** Claude wrote `requireStatus(t, got, want)` marked `t.Helper()` and called it from every subtest, so no `Test*` body carried a comparison. Why it failed: the helper owned the verdict, so inverting a claim meant editing the helper every test shared, and the failure output reported the helper's line. How to avoid: a `t.Helper()` mark removes a frame from failure output and nothing more; keep the `if got != want` and the `t.Errorf` in the `Test*` function or its subtest.

</failure_modes>

<reference_guides>
The skill body states the rules; the reference files carry the only worked examples for every level.

- `${CLAUDE_SKILL_DIR}/references/level-1.md` - the worked pure-function, dependency-seam, recorder, tempdir, property, and compile-time examples
- `${CLAUDE_SKILL_DIR}/references/level-2.md` - the worked installed-binary, database-adapter, and containerized collaborator examples
- `${CLAUDE_SKILL_DIR}/references/level-3.md` - the worked remote API, sandboxed CLI, and browser workflow examples, with credentials, isolation, and cleanup

</reference_guides>
