---
name: audit-rust-tests
description: >-
  Rust test-evidence audit methodology — judges the Rust tests in scope against
  the spec-tree and Rust-specific evidence properties.
model: sonnet
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Skill
---

<objective>
A verdict on Rust test evidence — APPROVED, or REJECTED with each finding naming the assertion or evidence artifact, the failed evidence property, and the evidence gap.
</objective>

<constraints>

This audit is read-only. Produce a verdict over test evidence; never edit tests, production code, specs, fixtures, harnesses, generators, or project configuration.

</constraints>

<audit_workflow>

<prerequisites>

Invoke the `rust:rust-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Invoke the `rust:rust-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Invoke the `spec-tree:audit-tests` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Invoke the `spec-tree:test` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

Read local overlay files — each routes skill behavior to the product's governing specs and decisions; overlays supplement skills and do not supersede them:

Read `spx/local/rust.md` if it exists; otherwise apply the loaded skills only.
Read `spx/local/rust-tests.md` if it exists; otherwise apply the loaded skills only.

Invoke `/contextualize` on the spec node under audit — `<SPEC_TREE_CONTEXT>` marker must be present before Gate 1.

This audit runs no deterministic verification — no `cargo fmt`, `cargo clippy`, `cargo test`, `cargo llvm-cov`, or any other project command. Spend the whole audit reading the evidence chain.

</prerequisites>

<audit_scope>

Begin with the current governing spec and its current evidence links. A deleted Rust test or test-infrastructure path belongs to this audit only when a current `[test]` assertion still links it or a current linked test still imports it. When the current spec carries no `[test]` link to the deleted path and no current evidence chain references it, classify the retired path as outside current Rust test-evidence scope and return `NOT_APPLICABLE` for that path. Never demand restoration of deterministic evidence solely because the base revision or changeset deletion names the retired path. When a current `[test]` assertion still links a missing path, report missing evidence against that current assertion.

Use read-only `git diff` only when the supplied changeset scope requires confirming whether an evidence path was deleted. Run no other shell command from this concern skill.

</audit_scope>

<structural_reading>
Before judging evidence, read the in-scope test files for structural defects — by reading, never by running the project's gate. These are reading observations folded into Gate 1, not a separate deterministic gate:

- **Filename policy** — each file MUST match `<subject>.<evidence>.<level>[.<runner>].rs` (`<evidence>` ∈ scenario/mapping/conformance/property/compliance, `<level>` ∈ l1/l2/l3). The project's validation owns this convention; note a mismatch as a `filename_policy` finding carrying property `alignment` from the base `/audit-tests` enum — a filename that misdeclares its evidence type or level misaligns the file with the assertion it claims to evidence — and do not re-validate it.
- **Test-file bindings** — apply the base `/audit-tests` semantic binding screen before coupling. A `const`, `static`, `let`, framework fixture parameter, property-generated parameter, or macro/closure parameter is valid when it only receives an actual result, source-owned contract, generated value, harness observation, callback input, resource handle, or fixture path and introduces no data or policy. Emit a finding carrying property `declarations` and the base `/audit-tests` rule label the choice matches — `test-owned configuration` for runner settings, seed policy, retries, setup policy, or lifecycle policy, and `test-owned data` for hand-picked data, boundary bags, expected outputs, fixture contents, or generator domains. Keep the two labels distinct. Keep every predicate and assertion macro in the linked test function or callback; a binding, closure, or helper that moves a predicate or assertion macro out carries property `predicate-ownership`, rule `assertion-seam`, remediation target `test-file`.
- **Source-file reads** — a test that reads `src/` production files (`read_to_string`, `include_str!`, `std::fs::read`) asserts on source text, not behavior → prose-coupling REJECT in Gate 1 step `four_properties`. Inert fixture data is read by path from `<product>-testing/fixtures/`; co-located `spx/.../tests/` remains the home of typed assertion files. When a loaded overlay points to a governing product spec or decision that explicitly amends this contract, follow that declaration; the overlay does not redefine fixture placement itself.
- **Disabled evidence** — a bare `#[ignore]` (no reason), skip-by-early-return, `todo!`, or `unimplemented!` in a test body provides no evidence → REJECT in Gate 1 carrying property `coverage` from the base `/audit-tests` enum, since execution never reaches the assertion-relevant path. A reasoned `#[ignore = "..."]` is acceptable in a `.l3.rs` file only when a loaded product spec or decision declares that credentialed Level 3 lane; otherwise disabled evidence rejects. Outside `.l3.rs`, reasoned ignore is misplaced.
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

