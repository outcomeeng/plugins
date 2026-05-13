<overview>

Detailed evidence model for test auditing. Read this before auditing any test file.

Four properties define test evidence: coupling, falsifiability, alignment, coverage. This reference provides the taxonomy, verification procedures, and concrete examples for each.

</overview>

<coupling_taxonomy>

Six coupling categories with definitions and code examples.

**Direct coupling** — Test imports the module under test and calls its functions directly.

```typescript
import { parseConfig } from "../src/config-parser";

it("parses nested sections", () => {
  const result = parseConfig(input);
  expect(result.section.key).toBe("value");
});
```

**Indirect coupling** — Test imports a test harness that wraps the module. Coupling exists but is mediated.

```typescript
import { ConfigTestHarness } from "./harness";

it("parses nested sections", () => {
  const harness = new ConfigTestHarness();
  const result = harness.parseAndValidate(input);
  expect(result.section.key).toBe("value");
});
```

When indirect coupling is found, verify the harness itself has direct coupling to the module. If the harness is also a tautology, the coupling chain is broken.

**Transitive coupling** — Test imports something that depends on the module under test, but does not import the module directly.

```typescript
import { Application } from "../src/app";

it("loads configuration", () => {
  const app = new Application();
  expect(app.config.section.key).toBe("value");
});
```

May be legitimate for integration tests. Verify the test level matches the assertion level.

**False coupling** — Test imports the module but never exercises the code path relevant to the assertion.

```typescript
import { parseConfig, validateConfig } from "../src/config-parser";

it("validates config structure", () => {
  // Assertion is about PARSING but test only validates
  const result = validateConfig(hardcodedConfig);
  expect(result.valid).toBe(true);
  // parseConfig is imported but never called
});
```

The import exists syntactically but the assertion-relevant function is never called.

**Partial coupling** — Test exercises some code paths but not the ones the assertion specifies.

```typescript
import { parseConfig } from "../src/config-parser";

it("parses flat config", () => {
  // Assertion is about NESTED SECTIONS but test covers flat only
  const result = parseConfig("key=value");
  expect(result.key).toBe("value");
});
```

**No coupling** — Test imports only its test framework. A tautology.

```typescript
import { describe, expect, it } from "vitest";

const GRAY = { L: 0.98, C: 0.003, H: 85 };

it("has correct chroma", () => {
  expect(GRAY.C).toBe(0.003); // Tests a constant it declared itself
});
```

This test passes if every file in the codebase is deleted.

</coupling_taxonomy>

<coupling_verification>

**Procedure:**

1. Read import statements at the top of the test file
2. Classify each: framework, library, or codebase
3. Zero codebase imports → REJECT (no coupling)
4. For each codebase import:
   - Is the imported module the one the assertion is about? → Direct
   - Is it a test harness? → Indirect (follow the chain — verify harness has real coupling)
   - Is it a consumer of the module? → Transitive (verify test level)
5. Check whether the assertion-relevant function/method is actually called:
   - Imported but never called → False coupling
   - Called but on wrong inputs or code paths → Partial coupling

</coupling_verification>

<falsifiability_model>

**Mutation analysis**

For each codebase import with genuine coupling, name a concrete mutation:

```text
Module: src/config-parser.ts
Mutation: parseConfig returns empty object instead of parsed sections
Impact: "parses nested sections" fails — expect(result.section.key) throws
```

The mutation must be:

- **Concrete** — a specific change, not "if something breaks"
- **Relevant** — changes the behavior the assertion claims to verify
- **Detectable** — the test's assertions would actually catch it

If you cannot name such a mutation: the test is unfalsifiable.

**Mocking severs coupling**

A test that imports a module then replaces it with a mock:

```typescript
import { database } from "../src/database";
vi.mock("../src/database", () => ({ query: vi.fn().mockResolvedValue([]) }));
```

The real `database.query` never runs. Any change to the real module — schema changes, query bugs, connection failures — is invisible. Import + mock = coupling severed.

**Exception cross-reference with `/testing` methodology**

Test doubles used under the 7 legitimate exception cases are not "coupling severed." The auditor must identify which exception applies:

| Exception                | Double type           | Why coupling is maintained                         |
| ------------------------ | --------------------- | -------------------------------------------------- |
| 1. Failure modes         | Stub returning errors | Tests error handling of real integration           |
| 2. Interaction protocols | Spy recording calls   | Tests call sequence against real interface         |
| 3. Time/concurrency      | Fake clock            | Tests timing logic with real code                  |
| 4. Safety                | Stub that records     | Tests intent without destructive side effects      |
| 5. Combinatorial cost    | Configurable fake     | Tests breadth with fake that mirrors real behavior |
| 6. Observability         | Spy recording details | Tests request details the real system hides        |
| 7. Contract testing      | Contract stub         | Tests serialization/parsing against real schema    |

For each test double found:

1. Identify which exception applies (must be one of the 7)
2. Verify the double type matches the exception (see table)
3. Verify the test actually tests what the exception enables
4. If no exception applies → coupling is severed → REJECT

</falsifiability_model>

<alignment_verification>

**Procedure:**

Read the spec assertion and the test's expect/assert statements side by side.

1. Does the test exercise the exact behavior the assertion describes?
   - Assertion says "Given X, when Y, then Z"
   - Test must: set up X, perform Y, assert Z

2. Could the assertion be unfulfilled while the test passes?
   - If yes → misaligned

3. Is the test strategy appropriate for the assertion type?
   - Property assertion → must use property-based framework
   - Mapping assertion → must be parameterized over the input set
   - Conformance assertion → must use tool/schema validation

**Common misalignment patterns:**

| Assertion says                   | Test does                   | Finding                              |
| -------------------------------- | --------------------------- | ------------------------------------ |
| "Handles nested sections"        | Tests flat config only      | Partial behavior — misaligned        |
| "All themes meet threshold"      | Tests one theme             | Incomplete coverage — misaligned     |
| "Serialization is deterministic" | Tests one input             | Needs property test — wrong strategy |
| "API returns 404 for missing"    | Tests 200 for existing      | Wrong scenario — misaligned          |
| "Parser rejects invalid input"   | Asserts no exception thrown | Inverted assertion — misaligned      |

</alignment_verification>

<coverage_protocol>

**Step-by-step:**

1. **Find the coverage command.** Read the product's CLAUDE.md, package.json, pyproject.toml, or Justfile.

2. **Identify assertion-relevant source files.** From the spec assertion and test imports, determine which source files the test should cover.

3. **Run baseline** — coverage excluding the test file under audit:

   ```bash
   # TypeScript (vitest)
   pnpm vitest run --coverage --exclude='path/to/test-under-audit.test.ts'

   # Python (pytest)
   just run test --cov=src --cov-report=term -- --ignore=path/to/test_under_audit.py
   ```

4. **Run with test** — coverage including the test file:

   ```bash
   # TypeScript (vitest)
   pnpm vitest run --coverage 'path/to/test-under-audit.test.ts'

   # Python (pytest)
   just run test --cov=src --cov-report=term path/to/test_under_audit.py
   ```

5. **Compare deltas** for each assertion-relevant source file.

6. **Report actual numbers:**

   ```text
   Baseline: src/config-parser.ts — 43.2%
   With test: src/config-parser.ts — 67.8%
   Delta: +24.6% — new coverage ✓
   ```

**Edge cases:**

- **No coverage tooling**: Note as finding. Do not REJECT solely for this — the other three properties still apply.
- **New module with 0% baseline**: Any coverage from the test is positive delta.
- **Saturated coverage**: Baseline shows 100% line + branch coverage on assertion-relevant files. Zero delta is expected — there are no uncovered paths to hit. Coverage measures execution breadth, not assertion strength. A test that exercises fully-covered code with a stronger strategy (e.g., Hypothesis/fast-check over example-based) or broader input domain adds evidentiary value through its assertions, not through additional execution. The other three properties carry the evidence. Annotate as `saturated` in the verdict table.
- **Shared coverage**: Multiple tests may cover same paths. If baseline is < 100%, a test with zero delta should still be hitting uncovered branches. If baseline is 100%, see saturated coverage above.

</coverage_protocol>
