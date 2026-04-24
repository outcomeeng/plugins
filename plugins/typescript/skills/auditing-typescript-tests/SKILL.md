---
name: auditing-typescript-tests
allowed-tools: Read, Grep, Glob, Bash
description: >-
  ALWAYS invoke this skill when auditing tests for TypeScript or after writing or editing tests.
  NEVER use auditing-typescript for test code.
---

<objective>

TypeScript test audit. Three gates in strict sequence, fail-closed:

1. **Gate 0 — Deterministic**: ESLint (per-file) and `spx validation literal` (cross-file) check filenames, magic literals, harness placement, BDD anti-patterns, and mock-API presence. Claude does not judge these rules — Gate 0 output is routed into the verdict template verbatim.
2. **Gate 1 — Assertion audit**: per-assertion LLM audit starting from the spec — challenge, scope, evidence, mocks, oracle, harness chain, 4-property evidence check.
3. **Gate 2 — Architectural DRY**: LLM scan for repeated cross-file setup patterns.

A gate failure skips every later gate. Output is a structured XML verdict validated by `spx validation audit-verdict`. The verdict template is the deliverable; `spx validation audit-verdict` exit code 0 is the sole success criterion.

</objective>

<prerequisites>

Before Gate 0, load in order:

1. `/standardizing-typescript` — TypeScript code standards
2. `/standardizing-typescript-tests` — test standards, including the canonical filename pattern
3. `/auditing-tests` — the 4-property evidence model
4. `spx/local/typescript.md` and `spx/local/typescript-tests.md` at the repository root (if present)
5. `/contextualizing` on the spec node under audit — `<SPEC_TREE_CONTEXT>` marker must be present before Gate 1

Gate 0 depends on two tools:

- ESLint must be installed in the consumer repo, and the standards config at `${CLAUDE_SKILL_DIR}/../standardizing-typescript-tests/eslint-rules/eslint.audit.config.ts` must be reachable. The rules and config are owned by `/standardizing-typescript-tests` — the audit invokes them, does not define them.
- `spx validation literal` must be available on the path (ships with the `spx` CLI; the cross-file literal-reuse detection step).

The skill's success criterion depends on `spx validation audit-verdict` — this subcommand must be available before the skill can complete.

If any tool is unavailable, Gate 0 records a terminal finding and the audit aborts.

</prerequisites>

<gate_0_deterministic>

Run two tools and merge their findings.

**Per-file checks (ESLint)**

```bash
pnpm eslint \
  --config ${CLAUDE_SKILL_DIR}/../standardizing-typescript-tests/eslint-rules/eslint.audit.config.ts \
  --format json \
  <spec-node-path>/tests/
```

ESLint rules applied (rule id → check):

| Rule id                               | Check                                                                  | Severity |
| ------------------------------------- | ---------------------------------------------------------------------- | -------- |
| `audit/no-test-filename-violations`   | F1-F5: canonical `<subject>.<evidence>.<level>[.<runner>].test.ts`     | error    |
| `audit/no-literal-test-strings`       | L1: string literals outside descriptive callsites / policy exceptions  | error    |
| `audit/no-literal-test-numbers`       | L2: numeric literals outside `{-1, 0, 1, 2}` and named precision slots | error    |
| `audit/no-ad-hoc-test-constants`      | module-scope const backed by literal data                              | error    |
| `audit/no-bdd-try-catch-anti-pattern` | `expect()` inside try/catch with no re-throw                           | error    |
| `no-restricted-imports`               | H2: deep relative imports into `testing/`                              | error    |
| `audit/no-mock-api`                   | M1-M2: mock / stub / network-replacement call sites                    | warn     |

The rules themselves are the standard — coding agents see them via `/standardizing-typescript-tests` while writing tests, so Gate 0 cannot surface any rule the author did not already have access to. Consumer override: if `eslint.audit.config.ts` exists at the repo root, the skill uses that instead of the standardizing default. Consumers extend the default config to add project-specific exceptions.

**Cross-file checks (`spx validation literal`)**

```bash
spx validation literal --files <spec-node-path>/tests/**/*.test.ts --json
```

Detects `src-reuse` (a literal in a test also appears in the production module) and `test-dupe` (a literal duplicated across test files, absent from the production module). Both indicate the literal should be imported from production or extracted to a shared fixture.

**Exit-code composition:**

| ESLint exit | spx exit | Gate 0 status | Action                                                                                   |
| ----------- | -------- | ------------- | ---------------------------------------------------------------------------------------- |
| 0           | 0        | PASS          | Proceed to Gate 1. `audit/no-mock-api` warnings are handed to Gate 1 step `mocks`.       |
| 1           | any      | FAIL          | Record ESLint errors in the verdict; include spx findings if also 1; skip Gates 1 and 2. |
| 0           | 1        | FAIL          | Record spx findings in the verdict; skip Gates 1 and 2.                                  |
| 2           | any      | FAIL          | Terminal "eslint unavailable". Skip Gates 1 and 2.                                       |
| any         | 2        | FAIL          | Terminal "spx validation literal unavailable". Skip Gates 1 and 2.                       |

A missing tool is equivalent to exit 2 — the audit cannot proceed without both checks.

