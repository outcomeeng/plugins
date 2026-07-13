---
name: audit-rust-tests
model: sonnet
description: >-
  Rust test-evidence audit methodology composed by a dispatched test-evidence-auditor or implementation-auditor for the Rust tests in scope.
  Reached only through those auditor agents, never the main conversation.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

<dispatch_gate>

This audit runs inside either the dispatched `test-evidence-auditor` context via `audit-tests` or the dispatched `implementation-auditor` context via `audit-implementation`, isolated from the author context that produced the work under audit. When this skill loads in the author/main conversation instead, STOP — dispatch the auditor matching the requested verification surface. An already-dispatched matching auditor that loaded this skill proceeds.

</dispatch_gate>

<objective>
A shared-schema JSON verdict on Rust test evidence — `APPROVED` or `REJECTED`, with each finding naming the assertion or evidence artifact, failed evidence property, and evidence gap.
</objective>

<constraints>

This audit MUST remain read-only. ALWAYS produce only a verdict over test evidence. NEVER edit tests, production code, specs, fixtures, harnesses, generators, or project configuration.

</constraints>

<audit_workflow>

<prerequisites>

Invoke the `rust:rust-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `rust:rust-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `test` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Read local overlay files — each routes skill behavior to the product's governing specs and decisions; overlays supplement skills and do not supersede them:

Read `spx/local/rust.md` if it exists; otherwise apply the loaded skills only.
Read `spx/local/rust-tests.md` if it exists; otherwise apply the loaded skills only.

Invoke `/contextualize` on the spec node under audit — `<SPEC_TREE_CONTEXT>` marker must be present before Gate 1.

This audit runs no deterministic verification — no `cargo fmt`, `cargo clippy`, `cargo test`, `cargo llvm-cov`, or any other project command. The caller brings the project's formatting, linting, tests, and coverage gate to passing on the changeset before dispatch, and CI re-runs them over the whole repository. Spend the whole audit reading the evidence chain.

</prerequisites>

<structural_reading>
Before judging evidence, read the in-scope test files for structural defects — by reading, never by running the project's gate. These are reading observations folded into Gate 1, not a separate deterministic gate:

- **Filename policy** — each file should match `<subject>.<evidence>.<level>[.<runner>].rs` (`<evidence>` ∈ scenario/mapping/conformance/property/compliance, `<level>` ∈ l1/l2/l3). The project's validation owns this convention; note a mismatch as a finding, do not re-validate it.
- **Test-file bindings** — apply the base `/audit-tests` declaration screen before coupling. Any `const`, `static`, `let`, framework fixture parameter, property-generated parameter, or macro/closure parameter binding generated data or fixture state in an executed Rust test file is a `test_owned_declaration` finding. Name the right owner: production source contract, `<package>-testing` harness, `<package>-testing` generator, inert fixture data, or eval case data.
- **Source-file reads** — a test that reads `src/` production files (`read_to_string`, `include_str!`, `std::fs::read`) asserts on source text, not behavior → prose-coupling REJECT in Gate 1 step `four_properties`. Fixture reads under `spx/.../tests/` are fine.
- **Disabled evidence** — any `#[ignore]`, skip-by-early-return, `todo!`, or `unimplemented!` in a test body provides no executable evidence → REJECT in Gate 1. A governed Level 3 lane executes when selected; when no safe executable lane exists, surface the governing product decision or evidence gap instead of approving an ignored test.
- **Generated mock signal** — `mockall`, `automock`, `faux`, `double::` in a test is read and judged in Gate 1 step `controlled_implementations` against `/test` Stage 5 exceptions.

</structural_reading>

<gate_1_assertion>
Entry point is the spec, not the test file.

For each assertion in the spec's Assertions section, execute steps 1-8 in order. First step failure rejects that assertion and moves to the next assertion.

<step name="challenge">
Challenge the assertion:

- Does the assertion derive from an ancestor PDR or ADR claim in `<SPEC_TREE_CONTEXT>`, or is it floating?
- Is the assertion type correct for the claim?
- Does it overlap with another assertion in the same node or parent?

Record challenge findings and continue unless the assertion type is invalid.
</step>

<step name="scope">
Decompose the assertion text into testable clauses using the base `/audit-tests` scope procedure and `/rust-test-standards` `<alignment_rules>`.

The linked tests must exercise every clause with an assertion. A single assertion for a multi-clause claim is a `scope` finding.
</step>

<step name="evidence">
Match the Rust evidence method to the assertion type through `/rust-test-standards` `<alignment_rules>` and `<router_mapping>`. Inspect property-generator domains under the canonical property rules; reject finite examples presented as an open-domain property unless the spec declares that finite domain.
</step>

