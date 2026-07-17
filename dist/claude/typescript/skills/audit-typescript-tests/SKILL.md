---
name: audit-typescript-tests
description: >-
  TypeScript test-evidence audit methodology — judges the TypeScript tests in
  scope against the spec-tree and TypeScript-specific evidence properties.
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Skill
---

<objective>

A verdict on TypeScript test evidence — APPROVED, or REJECTED with each finding naming the assertion or evidence artifact, the failed evidence property, and the evidence gap.

</objective>

<constraints>

This audit is read-only. Produce a verdict over test evidence; never edit tests, production code, specs, fixtures, harnesses, generators, or project configuration.

</constraints>

<audit_workflow>

<prerequisites>

Invoke the `typescript:typescript-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `typescript:typescript-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `spec-tree:audit-tests` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `spec-tree:test` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Read local overlay files — each routes skill behavior to the product's governing specs and decisions; overlays supplement skills and do not supersede them:

Read `spx/local/typescript.md` if it exists; otherwise apply the loaded skills only.
Read `spx/local/typescript-tests.md` if it exists; otherwise apply the loaded skills only.

Invoke `/contextualize` on the spec node under audit — `<SPEC_TREE_CONTEXT>` marker must be present before Gate 1.

This audit runs no deterministic verification — no `spx validation literal`, test, type-check, or coverage command. Cross-file literal laundering is judged by reading.

</prerequisites>

<audit_scope>

Begin with the current governing spec and its current evidence links. A deleted TypeScript test or test-infrastructure path belongs to this audit only when a current `[test]` assertion still links it or a current linked test still imports it. When the current spec carries no `[test]` link to the deleted path and no current evidence chain references it, classify the retired path as outside current TypeScript test-evidence scope and return `NOT_APPLICABLE` for that path. Never demand restoration of deterministic evidence solely because the base revision or changeset deletion names the retired path. When a current `[test]` assertion still links a missing path, report missing evidence against that current assertion.

Use read-only `git diff` only when the supplied changeset scope requires confirming whether an evidence path was deleted. Run no other shell command from this concern skill.

</audit_scope>

<structural_reading>

Before Gate 1, read each in-scope test filename. Canonical TypeScript evidence files match `<subject>.<evidence>.<level>[.<runner>].test.ts`, where `<evidence>` is `scenario`, `mapping`, `conformance`, `property`, or `compliance` and `<level>` is `l1`, `l2`, or `l3`. Reject `.unit.test.ts`, `.integration.test.ts`, `.e2e.test.ts`, and `.spec.ts` as a Gate 1 `filename_policy` finding. Fold this reading observation into Gate 1 rather than running a naming-convention command.

</structural_reading>

<literal_laundering_by_reading>

Cross-file literal laundering is judged by reading the test's literals against their sources, not by running `spx validation literal`. The two laundering shapes the validator surfaces are read in Gate 1:

| Shape                                                          | What to read                                                                                                    | Judged in                      |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| src-reuse — a test literal also present in a production module | Read the literal at its test callsite and search the production module the assertion governs for the same value | Gate 1 step `mocks` / `oracle` |
| test-dupe — a literal duplicated across test files             | Read the literal at its callsite and the sibling test files in scope for the same value                         | Gate 1 step `four_properties`  |

A test literal that re-declares a production-owned value instead of importing it is laundered coupling → REJECT. Fixture-as-module and generator-laundering shapes are read in Gate 1 step `harness_chain`.

</literal_laundering_by_reading>

<test_file_declarations>

Executed TypeScript test files are typed assertion files. Before judging the assertion method, read the test file for `const`, `let`, `var`, framework fixture parameters, property-generated parameters, and local `function` declarations. Reject every `const`, `let`, or `var` declaration as test-file state; reject fixture and generated-case parameters as test-file bindings. Name the right owner for the value it binds: source contract, `@testing/harnesses/*`, `@testing/generators/*`, inert whole-payload fixture, or eval case data. Reject local `function` declarations when they own setup policy, reusable cases, fixture paths, generator choices, harness handles, diagnostics, credential loading, or source-owned singleton shapes.