**NEVER apply the deterministic checks manually in the skill body.** Filename shape, mock-API presence, magic literals, harness placement, and cross-file literal reuse are regex-able or tool-decidable; they belong to the tools. Route the tool output into the verdict template verbatim — do not reproduce the checks manually.

Verdict `check_id` mapping (for the `<finding>`-level `<check_id>` element):

| check_id | Source                                               |
| -------- | ---------------------------------------------------- |
| F1–F5    | `audit/no-test-filename-violations`                  |
| L1       | `audit/no-literal-test-strings`                      |
| L2       | `audit/no-literal-test-numbers`                      |
| L3       | `spx validation literal` — src-reuse                 |
| L4       | `spx validation literal` — test-dupe                 |
| M1       | `audit/no-mock-api` (vitest/jest patterns — warning) |
| M2       | `audit/no-mock-api` (network libraries — warning)    |
| H2       | `no-restricted-imports`                              |
| B1       | `audit/no-bdd-try-catch-anti-pattern`                |
| C1       | `audit/no-ad-hoc-test-constants`                     |

</gate_0_deterministic>

<gate_1_assertion>

Runs only if Gate 0 is PASS. Entry point is the spec, not the test file.

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

**Step 4 — Judge Gate 0-detected mocks against `/testing` exceptions**

For each `M1`/`M2` finding in this test file:

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
2. Search for `vi.mock`, `vi.doMock`, `vi.hoisted` with mock, `vi.stubGlobal`, `vi.stubEnv`, `jest.mock`, `msw.setupServer`, `nock(...)` — any pattern Gate 0 would flag — inside the harness module body or its setup path.
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

<verdict_template>

The skill output is exactly this XML structure. `spx validation audit-verdict` parses and checks it.

```xml
<audit_verdict>
  <header>
    <spec_node>{spec-node-path}</spec_node>
    <verdict>{APPROVED|REJECT}</verdict>
    <timestamp>{iso-8601}</timestamp>
  </header>
  <gates>
    <gate id="0" name="deterministic" status="{PASS|FAIL|SKIPPED}">
      <skipped_reason>{if SKIPPED}</skipped_reason>
      <findings count="{n}">
        <finding>
          <file>{path}</file>
          <line>{n}</line>
          <check_id>{F1-F5|L1-L4|M1-M2|H2|B1|C1}</check_id>
          <message>{validator message}</message>
        </finding>
      </findings>
    </gate>
    <gate id="1" name="assertion" status="{PASS|FAIL|SKIPPED}">
      <skipped_reason>{if SKIPPED}</skipped_reason>
      <assertions>
        <assertion index="{n}">
          <spec_file>{path}</spec_file>
          <assertion_text>{exact quote from spec}</assertion_text>
          <assertion_type>{Scenario|Mapping|Conformance|Property|Compliance}</assertion_type>
          <test_file>{path}</test_file>
          <verdict>{PASS|REJECT}</verdict>
          <findings>
            <finding>
              <step>{challenge|scope|evidence|mocks|oracle|harness_chain|coupling|falsifiability|alignment|coverage}</step>
              <detail>{specific failure}</detail>
            </finding>
          </findings>
        </assertion>
      </assertions>
    </gate>
    <gate id="2" name="architectural" status="{PASS|FAIL|SKIPPED}">
      <skipped_reason>{if SKIPPED}</skipped_reason>
      <findings>
        <finding>
          <pattern>{e.g., vi.useFakeTimers with initial date 2025-01-01}</pattern>
          <occurrences>
            <occurrence><file>{path}</file><line>{n}</line></occurrence>
            <occurrence><file>{path}</file><line>{n}</line></occurrence>
          </occurrences>
          <extraction_target>testing/harnesses/{name}.ts</extraction_target>
        </finding>
      </findings>
    </gate>
  </gates>
</audit_verdict>
```

Template rules enforced by the validator:

- `SKIPPED` requires a non-empty `<skipped_reason>` (for example, "Gate 0 failed", "Gate 1 failed").
- `FAIL` requires `<findings count="N">` with at least one `<finding>` child; the `count` attribute must equal the child count.
- `APPROVED` is valid only when all three gates are `PASS`. Any `FAIL` → `REJECT`. Terminal Gate 0 validator-unavailable → `REJECT`.

After emitting the verdict, invoke the template validator:

```bash
spx validation audit-verdict <verdict-xml-path>
```

Exit 0 → audit is complete. Exit 1 → verdict is malformed; fix before reporting.

</verdict_template>

<failure_modes>

**Failure 1 — Contradiction resolution followed operational guide over canonical standard**

The standard in `/standardizing-typescript-tests` rejects `.e2e.test.ts`, `.unit.test.ts`, `.integration.test.ts`. A prior version of this skill said filename conventions were "deferred as standards issues." Both rules were visible. Claude followed the audit skill because it was the operational guide for *this task*, resolving the contradiction by authority-of-specificity. Five files with legacy suffixes shipped approved.

How to avoid: Gate 0 runs the standard's rules directly. The deferral carveout no longer exists; there is no contradiction to resolve.

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

The audit is complete when `spx validation audit-verdict` returns exit code 0 for the emitted verdict XML.

The validator checks structure completeness, status validity, findings consistency, and verdict coherence. No other checklist applies.

</success_criteria>