<step name="controlled_implementations">
Judge controlled implementations against `/rust-test-standards` `<router_mapping>` Stage 5 mappings and `<acceptable_doubles>`.

Generated mock frameworks, fake modules, or stubs that bypass the governed seam reject the assertion unless a Stage 5 exception applies and the real interface or protocol remains intact.
</step>

<step name="oracle">
Identify the source of every expected value.

Reject with an `oracle` finding when the expected value is derived from the module under test. Proceed when the expected value comes from an independent source: the spec, a public constant owned by a different module, an external protocol/schema, a fixture transcript, or a value hand-computed in the test.
</step>

<step name="harness_chain">
Trace every test-infrastructure import:

- imports from the `<package>_testing` workspace-member crate (e.g., `<package>_testing::harnesses::*`, `<package>_testing::generators::*`, `<package>_testing::fixtures::*`) — the canonical home per the product's `test-infrastructure` PDR
- non-canonical legacy locations that must be flagged as misplaced infrastructure: `super::tests`, `crate::test_support`, `tests/support.rs`, `tests/support/`, `#[cfg(test)] mod` test-infrastructure modules inside a product crate
- local functions inside `spx/.../tests/` — these are misplaced infrastructure when they own setup, reusable cases, fixture handling, generator selection, harness behavior, diagnostics, or source vocabulary
- binary harnesses built around `assert_cmd::Command::cargo_bin(...)`

Open each harness. If the harness replaces the governed module instead of exercising it, reject with a `harness_chain` finding. Trace imports until the chain terminates at production code, fixture data, or framework/library code. If a harness lives in a non-canonical legacy location, surface an `extraction_target` finding pointing at the `<package>-testing` workspace-member crate.
</step>

<step name="four_properties">
Apply the Rust supplements:

- Coupling: direct, indirect, transitive, false, partial, severed
- Falsifiability: concrete mutation named for every codebase path or binary contract
- Alignment: every assertion clause maps to exercised test behavior
- Coverage: read whether the test drives execution into the governed source path; no coverage tool is run

First property failure rejects the assertion.
</step>

<step name="coverage">
Establish coverage by reading, never by running `cargo llvm-cov` or any other coverage tool. A dispatched agentic audit runs no deterministic verification — the caller passes the project's tests and coverage gate before dispatch, and CI re-runs them; re-running coverage here re-pays that cost.

Trace, by reading, whether the test drives execution into the governed source path:

1. Read the governed source the assertion names and identify the assertion-relevant functions, branches, and lines.
2. Read the test and follow what it calls into that source — directly, through a harness, or through `cargo_bin(...)` for a binary contract.
3. Judge whether the test's execution reaches the assertion-relevant path.

A test that compiles against the governed module but never drives execution into the assertion-relevant path → REJECT with `coverage`; name the path the test fails to reach, traced from the code. When the assertion-relevant path is trivially total, annotate `saturated`.
</step>

Gate 1 status:

- PASS if every assertion verdict is PASS.
- FAIL if any assertion verdict is REJECT.

</gate_1_assertion>

<gate_2_architectural>
Runs only if Gate 1 is PASS. Scan in-scope tests for repeated setup patterns that belong in shared test infrastructure.

Trigger: two or more in-scope tests share any of these patterns:

- identical `assert_cmd::Command::cargo_bin(...)` setup
- repeated hook JSON builders
- repeated transcript fixture writers
- repeated tempdir/home-directory scaffolding
- repeated stdout/stderr/exit-code assertion functions
- repeated tracing/debug capture setup

Each finding names the pattern, lists at least two occurrences with file and line, and proposes the canonical home in the `<package>-testing` workspace-member crate — `<package>_testing::harnesses::{name}` for shared resource mediators, `<package>_testing::generators::{name}` for input factories, or `<package>_testing::fixtures::{name}` for fixture-loading code.

Gate 2 status:

- PASS if no repeated setup pattern appears in two or more in-scope tests.
- FAIL if any repeated setup pattern appears in two or more in-scope tests.

</gate_2_architectural>

<rust_supplements>
Applied during Gate 1.

<supplement property="coupling">

| Category   | Definition                                                                                                            | Verdict                       |
| ---------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| Direct     | Test calls the governed Rust function, type, module, or binary                                                        | Proceed                       |
| Indirect   | Test calls test infrastructure that calls the governed path                                                           | Proceed after harness tracing |
| Transitive | Test calls a public consumer of the governed path                                                                     | Proceed if the level matches  |
| False      | Test imports the module but never calls assertion-relevant symbols                                                    | REJECT                        |
| Partial    | Test calls the right module with wrong inputs or wrong path                                                           | REJECT                        |
| Severed    | Test or harness replaces the governed behavior with a mock, fake, generated mock, alternate module, or bypassing stub | REJECT                        |

