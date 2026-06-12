---
name: auditing-rust-tests
description: Use when asked by the user to invoke the Rust test audit skill
allowed-tools: Read, Grep, Glob, Bash
---

{!% require_skill 'rust:standardizing-rust' %!}

{!% require_skill 'rust:standardizing-rust-tests' %!}

{!% require_skill 'spec-tree:testing' %!}

{!% require_skill 'spec-tree:auditing-tests' %!}

<objective>
Rust test audit. Three gates run in strict sequence:

1. Gate 0 deterministic readiness: filename policy, forbidden source-file reads, skipped tests, generated-mock signals, Rust validation, and coverage-tool availability.
2. Gate 1 assertion audit: per-assertion challenge, scope, evidence method, controlled implementations, oracle independence, harness chain, and four-property evidence check.
3. Gate 2 architectural DRY: repeated setup patterns that belong in shared test infrastructure.

A gate failure skips every later gate.
</objective>

<prerequisites>

1. Invoking 4 skills: Already done above.
2. Read local overlay files — each routes skill behavior to the product's governing specs and decisions; overlays supplement skills and do not supersede them — and are loaded below:

Read `spx/local/rust.md` if it exists; otherwise apply the loaded skills only.
Read `spx/local/rust-tests.md` if it exists; otherwise apply the loaded skills only.

3. Invoke `/contextualizing` on the spec node under audit — `<SPEC_TREE_CONTEXT>` marker must be present before Gate 1

Gate 0 tool dependencies:

- `cargo fmt --check` and `cargo clippy` must be runnable (V1)
- `cargo llvm-cov` or the product's declared coverage tool (C1)

If any tool is unavailable, Gate 0 records a terminal finding and the audit aborts.

Repository-specific rules:

- Coverage audits use the repository's declared Rust coverage tool; do not infer coverage from imports or test names.
- When `spx` test files are included through `#[path = "..."]` modules in source files, coverage commands target Cargo test filters and source-file deltas.

</prerequisites>

<gate_0_deterministic>
Run deterministic checks before judging evidence.

<check id="F1" name="filename_policy">
List Rust test files under the target node:

```bash
rg --files <spec-node-path>/tests
```

Each file must match `<subject>.<evidence>.<level>[.<runner>].rs` where:

- `<evidence>` is one of: `scenario`, `mapping`, `conformance`, `property`, `compliance`
- `<level>` is one of: `l1`, `l2`, `l3`
- `<runner>` is optional (e.g., `tokio`, `actix`)

Fail Gate 0 for files that do not match this pattern, unless a governing product spec or decision declares a different Rust test filename convention and a repo-local overlay points to it. If governing product truth disables Level 3, fail `.l3.rs` files for that product.
</check>

<check id="R1" name="source_file_reads">
Scan target tests for source-file reads:

```bash
rg -n 'read_to_string|include_str!|std::fs::read|std::fs::read_to_string' <spec-node-path>/tests
```

Fail Gate 0 when a test reads files under `src/` or other production source paths. Fixture reads under `spx/.../tests/` proceed to Gate 1.
</check>

<check id="S1" name="skipped_tests">
Scan target tests for disabled evidence:

```bash
rg -n '#\[ignore\]|return;|panic!\("skip|todo!\(|unimplemented!\(' <spec-node-path>/tests
```

Fail Gate 0 for bare `#[ignore]` (no reason string), skip-by-early-return, `todo!`, or `unimplemented!` in test bodies.

The credentialed form `#[ignore = "..."]` is the declared Level 3 lane pattern from `/standardizing-rust-tests` and must **not** be failed in `.l3.rs` files. Check for misuse in non-Level-3 files:

```bash
rg -n '#\[ignore = ' <spec-node-path>/tests --glob '!*.l3.rs'
```

Any `#[ignore = "..."]` outside `.l3.rs` files is a misplaced credentialed annotation → fail Gate 0.
</check>

<check id="M1" name="generated_mock_signal">
Scan target tests for generated mock frameworks:

```bash
rg -n 'mockall|automock|faux|double::' <spec-node-path>/tests
```

Do not fail Gate 0 solely for this signal. Pass the finding to Gate 1 step `controlled_implementations`, where it is judged against `/testing` Stage 5 exceptions.
</check>