Record challenge findings and continue unless the assertion type is invalid. A `challenge` finding carries property `alignment` from the base `/audit-tests` enum — the claim itself is malformed or misaligned with its governing decision.
</step>

<step name="scope">
Decompose the assertion text into testable clauses.

Example:

| Assertion                                          | Clauses                                              |
| -------------------------------------------------- | ---------------------------------------------------- |
| "MUST exit 0 with no stdout for invalid hook JSON" | (1) invalid JSON input, (2) exit 0, (3) empty stdout |

The linked tests must exercise every clause with an assertion. A single assertion for a multi-clause claim is a `scope` finding carrying property `coverage` from the base `/audit-tests` enum — clauses of the claim go unexercised.
</step>

<step name="evidence">
Match the Rust evidence method to the assertion type:

| Type        | Required Rust evidence                                                                   | Reject if                                 |
| ----------- | ---------------------------------------------------------------------------------------- | ----------------------------------------- |
| Scenario    | concrete inputs through the governed function, module, or binary                         | only existence or truthiness is checked   |
| Mapping     | table-driven cases, `rstest`, or looped fixtures with at least two meaningful cases      | one example stands in for a mapping       |
| Conformance | parser, schema, protocol harness, CLI contract, or `trybuild` for compile-time contracts | manual shape checks replace the validator |
| Property    | `proptest` or `quickcheck` with meaningful generators and invariants                     | examples are wrapped in property syntax   |
| Compliance  | violating fixture or lint harness for a current `[test]` link                            | no violating input or rule oracle exists  |

For property tests, inspect the generator domain. `Just`, one-value ranges, or tiny enumerations reduce the property to examples unless the spec explicitly declares a finite set.

An assertion tagged `[audit]` carries no assertion type and is outside Rust test-evidence scope. Skip it rather than treating the marker as test evidence.
</step>

<step name="controlled_implementations">
Judge controlled implementations against `/test` exceptions:

| Exception                | Legitimate Rust pattern                                         |
| ------------------------ | --------------------------------------------------------------- |
| 1. Failure modes         | trait impl returning deterministic errors                       |
| 2. Interaction protocols | recorder struct capturing calls                                 |
| 3. Time/concurrency      | injected clock, paused runtime time, deterministic channels     |
| 4. Safety                | recorder or no-op implementation preserving the seam            |
| 5. Combinatorial cost    | configurable in-memory implementation with real-shaped behavior |
| 6. Observability         | capture struct for spans, logs, events, or serialized output    |
| 7. Contract probes       | local stub validated against the same contract schema           |

Generated mock frameworks, fake modules, or stubs that bypass the governed seam reject the assertion unless a Stage 5 exception applies and the real interface or protocol remains intact. Such a rejection carries property `falsifiability` from the base `/audit-tests` enum — a severed seam means no production mutation can break the test.
</step>

<step name="oracle">
Identify the source of every expected value.

Reject with an `oracle` finding carrying property `oracle-independence` and remediation target `independent-oracle` from the base `/audit-tests` enum when the expected value is derived from the module under test. This is distinct from `falsifiability`: an expected result computed by the same path that produces the actual result passes even when both are wrong. Proceed when the expected value comes from an independent source: the spec, a public constant owned by a different module, an external protocol/schema, a fixture transcript, or a value hand-computed in the test.
</step>

<step name="harness_chain">
Trace every test-infrastructure import:

- imports from the `<product>_testing` workspace-member crate (e.g., `<product>_testing::harnesses::*`, `<product>_testing::generators::*`, `<product>_testing::fixtures::*`) — the canonical home per the product's `test-infrastructure` PDR
- non-canonical legacy locations that must be flagged as misplaced infrastructure: `super::tests`, `crate::test_support`, `tests/support.rs`, `tests/support/`, `#[cfg(test)] mod` test-infrastructure modules inside a product crate
- local functions inside `spx/.../tests/` — these are misplaced infrastructure when they own setup, reusable cases, fixture handling, generator selection, harness behavior, diagnostics, or source vocabulary
- binary harnesses built around `assert_cmd::Command::cargo_bin(...)`

Open each harness. If the harness replaces the governed module instead of exercising it, reject with a `harness_chain` finding. Trace imports until the chain terminates at production code, fixture data, or framework/library code. If a harness lives in a non-canonical legacy location, surface an `extraction_target` finding pointing at the `<product>-testing` workspace-member crate.
</step>

<step name="four_properties">
Apply the Rust supplements:

- Coupling: classified from the full `<supplement property="coupling">` taxonomy below — every category it names, never a subset
- Falsifiability: concrete mutation named for every codebase path or binary contract
- Alignment: every assertion clause maps to exercised test behavior
- Coverage: read whether the test drives execution into the governed source path; no coverage tool is run

First property failure rejects the assertion.
</step>

<step name="coverage">
Establish coverage by reading, never by running `cargo llvm-cov` or any other coverage tool. This audit runs no deterministic verification.

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

Each finding names the pattern, lists at least two occurrences with file and line, and proposes the canonical home in the `<product>-testing` workspace-member crate — `<product>_testing::harnesses::{name}` for shared resource mediators, `<product>_testing::generators::{name}` for input factories, or `<product>_testing::fixtures::{name}` for fixture-loading code.

Gate 2 status:

- PASS if no repeated setup pattern appears in two or more in-scope tests.
- FAIL if any repeated setup pattern appears in two or more in-scope tests.

</gate_2_architectural>

<rust_supplements>
Applied during Gate 1.

<supplement property="coupling">

This supplement specializes each category of the coupling taxonomy `/audit-tests` owns to Rust paths. Classify from the table below rather than a subset of it; every category the canonical taxonomy names appears here, so a category missing from this table would silently narrow the verdict.

| Category           | Definition                                                                                                                 | Verdict                                         |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Direct             | Test calls the governed Rust function, type, module, or binary                                                             | Proceed                                         |
| Indirect           | Test calls test infrastructure that calls the governed path                                                                | Proceed after harness tracing                   |
| Transitive         | Test calls a public consumer of the governed path                                                                          | Proceed if the level matches                    |
| Laundered indirect | Calls a `<product>_testing` module that exists only to expose hardcoded values back to the test                            | REJECT — laundering                             |
| False              | Test imports the module but never calls assertion-relevant symbols                                                         | REJECT                                          |
| Partial            | Test calls the right module with wrong inputs or wrong path                                                                | REJECT                                          |
| None               | Test imports only its test framework or dev-dependency crates, with zero product-crate coupling                            | REJECT — tautology                              |
| Severed            | Test or harness replaces the governed behavior with a mock, fake, generated mock, alternate module, or bypassing stub      | REJECT — coupling severed                       |
| Prose-coupling     | Reads an authored prose/doc body and asserts its content, including through a harness constant or an infrastructure reader | REJECT — couples to authored text, not behavior |

Framework/library imports such as `std`, `tempfile`, `assert_cmd`, `predicates`, `insta`, `tokio`, `proptest`, and `quickcheck` do not count as coupling by themselves. `assert_cmd::Command::cargo_bin(...)` counts as coupling to the named binary contract. The Prose-coupling row is the table-side form of the source-file read that `<structural_reading>` screens for; both reach the same REJECT.

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
Coverage passes when reading the test against the governed source shows the test drives execution into the assertion-relevant path, or that path is trivially total (`saturated`) and the other three properties pass. No coverage tool is run — this audit establishes coverage by reading.

