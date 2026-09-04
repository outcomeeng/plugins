---
name: audit-go-tests
description: >-
  Go test-evidence audit methodology — judges the Go tests in scope against
  the spec-tree and Go-specific evidence properties.
model: sonnet
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Skill
---

<objective>
A verdict on Go test evidence — APPROVED, or REJECTED with each finding naming the assertion or evidence artifact, the failed evidence property, and the evidence gap.
</objective>

<constraints>

This audit is read-only. Produce a verdict over test evidence; never edit tests, production code, specs, fixtures, harnesses, generators, or project configuration.

</constraints>

<audit_workflow>

<prerequisites>

Invoke the `go:go-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `go:go-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `spec-tree:audit-tests` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `spec-tree:test` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Read local overlay files — each routes skill behavior to the product's governing specs and decisions; overlays supplement skills and do not supersede them:

Read `spx/local/go.md` and `spx/local/go-tests.md` when they exist; otherwise apply the loaded skills only.

Invoke `/contextualize` on the spec node under audit — `<SPEC_TREE_CONTEXT>` marker must be present before Gate 1.

This audit runs no deterministic verification — no `gofmt`, `go vet`, `go test`, `go test -cover`, or any other project command. Spend the whole audit reading the evidence chain.

</prerequisites>

<audit_scope>

Begin with the current governing spec and its current evidence links. A deleted Go test or test-infrastructure path belongs to this audit only when a current `[test]` assertion still links it or a current linked test still imports it. When the current spec carries no `[test]` link to the deleted path and no current evidence chain references it, classify the retired path as outside current Go test-evidence scope and return `NOT_APPLICABLE` for that path. Never demand restoration of deterministic evidence solely because the base revision or changeset deletion names the retired path. When a current `[test]` assertion still links a missing path, report missing evidence against that current assertion.

Use read-only `git diff` only when the supplied changeset scope requires confirming whether an evidence path was deleted. Run no other shell command from this concern skill.

</audit_scope>

<structural_reading>
Before judging evidence, read the in-scope test files for structural defects — by reading, never by running the project's gate. These are reading observations folded into Gate 1, not a separate deterministic gate:

- **Filename policy** — each file MUST match `<subject>.<evidence>.<level>[.<runner>]_test.go` (`<evidence>` ∈ scenario/mapping/conformance/property/compliance, `<level>` ∈ l1/l2/l3). The project's validation owns this convention; note a mismatch as a `filename_policy` finding carrying property `alignment` from the base `/audit-tests` enum — a filename that misdeclares its evidence type or level misaligns the file with the assertion it claims to evidence — and do not re-validate it.
- **Build constraint** — an `l2` or `l3` file whose first line is not the matching `//go:build l2` or `//go:build l3` constraint runs in the default lane against infrastructure it declares absent there; note it as a `filename_policy` finding carrying property `alignment`.
- **Test-file bindings** — apply the base `/audit-tests` semantic binding screen before coupling. A `:=`, `var`, `const`, table-row literal, closure parameter, or property-generated parameter is valid when it only receives an actual result, source-owned contract, generated value, harness observation, callback input, resource handle, or fixture path and introduces no data or policy. Emit a finding carrying property `declarations` and the base `/audit-tests` rule label the choice matches — `test-owned configuration` for runner settings, seed policy, retries, setup policy, or lifecycle policy, and `test-owned data` for hand-picked data, boundary bags, expected outputs, fixture contents, generator domains, or a table of author-invented rows presented as a mapping. Keep the two labels distinct. Keep every predicate and `testing.T` failure call in the linked test function or subtest; a binding, closure, or `t.Helper()`-marked function that moves a predicate or failure call out carries property `predicate-ownership`, rule `assertion-seam`, remediation target `test-file`.
- **Source-file reads** — a test that reads production `.go` files (`os.ReadFile`, `embed` of a source path, `go/parser` over production code) asserts on source text, not behavior → prose-coupling REJECT in Gate 1 step `four_properties`. Inert fixture data is read by path from `internal/testinfra/fixtures/testdata/`; co-located `spx/.../tests/` remains the home of typed assertion files. When a loaded overlay points to a governing product spec or decision that explicitly amends this contract, follow that declaration; the overlay does not redefine fixture placement itself.
- **Disabled evidence** — a bare `t.Skip()` (no reason), skip-by-early-return, `t.SkipNow()`, or `panic("TODO")` in a test body provides no evidence → REJECT in Gate 1 carrying property `coverage` from the base `/audit-tests` enum, since execution never reaches the assertion-relevant path. A reasoned `t.Skip("...")` is acceptable in an `.l3_test.go` file only when a loaded product spec or decision declares that credentialed Level 3 lane and the suite declares that evidence optional; a missing mandatory dependency fails through `t.Fatal`, so a skip on it rejects. Outside `.l3_test.go`, reasoned skip is misplaced.
- **Generated mock signal** — `gomock`, `mockery`, `moq`, `mock.Mock`, or a reassigned package-level function variable in a test is read and judged in Gate 1 step `controlled_implementations` against `/test` Stage 5 exceptions.

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
Match the Go evidence method to the assertion type:

| Type        | Required Go evidence                                                                           | Reject if                                 |
| ----------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Scenario    | concrete inputs through the governed function, package, or binary                              | only existence or truthiness is checked   |
| Mapping     | table-driven `t.Run` cases iterating a source-owned enumeration with at least two members      | one example stands in for a mapping       |
| Conformance | parser, schema, protocol harness, CLI contract, or toolchain oracle for compile-time contracts | manual shape checks replace the validator |
| Property    | `rapid` through the property harness with meaningful generators and invariants                 | examples are wrapped in property syntax   |
| Compliance  | violating fixture or analyzer harness for a current `[test]` link                              | no violating input or rule oracle exists  |

For property tests, inspect the generator domain. `rapid.Just`, one-value ranges, or tiny enumerations reduce the property to examples unless the spec explicitly declares a finite set.

An assertion tagged `[audit]` carries no assertion type and is outside Go test-evidence scope. Skip it rather than treating the marker as test evidence.
</step>

<step name="controlled_implementations">
Judge controlled implementations against `/test` exceptions:

| Exception                | Legitimate Go pattern                                                    |
| ------------------------ | ------------------------------------------------------------------------ |
| 1. Failure modes         | interface implementation returning deterministic errors                  |
| 2. Interaction protocols | recording implementation capturing calls                                 |
| 3. Time/concurrency      | injected clock, deterministic channels, `synctest` where available       |
| 4. Safety                | recording or no-op implementation preserving the seam                    |
| 5. Combinatorial cost    | configurable in-memory implementation with real-shaped behavior          |
| 6. Observability         | capture implementation for `slog` handlers, events, or serialized output |
| 7. Contract probes       | `httptest` stub validated against the same contract schema               |

Generated mock frameworks, reassigned package-level function variables, or stubs that bypass the governed seam reject the assertion unless a Stage 5 exception applies and the real interface or protocol remains intact. Such a rejection carries property `falsifiability` from the base `/audit-tests` enum — a severed seam means no production mutation can break the test.
</step>

<step name="oracle">
Identify the source of every expected value.

Reject with an `oracle` finding carrying property `oracle-independence` and remediation target `independent-oracle` from the base `/audit-tests` enum when the expected value is derived from the package under test. This is distinct from `falsifiability`: an expected result computed by the same path that produces the actual result passes even when both are wrong. Proceed when the expected value comes from an independent source: the spec, an exported constant owned by a different package, an external protocol/schema, a fixture transcript, or a value hand-computed in the test.
</step>

<step name="harness_chain">
Trace every test-infrastructure import:

- imports from `<module>/internal/testinfra/harnesses`, `<module>/internal/testinfra/generators`, and `<module>/internal/testinfra/fixtures` — the canonical home per the product's `test-infrastructure` PDR
- non-canonical legacy locations that must be flagged as misplaced infrastructure: an in-package `testutil` or `testhelpers` package, an `export_test.go` that hands a harness or fixture to a test, a `testdata/` directory outside `internal/testinfra/fixtures/`, or a `tests/` subdirectory carrying non-test Go files
- local functions inside `spx/.../tests/` — these are misplaced infrastructure when they own setup, reusable cases, fixture handling, generator selection, harness behavior, diagnostics, or source vocabulary
- binary harnesses that build or resolve the product binary and hand it to `os/exec`

Open each harness. If the harness replaces the governed package instead of exercising it, reject with a `harness_chain` finding. Trace imports until the chain terminates at production code, fixture data, or framework/library code. If a harness lives in a non-canonical legacy location, surface an `extraction_target` finding pointing at `internal/testinfra/`.
</step>

<step name="four_properties">
Apply the Go supplements:

- Coupling: classified from the full `<supplement property="coupling">` taxonomy below — every category it names, never a subset
- Falsifiability: concrete mutation named for every codebase path or binary contract
- Alignment: every assertion clause maps to exercised test behavior
- Coverage: read whether the test drives execution into the governed source path; no coverage tool is run

First property failure rejects the assertion.
</step>

<step name="coverage">
Establish coverage by reading, never by running `go test -cover` or any other coverage tool. This audit runs no deterministic verification.

Trace, by reading, whether the test drives execution into the governed source path:

1. Read the governed source the assertion names and identify the assertion-relevant functions, branches, and lines.
2. Read the test and follow what it calls into that source — directly, through a harness, or through the harness-provided binary for a binary contract.
3. Judge whether the test's execution reaches the assertion-relevant path.

A test that compiles against the governed package but never drives execution into the assertion-relevant path → REJECT with `coverage`; name the path the test fails to reach, traced from the code. When the assertion-relevant path is trivially total, annotate `saturated`.
</step>

Gate 1 status:

- PASS if every assertion verdict is PASS.
- FAIL if any assertion verdict is REJECT.

</gate_1_assertion>

<gate_2_architectural>
Runs only if Gate 1 is PASS. Scan in-scope tests for repeated setup patterns that belong in shared test infrastructure.

Trigger: two or more in-scope tests share any of these patterns:

- identical product-binary build or resolution setup
- repeated hook JSON builders
- repeated transcript fixture writers
- repeated tempdir/home-directory scaffolding beyond a bare `t.TempDir()`
- repeated stdout/stderr/exit-code comparison functions
- repeated `slog` or debug capture setup

Each finding names the pattern, lists at least two occurrences with file and line, and proposes the canonical home under `internal/testinfra/` — `harnesses` for shared resource mediators, `generators` for input factories, or `fixtures` for fixture-resolving code.

Gate 2 status:

- PASS if no repeated setup pattern appears in two or more in-scope tests.
- FAIL if any repeated setup pattern appears in two or more in-scope tests.

</gate_2_architectural>

<go_supplements>
Applied during Gate 1.

<supplement property="coupling">

This supplement specializes each category of the coupling taxonomy `/audit-tests` owns to Go paths. Classify from the table below rather than a subset of it; every category the canonical taxonomy names appears here, so a category missing from this table would silently narrow the verdict.

| Category           | Definition                                                                                                                        | Verdict                                         |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Direct             | Test calls the governed Go function, type, package, or binary                                                                     | Proceed                                         |
| Indirect           | Test calls test infrastructure that calls the governed path                                                                       | Proceed after harness tracing                   |
| Transitive         | Test calls a public consumer of the governed path                                                                                 | Proceed if the level matches                    |
| Laundered indirect | Calls an `internal/testinfra` package that exists only to expose hardcoded values back to the test                                | REJECT — laundering                             |
| False              | Test imports the package but never calls assertion-relevant symbols                                                               | REJECT                                          |
| Partial            | Test calls the right package with wrong inputs or wrong path                                                                      | REJECT                                          |
| None               | Test imports only `testing` and third-party modules, with zero product-package coupling                                           | REJECT — tautology                              |
| Severed            | Test or harness replaces the governed behavior with a mock, fake, generated mock, reassigned function variable, or bypassing stub | REJECT — coupling severed                       |
| Prose-coupling     | Reads an authored prose/doc body and asserts its content, including through a harness constant or an infrastructure reader        | REJECT — couples to authored text, not behavior |