Do not use naming style or declaration shape as a proxy. `MAPPING_RUNS`, `mappingRuns`, `runs`, and `function mappingRuns()` are the same failure when the declaration owns a run count. The finding code is `test_owned_declaration`; the message names the right owner: source contract, `@testing/harnesses/*`, `@testing/generators/*`, inert fixture path, or eval case data.

Property-based tests must route the property assertion through a harness or wrapper that owns seed selection, `numRuns`, and replay diagnostics. A TypeScript property test is rejected when failure output would not include the seed and replay path, or when the test file owns the seed/run-count itself.

</test_file_declarations>

<gate_1_assertion>

Entry point is the spec, not the test file.

For each assertion in the spec's Assertions section, execute steps 1–8 in order. First step failure rejects that assertion and moves to the next.

<step name="challenge">

**Step 1 — Challenge the assertion**

- Does the assertion derive from a PDR/ADR claim in the node's ancestors (from `<SPEC_TREE_CONTEXT>`), or is it floating?
- Is the assertion type (Scenario / Mapping / Conformance / Property / Compliance) the right one for the claim? A behavioral rule is not a Scenario.
- Does the assertion overlap with another assertion in the same node or a parent (redundancy)?

Record any issue as a `challenge` finding and continue to step 2 — challenge issues do not short-circuit the remaining steps unless the assertion type is provably wrong (which invalidates step 4).

</step>

<step name="scope">

**Step 2 — Scope coverage: enumerate clauses**

Decompose the assertion text into testable clauses. Examples:

| Assertion                                                             | Clauses                                                     |
| --------------------------------------------------------------------- | ----------------------------------------------------------- |
| "MUST reject expired requests with HTTP 410 and an error-schema body" | (1) reject, (2) HTTP 410, (3) body schema conforms          |
| "Outputs OKLCH colors meeting WCAG AA at AA-Large text weights"       | (1) OKLCH format, (2) WCAG AA contrast, (3) AA-Large sizing |

The test must exercise every clause with at least one `expect`. Single `expect` for a multi-clause assertion → REJECT this assertion with a `scope` finding.

</step>

<step name="test_file_declarations">

**Step 3 — Test-file declarations**

Apply `<test_file_declarations>` to each linked TypeScript test file before inspecting the property/mapping/scenario method. Any `const`, `let`, `var`, framework fixture parameter, or property-generated parameter is a `test_owned_declaration` finding. Any local `function` declaration that owns data, configuration, setup, reusable cases, fixtures, generators, harness behavior, diagnostics, credentials, or source vocabulary is also a `test_owned_declaration` finding. For property assertions, missing seed/replay reporting is a `missing_property_seed_reporting` finding.

</step>

<step name="evidence">

**Step 4 — Assertion type and method**

| Type        | Required TypeScript pattern                                                                                                             | REJECT if                                               |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Scenario    | Concrete non-trivial inputs; assertions on assertion-relevant state                                                                     | Only `toBeDefined` / `toBeTruthy` / `expect.any`        |
| Mapping     | `it.each` / `describe.each` / `test.each` over ≥2 cases                                                                                 | Single example for a claimed mapping                    |
| Conformance | Schema validator (`zod.parse`, `ajv`, JSON Schema)                                                                                      | Manual `toEqual({...hardcoded...})` with no validator   |
| Property    | `assertProperty(namedProperty())` — meaningful arbitrary, invariant body, seed, and replay output live in the imported property harness | `fc.constant`, body `return true`, only "doesn't throw" |
| Compliance  | `[test]`: exercises a violating fixture; `[audit]`: skip this audit                                                                     | `[test]` with no violating fixture                      |

Inspect the arbitrary's domain for Property assertions. `fc.constant(...)`, `fc.oneof(fc.constant(a), fc.constant(b))` with 2–3 hardcoded values, or narrow ranges like `fc.nat(1)` reduce the property to examples → REJECT.

If a generator's only behavior is `fc.constant(...)` for a source-owned singleton, REJECT the generator and require a source-owned constructor or registry import instead. A constant branch inside a larger meaningful arbitrary is allowed only when it expands boundary coverage and source-owned values still come from source APIs.