Framework/library imports such as `std`, `tempfile`, `assert_cmd`, `predicates`, `insta`, `tokio`, `proptest`, and `quickcheck` do not count as coupling by themselves. `assert_cmd::Command::cargo_bin(...)` counts as coupling to the named binary contract.

</supplement>

<supplement property="falsifiability">
For each codebase path, name a concrete mutation that would fail the test.

Example:

```text
Module: src/install.rs
Mutation: install writes block hook entries under PreToolUse instead of Stop
Impact: install-tooling L2 scenario test comparing settings JSON fails
```

Reject when no mutation can be named, when generated mocks replace the governed behavior, or when snapshots only capture hand-built fixtures.
</supplement>

<supplement property="alignment">
Alignment passes when every assertion clause is exercised by at least one assertion and the test's evidence method matches the assertion type.

Reject when the test covers a nearby behavior, collapses clauses, uses one example for a mapping, or tests runtime behavior for a compile-time contract.
</supplement>

<supplement property="coverage">
Coverage passes when reading the test against the governed source shows the test drives execution into the assertion-relevant path, or that path is trivially total (`saturated`) and the other three properties pass. No coverage tool is run — the caller and CI own coverage measurement.

Coverage notes do not rescue missing coupling, falsifiability, or alignment.
</supplement>

</rust_supplements>

</audit_workflow>

<verdict_format>

This skill inherits the base `/audit-tests` JSON schema and row names. It appends Rust structural-reading and assertion-evidence findings to `gate-1-assertion`, and appends repeated setup or test-infrastructure extraction findings to `gate-2-architectural`. Every contributed finding populates the base fields `id`, `file`, `line`, `rule`, `severity`, `message`, `evidence_property`, and `required_fix`; this skill introduces no additional required fields. Append findings to matching base rows, never replace a row, and never emit `gate-0-deterministic`. Gate 2 extraction targets a module under the `<package>-testing` workspace-member crate, such as `<package>_testing::harnesses::{name}`, `<package>_testing::generators::{name}`, or `<package>_testing::fixtures::{name}` — never `tests/support/` or `crate::test_support`.

</verdict_format>

<failure_modes>
**Failure 1: Treated binary tests as uncoupled**

Claude rejected a binary L2 test because it imported only `assert_cmd`, `predicates`, and fixture functions. The test spawned the product binary and asserted stdout/exit behavior. Coupling existed through `cargo_bin("mybin")`.

Why it failed: The audit required a source import and missed the executable coupling path through the built product binary.

How to avoid: Count `assert_cmd::Command::cargo_bin(...)` as direct coupling to the named binary contract.

**Failure 2: Approved source-text tests**

Claude accepted a test that read `src/rules.rs` and searched for a string. The implementation could satisfy the source-text assertion while runtime behavior was broken.

Why it failed: Source-text presence was mistaken for behavioral evidence even though the asserted runtime path never executed.

How to avoid: `<structural_reading>` reads in-scope tests for production source-file reads; a test asserting on `src/` text is prose-coupling → REJECT in Gate 1.

**Failure 3: Hard-coded a product-specific Level 3 restriction**

Claude encoded one repository's no-Level-3 test policy in the reusable Rust standard. Other Rust projects can own real remote APIs, browser flows, deployed services, or shared environments where Level 3 evidence is appropriate.

Why it failed: A consumer-specific execution policy was promoted into a portable language standard without governing product truth.

How to avoid: Keep Level 3 in the generic Rust standard. Apply `.l3.rs` rejection only when a governing product spec or decision disables Level 3; a repo-local overlay can route to that declaration, but does not create it.
</failure_modes>

<success_criteria>

The Rust test verdict is sound when:

- Every in-scope assertion was judged on every Gate 1 step — challenge, scope, evidence-method, controlled implementations, oracle independence, harness-chain tracing, the four properties (coupling, falsifiability, alignment, coverage by reading), and the `<structural_reading>` observations (filename, source-reads, disabled evidence, mock signals). Gate 2 was judged when Gate 1 passed; when Gate 1 failed, Gate 2 was omitted as non-applicable.
- The verdict uses the base `/audit-tests` JSON rows and states `overall` as `APPROVED` or `REJECTED`, with no assertion left unevaluated.
- Each `REJECT` finding is falsifiable: it names the assertion or evidence artifact, the failed property, the gate and step, and how the test could pass while the assertion is unfulfilled.
- The same test node yields the same verdict regardless of run order (reproducible).

</success_criteria>