<check id="V1" name="rust_validation">
Run the repository validation sequence:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
```

Fail Gate 0 if any command fails. A non-compiling or failing test suite has no auditable evidence surface.
</check>

<check id="C1" name="coverage_tool">
Check coverage availability:

```bash
cargo llvm-cov --version
```

Fail Gate 0 when product instructions require measured coverage and this command fails. Otherwise record coverage tooling as unavailable and continue with the other evidence properties.
</check>

Gate 0 status:

| Condition                   | Status | Action                              |
| --------------------------- | ------ | ----------------------------------- |
| F1, R1, S1, V1, or C1 fails | FAIL   | Record findings, skip Gates 1 and 2 |
| M1 only                     | PASS   | Carry warnings into Gate 1          |
| all checks pass             | PASS   | Proceed to Gate 1                   |

</gate_0_deterministic>

<gate_1_assertion>
Runs only if Gate 0 is PASS. Entry point is the spec, not the test file.

For each assertion in the spec's Assertions section, execute steps 1-8 in order. First step failure rejects that assertion and moves to the next assertion.

<step name="challenge">
Challenge the assertion:

- Does the assertion derive from an ancestor PDR or ADR claim in `<SPEC_TREE_CONTEXT>`, or is it floating?
- Is the assertion type correct for the claim?
- Does it overlap with another assertion in the same node or parent?

Record challenge findings and continue unless the assertion type is invalid.
</step>

<step name="scope">
Decompose the assertion text into testable clauses.

Example:

| Assertion                                          | Clauses                                              |
| -------------------------------------------------- | ---------------------------------------------------- |
| "MUST exit 0 with no stdout for invalid hook JSON" | (1) invalid JSON input, (2) exit 0, (3) empty stdout |

The linked tests must exercise every clause with an assertion. A single assertion for a multi-clause claim is a `scope` finding.
</step>

<step name="evidence">
Match the Rust evidence method to the assertion type:

| Type        | Required Rust evidence                                                                   | Reject if                                    |
| ----------- | ---------------------------------------------------------------------------------------- | -------------------------------------------- |
| Scenario    | concrete inputs through the governed function, module, or binary                         | only existence or truthiness is checked      |
| Mapping     | table-driven cases, `rstest`, or looped fixtures with at least two meaningful cases      | one example stands in for a mapping          |
| Conformance | parser, schema, protocol harness, CLI contract, or `trybuild` for compile-time contracts | manual shape checks replace the validator    |
| Property    | `proptest` or `quickcheck` with meaningful generators and invariants                     | examples are wrapped in property syntax      |
| Compliance  | violating fixture, lint harness, or explicit `[review]` marker                           | no violating input or review evidence exists |

For property tests, inspect the generator domain. `Just`, one-value ranges, or tiny enumerations reduce the property to examples unless the spec explicitly declares a finite set.
</step>

<step name="controlled_implementations">
Judge controlled implementations against `/testing` exceptions:

| Exception                | Legitimate Rust pattern                                         |
| ------------------------ | --------------------------------------------------------------- |
| 1. Failure modes         | trait impl returning deterministic errors                       |
| 2. Interaction protocols | recorder struct capturing calls                                 |
| 3. Time/concurrency      | injected clock, paused runtime time, deterministic channels     |
| 4. Safety                | recorder or no-op implementation preserving the seam            |
| 5. Combinatorial cost    | configurable in-memory implementation with real-shaped behavior |
| 6. Observability         | capture struct for spans, logs, events, or serialized output    |
| 7. Contract probes       | local stub validated against the same contract schema           |

Generated mock frameworks, fake modules, or stubs that bypass the governed seam reject the assertion unless a Stage 5 exception applies and the real interface or protocol remains intact.
</step>

<step name="oracle">
Identify the source of every expected value.

Reject with an `oracle` finding when the expected value is derived from the module under test. Proceed when the expected value comes from an independent source: the spec, a public constant owned by a different module, an external protocol/schema, a fixture transcript, or a value hand-computed in the test.
</step>

<step name="harness_chain">
Trace every helper or harness import:

- imports from the `product_testing` workspace-member crate (e.g., `product_testing::harnesses::*`, `product_testing::generators::*`, `product_testing::fixtures::*`) — the canonical home per the product's `test-infrastructure` PDR
- non-canonical legacy locations that must be flagged as misplaced infrastructure: `super::tests`, `crate::test_support`, `tests/support.rs`, `tests/support/`, `#[cfg(test)] mod` helper modules inside a product crate
- helper functions inside `spx/.../tests/` — these are misplaced infrastructure unless they serve a single test file
- binary harnesses built around `assert_cmd::Command::cargo_bin(...)`

Open each harness. If the harness replaces the governed module instead of exercising it, reject with a `harness_chain` finding. Trace imports until the chain terminates at production code, fixture data, or framework/library code. If a harness lives in a non-canonical legacy location, surface an `extraction_target` finding pointing at the `product-testing` workspace-member crate.
</step>

<step name="four_properties">
Apply the Rust supplements:

- Coupling: direct, indirect, transitive, false, partial
- Falsifiability: concrete mutation named for every codebase path or binary contract
- Alignment: every assertion clause maps to exercised test behavior
- Coverage: `cargo llvm-cov` reports measured coverage for the governed source files

First property failure rejects the assertion.
</step>

<step name="coverage">
Run measured coverage for the governed source files.

Use `cargo llvm-cov --json --summary-only --output-path <path>` when file-level deltas are enough. Use `cargo llvm-cov --text --show-missing-lines --output-path <path>` when line-level evidence is needed.

For tests included through `#[path = "spx/.../tests/..."]` modules, gather:

1. Full-suite coverage:

   ```bash
   cargo llvm-cov --all-targets --json --summary-only --output-path /tmp/rust-coverage-all.json
   ```

2. Targeted coverage using the narrowest stable test-name filter or module filter:

   ```bash
   cargo llvm-cov test --all-targets --json --summary-only --output-path /tmp/rust-coverage-target.json -- <test-filter>
   ```

Report the governed file coverage from both reports. If the full suite is saturated, annotate `saturated`. If the targeted run does not execute the governed file, reject with `coverage`.
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
- repeated stdout/stderr/exit-code assertion helpers
- repeated tracing/debug capture setup

Each finding names the pattern, lists at least two occurrences with file and line, and proposes the canonical home in the `product-testing` workspace-member crate — `product_testing::harnesses::{name}` for shared resource mediators, `product_testing::generators::{name}` for input factories, or `product_testing::fixtures::{name}` for fixture-loading code.

Gate 2 status:

- PASS if no repeated setup pattern appears in two or more in-scope tests.
- FAIL if any repeated setup pattern appears in two or more in-scope tests.

</gate_2_architectural>

<rust_supplements>
Applied during Gate 1.

<supplement property="coupling">

| Category   | Definition                                                         | Verdict                       |
| ---------- | ------------------------------------------------------------------ | ----------------------------- |
| Direct     | Test calls the governed Rust function, type, module, or binary     | Proceed                       |
| Indirect   | Test calls a helper or harness that calls the governed path        | Proceed after harness tracing |
| Transitive | Test calls a public consumer of the governed path                  | Proceed if the level matches  |
| False      | Test imports the module but never calls assertion-relevant symbols | REJECT                        |
| Partial    | Test calls the right module with wrong inputs or wrong path        | REJECT                        |

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
Coverage passes when `cargo llvm-cov` shows the targeted run executes the governed source file or the full-suite report is saturated for that file and the other three properties pass.

Coverage notes do not rescue missing coupling, falsifiability, or alignment.
</supplement>

</rust_supplements>

<verdict_format>

Follow `<verdict_format>` in `/auditing-tests`. Gate 0 check IDs for Rust: F1, R1, S1, M1, V1, C1 (see `<gate_0_deterministic>` for the check-to-command mapping). Gate 2 extraction target: a module under the `product-testing` workspace-member crate, e.g. `product_testing::harnesses::{name}`, `product_testing::generators::{name}`, or `product_testing::fixtures::{name}` — never `tests/support/` or `crate::test_support`, which are legacy non-canonical locations.

</verdict_format>

<failure_modes>
**Failure 1: Treated binary tests as uncoupled**

Claude rejected a binary L2 test because it imported only `assert_cmd`, `predicates`, and fixture helpers. The test spawned the product binary and asserted stdout/exit behavior. Coupling existed through `cargo_bin("mybin")`.

How to avoid: Count `assert_cmd::Command::cargo_bin(...)` as direct coupling to the named binary contract.

**Failure 2: Approved source-text tests**

Claude accepted a test that read `src/rules.rs` and searched for a string. The implementation could satisfy the source-text assertion while runtime behavior was broken.

How to avoid: Gate 0 fails production source-file reads from tests.

**Failure 3: Hard-coded a product-specific Level 3 restriction**

Claude encoded one repository's no-Level-3 test policy in the reusable Rust standard. Other Rust projects can own real remote APIs, browser flows, deployed services, or shared environments where Level 3 evidence is appropriate.

How to avoid: Keep Level 3 in the generic Rust standard. Apply `.l3.rs` rejection only when a governing product spec or decision disables Level 3; a repo-local overlay can route to that declaration, but does not create it.
</failure_modes>

<success_criteria>

Audit is complete when:

- [ ] Gate 0 run: filename policy, source-file reads, skipped tests, mock signals, Rust validation, coverage tool
- [ ] Gate 1 complete: every assertion evaluated through all 8 steps (if Gate 0 PASS)
- [ ] Gate 2 complete: in-scope tests scanned for repeated setup patterns (if Gate 1 PASS)
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has gate, step, and specific detail
- [ ] For REJECT: "how tests could pass while assertions fail" explained

</success_criteria>