For Property assertions, also verify the property call goes through the seed-reporting harness or wrapper required by `<test_file_declarations>`. A meaningful arbitrary without reproducible failure output is still incomplete evidence.

</step>

<step name="mocks">

**Step 5 — Scan for mocks and judge against `/test` exceptions**

For each `vi.mock`, `vi.spyOn`, `vi.fn`, or similar mock pattern in this test file:

1. Identify which `/test` exception (1–7) applies:

   | Exception                | Legitimate TypeScript pattern              |
   | ------------------------ | ------------------------------------------ |
   | 1. Failure modes         | Class implementing interface; throws       |
   | 2. Interaction protocols | Class with call-recording array            |
   | 3. Time/concurrency      | `vi.useFakeTimers()` or injected clock     |
   | 4. Safety                | Class that records but does not execute    |
   | 5. Combinatorial cost    | Configurable class mirroring real behavior |
   | 6. Observability         | Class capturing request details            |
   | 7. Contract testing      | Stub validated against a schema            |

2. No exception applies → coupling severed → REJECT the assertion with a `mocks` finding.
3. Passthrough partial mocks — `vi.mock(m, async () => ({ ...await vi.importActual(m), x: vi.fn() }))` — preserve coupling for every export except `x`. REJECT only if the assertion targets `x`.
4. `vi.spyOn(obj, "m")` without `.mockReturnValue()` / `.mockImplementation(() => ...)` observes only — coupling preserved.

</step>

<step name="oracle">

**Step 6 — Oracle independence**

Identify the source of each `expect`'s expected value.

- REJECT with an `oracle` finding if the expected value is derived from the module under test. Example: `expect(encode(decode(x))).toBe(x)` where both `encode` and `decode` live in the audited module — a shared bug (both strip trailing whitespace) passes the test.
- Proceed if the expected value comes from a source the module did not produce: a canonical constant imported from a different module, an external standard (schema, RFC, spec document), or a value hand-computed in the test independently of the module.

The test proves correctness against an independent oracle, not self-consistency.

</step>

<step name="harness_chain">

**Step 7 — Harness chain tracing**

For every import from `@testing/harnesses/*`, `@testing/fixtures/*`, or `@testing/generators/*`:

1. Open the imported test-infrastructure file.
2. Search for `vi.mock`, `vi.doMock`, `vi.hoisted` with mock, `vi.stubGlobal`, `vi.stubEnv`, `jest.mock`, `msw.setupServer`, `nock(...)` — any mocking pattern — inside the harness module body or its setup path.
3. If the import targets `@testing/fixtures/*`, REJECT with a `fixture_import` finding. Fixtures are inert files: tests may read, copy, or pass fixture paths, but executed tests must not import fixture modules or consume fixture exports.
4. If the harness mocks the module the assertion is about → coupling severed through the harness → REJECT with a `harness_chain` finding.
5. If a generator's only behavior is returning arbitrary literals or `fc.constant(...)` wrappers that duplicate source-owned vocabulary or singleton shapes, REJECT with a `generator_laundering` finding.
6. If a property harness or wrapper owns `numRuns` or seed policy, verify it reports seed and replay details on failure; otherwise REJECT with `missing_property_seed_reporting`.
7. If the test-infrastructure file imports another test-infrastructure file, trace one level at a time until the chain terminates at a non-test module.

If an executed test imports a local test-adjacent module that carries harness, generator, or fixture behavior outside the canonical `@testing/` path, REJECT with a `noncanonical_test_infrastructure` finding. Spec-tree `tests/` directories contain typed assertion files only.

The test's own imports look clean when the mock lives in a harness, the hardcoded value lives in a generator, or a fixture masquerades as a module. Always open the test-infrastructure module. When recording audit findings, cite the stable step name `harness_chain` and finding code, not numbered checklist item positions.

</step>

<step name="four_properties">

**Step 8 — 4-property evidence check**

Apply the supplements in `<typescript_supplements>` for each property:

- **Coupling** — executable coupling categories (Direct / Indirect / Transitive / False / Partial / Severed), barrel resolution, type-only import handling.
- **Falsifiability** — incorporates step 5 (mocks) and step 6 (oracle) judgments, plus snapshot rules.
- **Alignment** — incorporates step 2 (clause enumeration) and step 4 (assertion type).
- **Coverage** — read whether the test drives execution into the assertion-relevant path; no coverage tooling is run.