Framework/library imports such as `testing`, `context`, `os/exec`, `net/http/httptest`, `pgregory.net/rapid`, and `github.com/google/go-cmp/cmp` do not count as coupling by themselves. A harness-provided product binary run through `os/exec` counts as coupling to the named binary contract. The Prose-coupling row is the table-side form of the source-file read that `<structural_reading>` screens for; both reach the same REJECT.

</supplement>

<supplement property="falsifiability">
For each codebase path, name a concrete mutation that would fail the test.

Example:

```text
Package: internal/install
Mutation: Install writes block hook entries under PreToolUse instead of Stop
Impact: install-tooling scenario test comparing settings JSON fails
```

Reject when no mutation can be named, when generated mocks replace the governed behavior, or when golden files only capture hand-built fixtures.
</supplement>

<supplement property="alignment">
Alignment passes when every assertion clause is exercised by at least one assertion and the test's evidence method matches the assertion type.

Reject when the test covers a nearby behavior, collapses clauses, uses one example for a mapping, or tests runtime behavior for a compile-time contract.
</supplement>

<supplement property="coverage">
Coverage passes when reading the test against the governed source shows the test drives execution into the assertion-relevant path, or that path is trivially total (`saturated`) and the other three properties pass. No coverage tool is run — this audit establishes coverage by reading.

Coverage notes do not rescue missing coupling, falsifiability, or alignment.
</supplement>

</go_supplements>

</audit_workflow>

<verdict_format>

This skill composes the base `/audit-tests` verdict: the row names (`gate-1-assertion`, `gate-2-architectural`) and the JSON schema are defined in its `<verdict_format>` and are not redefined here. This skill contributes Go-specific finding detail into those rows. The audit emits no `gate-0-deterministic` row — it runs no deterministic verification; the structural reading observations from `<structural_reading>` are folded into the Gate 1 (`gate-1-assertion`) findings. Gate 2 extraction target: a package under `internal/testinfra/`, e.g. `internal/testinfra/harnesses`, `internal/testinfra/generators`, or `internal/testinfra/fixtures` — never an in-package `testutil` or a `testdata/` directory outside the fixtures package, which are legacy non-canonical locations.

When `<audit_scope>` finds that a retired path has no current `[test]` assertion or current evidence-chain owner, emit this alternate concern result instead of the inherited rows:

```json
{
  "status": "NOT_APPLICABLE",
  "subjects": ["<retired-repository-relative-path>"],
  "explanation": "No current [test] assertion or evidence chain references the retired path."
}
```

Emit this shape only when every supplied subject is outside current Go test-evidence scope. A current broken `[test]` link remains applicable and produces the inherited `REJECTED` verdict.

</verdict_format>

<success_criteria>

The Go test verdict is sound when:

- Every applicable rule was judged: each in-scope assertion received every Gate 1 step and the `<structural_reading>` observations (filename, build constraint, source-reads, disabled evidence, mock signals); Gate 2 was judged when Gate 1 passed and omitted only when Gate 1 rejected the evidence.
- Every deleted Go test or test-infrastructure path was classified from current spec links and current evidence chains, with retired evidence returned as `NOT_APPLICABLE` and current broken `[test]` links reported as missing evidence.
- Applicable scope states an overall `APPROVED` / `REJECTED` with no assertion left unevaluated; a composition-only retired-path scope emits the defined `NOT_APPLICABLE` result.
- Each `REJECT` finding is falsifiable: it names the assertion or evidence artifact, the failed property, the gate and step, and how the test could pass while the assertion is unfulfilled.
- The same test node yields the same verdict regardless of run order (reproducible).

</success_criteria>
