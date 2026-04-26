---
name: auditing-typescript-tests
allowed-tools: Read, Grep, Glob, Bash
description: >-
  ALWAYS invoke this skill when auditing tests for TypeScript or after writing or editing tests.
  NEVER use auditing-typescript for test code.
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript/SKILL.md" || echo "standardizing-typescript not found — invoke skill typescript:standardizing-typescript now"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript-tests/SKILL.md" || echo "standardizing-typescript-tests not found — invoke skill typescript:standardizing-typescript-tests now"`

!`cat "${CLAUDE_SKILL_DIR}/../../../spec-tree/skills/testing/SKILL.md" || echo "testing not found — invoke skill spec-tree:testing now"`

!`cat "${CLAUDE_SKILL_DIR}/../../../spec-tree/skills/auditing-tests/SKILL.md" || echo "auditing-tests not found — invoke skill spec-tree:auditing-tests now"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. Skill `typescript:standardizing-typescript`
2. Skill `typescript:standardizing-typescript-tests`
3. Skill `spec-tree:testing`
4. Skill `spec-tree:auditing-tests`

</codex_fallback>

<objective>

TypeScript test audit. Two gates in strict sequence, fail-closed:

1. **Gate 1 — Assertion audit**: per-assertion LLM audit starting from the spec — challenge, scope, evidence, mocks, oracle, harness chain, 4-property evidence check. A `spx validation literal` cross-file check runs before Gate 1 as a non-blocking preliminary; findings feed into step `mocks` and step `four_properties`.
2. **Gate 2 — Architectural DRY**: LLM scan for repeated cross-file setup patterns.

A gate failure skips the next gate.

</objective>

<prerequisites>

1. Invoking 4 skills: Already done above.
2. Read local overlay files, they supersede any skills and are loaded below:

!`cat "spx/local/typescript.md" || echo "spx/local/typescript.md not found; apply skills only."`
!`cat "spx/local/typescript-tests.md" || echo "spx/local/typescript-tests.md not found; apply skills only."`

<codex_fallback>
If you see `cat` commands above, shell injection did not run (Codex or similar environment). Look for project-specific overlay files:

1. Read `spx/local/typescript.md` if it exists. It supersedes any skills.
2. Read `spx/local/typescript-tests.md` if it exists. It supersedes any skills.

</codex_fallback>

3. Invoke `/contextualizing` on the spec node under audit — `<SPEC_TREE_CONTEXT>` marker must be present before Gate 1

Optional preliminary tool: `spx validation literal` (ships with the `spx` CLI). If unavailable, proceed without cross-file literal findings.

</prerequisites>

<preliminary_check>

If `spx validation literal` is available, run it before Gate 1:

```bash
spx validation literal --files <spec-node-path>/tests/**/*.test.ts --json
```

Findings feed into Gate 1:

| check_id | Source                                                                      | Hands to                               |
| -------- | --------------------------------------------------------------------------- | -------------------------------------- |
| L3       | `spx validation literal` — src-reuse (literal appears in production module) | Gate 1 step `mocks` / `falsifiability` |
| L4       | `spx validation literal` — test-dupe (literal duplicated across test files) | Gate 1 step `four_properties`          |

If `spx validation literal` is unavailable, proceed to Gate 1 without these findings.

</preliminary_check>

<gate_1_assertion>

Entry point is the spec, not the test file.

For each assertion in the spec's Assertions section, execute steps 1–7 in order. First step failure rejects that assertion and moves to the next.

<step name="challenge">

**Step 1 — Challenge the assertion**

- Does the assertion derive from a PDR/ADR claim in the node's ancestors (from `<SPEC_TREE_CONTEXT>`), or is it floating?
- Is the assertion type (Scenario / Mapping / Conformance / Property / Compliance) the right one for the claim? A behavioral rule is not a Scenario.
- Does the assertion overlap with another assertion in the same node or a parent (redundancy)?

Record any issue as a `challenge` finding and continue to step 2 — challenge issues do not short-circuit the remaining steps unless the assertion type is provably wrong (which invalidates step 3).

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

<step name="evidence">

**Step 3 — Evidence type and method**

| Type        | Required TypeScript pattern                                          | REJECT if                                               |
| ----------- | -------------------------------------------------------------------- | ------------------------------------------------------- |
| Scenario    | Concrete non-trivial inputs; assertions on assertion-relevant state  | Only `toBeDefined` / `toBeTruthy` / `expect.any`        |
| Mapping     | `it.each` / `describe.each` / `test.each` over ≥2 cases              | Single example for a claimed mapping                    |
| Conformance | Schema validator (`zod.parse`, `ajv`, JSON Schema)                   | Manual `toEqual({...hardcoded...})` with no validator   |
| Property    | `fc.assert(fc.property(arb, pred))` — meaningful arbitrary and body  | `fc.constant`, body `return true`, only "doesn't throw" |
| Compliance  | `[test]`: exercises a violating fixture; `[review]`: skip this audit | `[test]` with no violating fixture                      |