First property failure at this step → REJECT the assertion; move to the next.

</step>

Gate 1 status:

- PASS if every assertion's per-assertion verdict is PASS.
- FAIL if any assertion's per-assertion verdict is REJECT.

</gate_1_assertion>

<gate_2_architectural>

Runs only if Gate 1 is PASS. Scans in-scope test files for repeated setup patterns that belong in shared harnesses.

Trigger: two or more in-scope tests sharing any of these patterns:

- `await page.goto("/<same-path>")` across tests
- Server / dev-server startup
- `vi.useFakeTimers(...)` with the same initial date
- `fetch` / HTTP-client configuration identical across tests
- Fixture-dir or temp-dir creation
- Browser-context setup
- Test-user creation with the same role or id shape

Each finding names the pattern, lists ≥2 occurrences (file + line), and proposes an extraction target under `testing/harnesses/<name>.ts`. One-occurrence patterns are not DRY violations.

Gate 2 status:

- PASS if no pattern appears in two or more in-scope tests.
- FAIL if any pattern appears in two or more.

</gate_2_architectural>

<typescript_supplements>

Applied at step 8 of Gate 1.

<supplement property="coupling">

Restate the executable coupling categories this supplement applies to TypeScript imports — do not delegate to `/audit-tests`:

| Category   | Definition                                                                       | Verdict                           |
| ---------- | -------------------------------------------------------------------------------- | --------------------------------- |
| Direct     | Test imports the module under test                                               | Proceed                           |
| Indirect   | Test imports a harness wrapping the module                                       | Proceed — step 7 traced the chain |
| Transitive | Test imports a consumer of the module                                            | Proceed — verify test level       |
| False      | Imports the module but never calls assertion-relevant symbols                    | REJECT                            |
| Partial    | Calls functions on wrong inputs or wrong code paths                              | REJECT                            |
| Severed    | Imports the module and replaces behavior with `vi.mock`, stubbed spies, or fakes | REJECT                            |

**Type-only imports do not count.**

```typescript
import type { ThemeColor } from "../src/theme"; // erased at runtime
```

All codebase imports are `import type` → tautology → REJECT.

**Barrel re-exports mask false coupling.** Resolve:

- `export * from "./x"` — trace to source file
- `export { y } from "./x"` — resolve re-exported symbol
- `export * as ns from "./x"` — trace namespace resolution
- `package.json` `"exports"` field — apply export-map resolution

If the test imports from a barrel and the assertion-relevant symbol is a sibling never called → False coupling → REJECT.

**Deep relative imports** (`../../../../testing/`) are a tracing cue. They signal the test may be reaching a harness that wraps a different module. Step 7 (`harness_chain`) traces the chain regardless.

</supplement>

<supplement property="falsifiability">

Apply step 5 (mocks) and step 6 (oracle).

For each codebase import, name a concrete mutation to the imported module that would cause this test to fail. Record the mutation in the assertion's finding detail:

```text
Module: src/config-parser.ts
Mutation: parseConfig returns empty object instead of parsed sections
Impact: expect(result.section.key).toBe("value") fails
```

Cannot name a mutation → unfalsifiable → REJECT.

**Snapshot rules:**

- `toMatchSnapshot()` / `toMatchInlineSnapshot()` satisfy falsifiability only if the snapshot content expresses the assertion's claim. A snapshot of `expect.any(Object)` is a tautology.
- Snapshots auto-updated in CI (`--update`, `-u`, update-on-CI flags) sever falsifiability — the test cannot fail.
- `expect(x).toMatchObject({...})` is falsifiable only on listed fields; extra fields are ignored by design.
- Sole assertion is `expect(x).toBeDefined()` / `.toBeTruthy()` / `.not.toBeNull()` / `expect.any(...)` → REJECT (trivial).

</supplement>

<supplement property="alignment">

Apply step 2 (clauses) and step 4 (assertion type).

Alignment passes when:

1. Every clause in the assertion is exercised by at least one `expect`.
2. The test's evidence method matches the assertion type.
3. The test's inputs exercise the domain the assertion claims to cover.

Alignment fails when clauses are collapsed, evidence method mismatches the type, or inputs are trivial literals that do not express the claimed domain.

</supplement>

<supplement property="coverage">

Establish coverage by reading, never by running `vitest --coverage` or any other coverage tool. This audit runs no deterministic verification.

Trace, by reading, whether the test drives execution into the assertion-relevant code path:

1. Read the production module the assertion governs and identify the assertion-relevant functions, branches, and lines.
2. Read the test and follow what it calls into that module.
3. Judge whether the test's execution reaches the assertion-relevant path.

Interpret the trace:

- Reaches the assertion-relevant path — the test exercises the behavior the assertion claims, pass.
- Imports the module but never drives execution into the assertion-relevant path → REJECT; name the specific path the test fails to reach, traced from the code.
- The assertion-relevant path is trivially total — annotate `saturated` in the finding detail.

Coverage here is execution breadth (does the test reach the assertion-relevant lines), traced by reading — never a measured percentage and never an unbacked "probably covers." A property-based test with a broader input domain adds evidence a line count would not.

</supplement>

</typescript_supplements>

</audit_workflow>

<verdict_format>

This skill composes the base `/audit-tests` verdict: the row names (`gate-1-assertion`, `gate-2-architectural`) and the JSON schema are defined in its `<verdict_format>` and are not redefined here. This skill contributes TypeScript-specific finding detail into those rows. Literal-laundering finding IDs: L3 (src-reuse), L4 (test-dupe) — judged by reading per `<literal_laundering_by_reading>`, not by running a validator. Gate 2 extraction target: `testing/harnesses/{name}.ts`.

When `<audit_scope>` finds that a retired path has no current `[test]` assertion or current evidence-chain owner, emit this alternate concern result instead of the inherited rows:

```json
{
  "status": "NOT_APPLICABLE",
  "subjects": ["<retired-repository-relative-path>"],
  "explanation": "No current [test] assertion or evidence chain references the retired path."
}
```

Emit this shape only when every supplied subject is outside current TypeScript test-evidence scope. A current broken `[test]` link remains applicable and produces the inherited `REJECTED` verdict.

</verdict_format>

<failure_modes>

**Failure 1 — Contradiction resolution followed operational guide over canonical standard**

What happened: The standard in `/typescript-test-standards` rejects `.e2e.test.ts`, `.unit.test.ts`, `.integration.test.ts`. A prior version of this skill said filename conventions were "deferred as standards issues." Both rules were visible. Claude followed the audit skill because it was the operational guide for *this task*, resolving the contradiction by authority-of-specificity. Five files with legacy suffixes shipped approved.

Why it failed: Claude treated a narrower operational prompt as authority over the canonical standards reference.

How to avoid: `/typescript-test-standards` defines the filename convention. `<structural_reading>` rejects every legacy suffix before Gate 1; the deferral carveout no longer exists.

**Failure 2 — Harness coupling camouflage: the mock lives in the harness**

What happened: A test imported `posthogHarness` from `@testing/harnesses/posthog` and used it across scenarios. No `vi.mock` appeared in the test, so Claude classified coupling as indirect. The harness file contained `vi.mock("posthog-js", () => ({ ...fake... }))` at module load, severing coupling for every consumer.

Why it failed: The audit stopped at the test file and never inspected the imported harness that replaced production behavior.

How to avoid: Gate 1 step 7 opens every imported harness file and traces mock calls one level deep. The test's imports look clean when the mock lives in a harness. Always open the harness.

**Failure 3 — Oracle inside the module under test: self-consistency passes shared bugs**

What happened: Claude approved `expect(encode(decode(value))).toBe(value)` as a roundtrip property. Both functions lived in the audited module, and a shared trailing-whitespace bug made the roundtrip hold for every input.

Why it failed: The module under test produced both the observed value and its oracle, allowing shared defects to cancel out.

How to avoid: Gate 1 step 6 requires the expected value to derive from a source the module under test did not produce — a canonical constant imported from a different module, an external standard, or a value hand-computed in the test.