Coverage notes do not rescue missing coupling, falsifiability, or alignment.
</supplement>

</rust_supplements>

</audit_workflow>

<verdict_format>

This skill composes the base `/audit-tests` verdict: the row names (`gate-1-assertion`, `gate-2-architectural`) and the JSON schema are defined in its `<verdict_format>` and are not redefined here. This skill contributes Rust-specific finding detail into those rows. The audit emits no `gate-0-deterministic` row — it runs no deterministic verification; the structural reading observations from `<structural_reading>` are folded into the Gate 1 (`gate-1-assertion`) findings. Gate 2 extraction target: a module under the `<product>-testing` workspace-member crate, e.g. `<product>_testing::harnesses::{name}`, `<product>_testing::generators::{name}`, or `<product>_testing::fixtures::{name}` — never `tests/support/` or `crate::test_support`, which are legacy non-canonical locations.

When `<audit_scope>` finds that a retired path has no current `[test]` assertion or current evidence-chain owner, emit this alternate concern result instead of the inherited rows:

```json
{
  "status": "NOT_APPLICABLE",
  "subjects": ["<retired-repository-relative-path>"],
  "explanation": "No current [test] assertion or evidence chain references the retired path."
}
```

Emit this shape only when every supplied subject is outside current Rust test-evidence scope. A current broken `[test]` link remains applicable and produces the inherited `REJECTED` verdict.

</verdict_format>

<failure_modes>
**Failure 1: Treated binary tests as uncoupled**

What happened: Claude rejected a binary L2 test because it imported only `assert_cmd`, `predicates`, and fixture functions. The test spawned the product binary and asserted stdout/exit behavior. Coupling existed through `cargo_bin("mybin")`.

Why it failed: Claude treated import shape as the only coupling signal and ignored execution through the product binary contract.

How to avoid: Count `assert_cmd::Command::cargo_bin(...)` as direct coupling to the named binary contract.

**Failure 2: Approved source-text tests**

What happened: Claude accepted a test that read `src/rules.rs` and searched for a string. The implementation could satisfy the source-text assertion while runtime behavior was broken.

Why it failed: Source-text presence is prose coupling and proves no executable behavior.

How to avoid: `<structural_reading>` reads in-scope tests for production source-file reads; a test asserting on `src/` text is prose-coupling → REJECT in Gate 1.

**Failure 3: Hard-coded a product-specific Level 3 restriction**

What happened: Claude encoded one repository's no-Level-3 test policy in the reusable Rust standard. Other Rust projects can own real remote APIs, browser flows, deployed services, or shared environments where Level 3 evidence is appropriate.

Why it failed: Product-local execution policy was promoted into a reusable language standard.

How to avoid: Keep Level 3 in the generic Rust standard. Apply `.l3.rs` rejection only when a governing product spec or decision disables Level 3; a repo-local overlay can route to that declaration, but does not create it.
</failure_modes>

<success_criteria>

The Rust test verdict is sound when:

- Every applicable rule was judged: each in-scope assertion received every Gate 1 step and the `<structural_reading>` observations (filename, source-reads, disabled evidence, mock signals); Gate 2 was judged when Gate 1 passed and omitted only when Gate 1 rejected the evidence.
- Every deleted Rust test or test-infrastructure path was classified from current spec links and current evidence chains, with retired evidence returned as `NOT_APPLICABLE` and current broken `[test]` links reported as missing evidence.
- Applicable scope states an overall `APPROVED` / `REJECTED` with no assertion left unevaluated; a composition-only retired-path scope emits the defined `NOT_APPLICABLE` result.
- Each `REJECT` finding is falsifiable: it names the assertion or evidence artifact, the failed property, the gate and step, and how the test could pass while the assertion is unfulfilled.
- The same test node yields the same verdict regardless of run order (reproducible).

</success_criteria>