Inspect the arbitrary's domain for Property assertions. `fc.constant(...)`, `fc.oneof(fc.constant(a), fc.constant(b))` with 2–3 hardcoded values, or narrow ranges like `fc.nat(1)` reduce the property to examples → REJECT.

</step>

<step name="mocks">

**Step 4 — Scan for mocks and judge against `/testing` exceptions**

For each `vi.mock`, `vi.spyOn`, `vi.fn`, or similar mock pattern in this test file:

1. Identify which `/testing` exception (1–7) applies:

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

**Step 5 — Oracle independence**

Identify the source of each `expect`'s expected value.

- REJECT with an `oracle` finding if the expected value is derived from the module under test. Example: `expect(encode(decode(x))).toBe(x)` where both `encode` and `decode` live in the audited module — a shared bug (both strip trailing whitespace) passes the test.
- Proceed if the expected value comes from a source the module did not produce: a canonical constant imported from a different module, an external standard (schema, RFC, spec document), or a value hand-computed in the test independently of the module.

The test proves correctness against an independent oracle, not self-consistency.

</step>

<step name="harness_chain">

**Step 6 — Harness chain tracing**

For every import from `@testing/harnesses/*`, `@testing/fixtures/*`, or `./helpers`:

1. Open the harness file.
2. Search for `vi.mock`, `vi.doMock`, `vi.hoisted` with mock, `vi.stubGlobal`, `vi.stubEnv`, `jest.mock`, `msw.setupServer`, `nock(...)` — any mocking pattern — inside the harness module body or its setup path.
3. If the harness mocks the module the assertion is about → coupling severed through the harness → REJECT with a `harness_chain` finding.
4. If the harness imports another harness, trace one level at a time until the chain terminates at a non-test module.

The test's own imports look clean when the mock lives in a harness. Always open the harness.

</step>

<step name="four_properties">

**Step 7 — 4-property evidence check**

Apply the supplements in `<typescript_supplements>` for each property:

- **Coupling** — 5-category taxonomy (Direct / Indirect / Transitive / False / Partial), barrel resolution, type-only import handling.
- **Falsifiability** — incorporates step 4 (mocks) and step 5 (oracle) judgments, plus snapshot rules.
- **Alignment** — incorporates step 2 (clause enumeration) and step 3 (evidence type).
- **Coverage** — package-manager detection, baseline vs. with-test deltas, saturation annotation.

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

Applied at step 7 of Gate 1.

<supplement property="coupling">

Restate the foundation's 5-category taxonomy — do not delegate to `/auditing-tests`:

| Category   | Definition                                                    | Verdict                           |
| ---------- | ------------------------------------------------------------- | --------------------------------- |
| Direct     | Test imports the module under test                            | Proceed                           |
| Indirect   | Test imports a harness wrapping the module                    | Proceed — step 6 traced the chain |
| Transitive | Test imports a consumer of the module                         | Proceed — verify test level       |
| False      | Imports the module but never calls assertion-relevant symbols | REJECT                            |
| Partial    | Calls functions on wrong inputs or wrong code paths           | REJECT                            |

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

**Deep relative imports** (`../../../../testing/`) are not themselves a coupling failure, but they signal the test may be reaching a harness that wraps a different module. Step 6 traces the chain regardless.

</supplement>

<supplement property="falsifiability">

Apply step 4 (mocks) and step 5 (oracle).

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

Apply step 2 (clauses) and step 3 (evidence type).

Alignment passes when:

1. Every clause in the assertion is exercised by at least one `expect`.
2. The test's evidence method matches the assertion type.
3. The test's inputs exercise the domain the assertion claims to cover.

Alignment fails when clauses are collapsed, evidence method mismatches the type, or inputs are trivial literals that do not express the claimed domain.

</supplement>

<supplement property="coverage">

Detect the package manager:

1. Read `package.json` `"packageManager"` field — use it if present.
2. Else detect from the lockfile in the project root: `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `bun.lockb` → bun, `package-lock.json` → npm.
3. Else read the project's CLAUDE.md or `justfile` for the canonical test command.

Run coverage twice.

Baseline (excluding the test under audit):

```bash
<pm> vitest run --coverage --exclude='<test-under-audit>'
```

With the test:

```bash
<pm> vitest run --coverage '<test-under-audit>'
```

Projects may use c8, istanbul, or v8 coverage providers — check `vitest.config.ts` `test.coverage.provider`.

Report actual deltas per source file:

```text
Baseline: src/config-parser.ts — 43.2%
With test: src/config-parser.ts — 67.8%
Delta: +24.6%
```

Interpret:

- Positive delta — new coverage, pass.
- Zero delta, baseline < 100% — no coverage increase → REJECT.
- Zero delta, baseline = 100% — saturated; annotate `saturated` in the finding detail.

Coverage measures execution breadth, not assertion strength. A property-based test with a broader input domain adds evidence coverage cannot measure.

If the project has no coverage tooling: record as a coverage note, do not REJECT solely for this.

</supplement>

</typescript_supplements>

<verdict_format>

Follow `<verdict_format>` in `/auditing-tests`. Preliminary check IDs: L3, L4 (from `spx validation literal` — see `<preliminary_check>`). Gate 2 extraction target: `testing/harnesses/{name}.ts`.

</verdict_format>

<failure_modes>

**Failure 1 — Contradiction resolution followed operational guide over canonical standard**

The standard in `/standardizing-typescript-tests` rejects `.e2e.test.ts`, `.unit.test.ts`, `.integration.test.ts`. A prior version of this skill said filename conventions were "deferred as standards issues." Both rules were visible. Claude followed the audit skill because it was the operational guide for *this task*, resolving the contradiction by authority-of-specificity. Five files with legacy suffixes shipped approved.

How to avoid: `/standardizing-typescript-tests` defines the filename convention. Gate 1 step 1 challenges the assertion type; the deferral carveout no longer exists.

**Failure 2 — Harness coupling camouflage: the mock lives in the harness**

Test imports `import { posthogHarness } from "@testing/harnesses/posthog"` and uses it across scenarios. No `vi.mock` in the test. Claude classified coupling as indirect (harness-wrapped). The harness file itself contained `vi.mock("posthog-js", () => ({ ...fake... }))` at module load. Every test using the harness had coupling severed at the harness level — invisible from the test file alone.

How to avoid: Gate 1 step 6 opens every imported harness file and traces mock calls one level deep. The test's imports look clean when the mock lives in a harness. Always open the harness.

**Failure 3 — Oracle inside the module under test: self-consistency passes shared bugs**

Test: `expect(encode(decode(value))).toBe(value)` — textbook roundtrip property, `fc.assert`-wrapped, meets alignment for a Property assertion on a serializer. Claude approved. Both `encode` and `decode` lived in the module being audited. A shared bug — both functions stripped trailing whitespace — made the roundtrip hold for every input. The oracle was the module's own output; the test verified self-consistency, not correctness.

How to avoid: Gate 1 step 5 requires the expected value to derive from a source the module under test did not produce — a canonical constant imported from a different module, an external standard, or a value hand-computed in the test.

**Failure 4 — Partial alignment through clause collapse**

Spec: "MUST reject expired requests with HTTP 410 and a body conforming to the error schema." Test: `expect(handler(expiredRequest).rejected).toBe(true)`. Claude saw the reject behavior tested and marked alignment as pass. The assertion had three clauses (reject, status 410, body schema). The test covered one. Two uncovered clauses could fail in production while the test passes.

How to avoid: Gate 1 step 2 enumerates clauses from the assertion text *before* matching to test `expect`s. A single `expect` for a three-clause assertion is REJECT, not "close enough."

**Failure 5 — Property-shaped example disguised by fast-check syntax**

Test: `fc.assert(fc.property(fc.constant({ user: "admin", role: "root" }), (x) => validate(x).ok))`. Wrapped in `fc.assert`, structurally a property test, filename `.property.l1.test.ts`. Claude saw the property framework and approved. The arbitrary was `fc.constant` — a single value. The test ran one example and called itself a property.

How to avoid: Gate 1 step 3 inspects the arbitrary's domain. `fc.constant`, small `fc.oneof` over hardcoded values, or narrow ranges like `fc.nat(1)` reduce the property to examples → REJECT the Property assertion.

</failure_modes>

<success_criteria>

Audit is complete when:

- [ ] Preliminary check: `spx validation literal` run (or skipped if unavailable)
- [ ] Gate 1 complete: every assertion evaluated through all 7 steps (if preliminary check complete or skipped)
- [ ] Gate 2 complete: in-scope tests scanned for repeated setup patterns (if Gate 1 PASS)
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has gate, step, and specific detail
- [ ] For REJECT: "how tests could pass while assertions fail" explained

</success_criteria>