**Failure 4 — Partial alignment through clause collapse**

What happened: The spec required rejection, HTTP 410, and an error-schema body. Claude marked `expect(handler(expiredRequest).rejected).toBe(true)` aligned even though it covered only the first clause.

Why it failed: Claude collapsed a multi-clause assertion into its first observable outcome.

How to avoid: Gate 1 step 2 enumerates clauses from the assertion text *before* matching to test `expect`s. A single `expect` for a three-clause assertion is REJECT, not "close enough."

**Failure 5 — Property-shaped example disguised by fast-check syntax**

What happened: Claude approved `fc.assert(fc.property(fc.constant({ user: "admin", role: "root" }), (x) => validate(x).ok))` because the file and framework looked property-shaped. The arbitrary held one value.

Why it failed: Framework syntax and filename classification replaced inspection of the generated domain.

How to avoid: Gate 1 step 4 inspects the arbitrary's domain. `fc.constant`, small `fc.oneof` over hardcoded values, or narrow ranges like `fc.nat(1)` reduce the property to examples → REJECT the Property assertion.

**Failure 6 — Literal laundering moved into generator modules**

What happened: Claude approved a literal-free test importing `arbitraryAbsentConfig()` from `@testing/generators/config`. The generator returned `fc.constant({ kind: CONFIG_FILE_READ_KIND.ABSENT })`, adding no variability, shrinking, or stronger oracle.

Why it failed: The audit checked literal location rather than whether the generator added a variable evidence domain.

How to avoid: Gate 1 step 7 opens generator modules. Generators whose only behavior is returning a source-owned singleton shape are REJECT. Require a source-owned constructor or registry import.

**Failure 7 — Fixture imported as executable test code**

What happened: An executed test imported `VALID_CASES` from `@testing/fixtures/rule-cases.ts`. The runner compiled the fixture and consumed its exports as shared test-owned data.

Why it failed: File placement was mistaken for fixture semantics even though executed test code imported its exports.

How to avoid: Gate 1 step 7 rejects imports from `@testing/fixtures/*`. Fixture files may be read from disk, copied into temp projects, or passed by path to the code under test. They are never imported by executed test code.

**Failure 8 — Runner configuration hidden in a renamed test variable**

What happened: Validation rejected `const MAPPING_RUNS = 12`, and Claude renamed it to `mappingRuns`. The property run count remained in the executed test file and the audit approved it.

Why it failed: A naming convention was used as a proxy for ownership, allowing configuration to remain in the assertion file.

How to avoid: Gate 1 step 3 rejects test-owned declarations by ownership, not casing. Property run counts, seeds, replay output, and diagnostics belong in a seed-reporting harness or wrapper.

**Failure 9 — Property failure could not be replayed**

What happened: A property used a meaningful `arbitraryPath()`, but no harness owned the seed and failure output carried no seed or replay command. Claude approved the incomplete debugging evidence.

Why it failed: Domain quality was judged without checking reproducibility of a generated failure.

How to avoid: Gate 1 steps 3 and 7 require seed-reporting property infrastructure. Approve property evidence only when failure output exposes the seed and replay path.

</failure_modes>

<success_criteria>

The TypeScript test verdict is sound when:

- Every applicable rule was judged: each in-scope test received the filename-policy structural reading, and each in-scope assertion received all eight Gate 1 steps — test-file declaration ownership, coupling, falsifiability, alignment, coverage (by reading), oracle independence, harness-chain tracing, and literal laundering; Gate 2 was judged when Gate 1 passed and omitted only when Gate 1 rejected the evidence.
- Every deleted TypeScript test or test-infrastructure path was classified from current spec links and current evidence chains, with retired evidence returned as `NOT_APPLICABLE` and current broken `[test]` links reported as missing evidence.
- Applicable scope states an overall `APPROVED` / `REJECTED` with no assertion left unevaluated; a composition-only retired-path scope emits the defined `NOT_APPLICABLE` result.
- Each `REJECT` finding is falsifiable: it names the assertion or evidence artifact, the failed property, the gate and step, and how the test could pass while the assertion is unfulfilled.
- The same test node yields the same verdict regardless of run order (reproducible).

</success_criteria>
