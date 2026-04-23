---
name: auditing-typescript-tests
description: >-
  ALWAYS invoke this skill when auditing tests for TypeScript or after writing or editing tests.
  NEVER use auditing-typescript for test code.
---

<objective>

TypeScript-specific test audit. Extends `/auditing-tests` with TypeScript supplements for each evidence property: coupling, falsifiability, alignment, coverage.

Read `/auditing-tests` first — it defines the 4-property evidence model and ordered workflow. This skill adds only what is TypeScript-specific.

Before running the audit, load `/standardizing-typescript`, then `/standardizing-typescript-tests`, then check `spx/local/typescript.md` and `spx/local/typescript-tests.md` at the repository root in that order.

</objective>

<quick_start>

**PREREQUISITES**:

1. Read `/standardizing-typescript`
2. Read `/standardizing-typescript-tests`
3. Check `spx/local/typescript.md` and `spx/local/typescript-tests.md` at the repository root in that order
4. Read `/auditing-tests` and its evidence model before auditing

5. Run the `/auditing-tests` workflow: load context → map assertions → audit coupling → falsifiability → alignment → coverage → verdict
6. At each property step, apply the TypeScript supplement below
7. First property failure = REJECT (skip remaining properties for that assertion)

Use the filename conventions from `/standardizing-typescript-tests` for assertion-to-test mapping.

</quick_start>

<essential_principles>

Follow the four principles from `/auditing-tests`: **COUPLING FIRST**, **RUN COVERAGE DON'T GUESS**, **NO MECHANICAL DETECTION**, **BINARY VERDICT**.

**NO CODE QUALITY CHECKS.**

Type safety (`as any`, `@ts-ignore`), filename conventions, test-data organization, and import style are standards concerns enforced by `/standardizing-typescript`, `/standardizing-typescript-tests`, tsc strict mode, and ESLint. The auditor evaluates evidence quality only. A test with perfect TypeScript quality and zero evidentiary value must be REJECTED. A test with sloppy types but genuine evidence of spec fulfillment is not rejected by this audit.

</essential_principles>

<typescript_supplements>

Apply these at the corresponding step of the `/auditing-tests` workflow.

<supplement property="coupling">

**TypeScript import classification:**

| Import pattern                                           | Classification                       |
| -------------------------------------------------------- | ------------------------------------ |
| `import { describe, expect, it } from "vitest"`          | Framework — does not count           |
| `import { z } from "zod"`                                | Library — does not count             |
| `import type { Config } from "../src/config"`            | Type-only — does not count           |
| `import { parseConfig } from "../src/config"`            | Codebase (production) — counts       |
| `import { parseConfig } from "@/config"`                 | Codebase (production alias) — counts |
| `import { ConfigTestHarness } from "@testing/harnesses"` | Codebase (test infra) — counts       |

**Production code vs test harnesses — both are codebase imports:**

| Import target          | Correct pattern             | Classification    |
| ---------------------- | --------------------------- | ----------------- |
| Production module      | `from "@/config"`           | Direct coupling   |
| Test harness           | `from "@testing/harnesses"` | Indirect coupling |
| Co-located test helper | `from "./helpers"`          | Indirect coupling |

Test harnesses wrap production modules, so they provide **indirect coupling**. When a test imports a harness, follow the chain: verify the harness itself has direct coupling to the module the assertion is about. If the harness is also a tautology, the coupling chain is broken.

**Deep relative imports to test infrastructure are a red flag:**

```typescript
// ❌ Red flag — deep relative to test infra
import { ConfigTestHarness } from "../../../../../../tests/harnesses";
// Likely correct but fragile — verify the harness has real coupling

// ✅ Correct — path alias to test infra
import { ConfigTestHarness } from "@testing/harnesses";
```

Deep relative imports (`../../../`) are not themselves a coupling failure — the audit cares whether the import ultimately reaches the module under test, not the path style. But deep relative imports to test infrastructure signal the test may be importing a shared harness that wraps a different module than the assertion targets. Always trace the chain.

**Type-only imports are not coupling.** `import type` is erased at runtime — the test has zero runtime dependency on the module. If all codebase imports are `import type`, the test is a tautology.

**Barrel re-exports can mask false coupling.** If the test imports from an `index.ts` barrel file, verify the specific export used is the one the assertion is about — not a sibling export from the same barrel.

```typescript
// Assertion is about parseConfig, but test uses validateConfig from same barrel
import { validateConfig } from "../src";
// parseConfig is also exported from "../src" but never called → false coupling
```

</supplement>

<supplement property="falsifiability">

**TypeScript mocking patterns that sever coupling:**

```typescript
// Coupling severed — real module never runs
import { database } from "../src/database";
vi.mock("../src/database", () => ({ query: vi.fn() }));

// Coupling severed — method intercepted
vi.spyOn(service, "process").mockReturnValue(fakeResult);

// Coupling severed — jest equivalent
jest.mock("../src/database");
jest.spyOn(service, "process").mockImplementation(() => fakeResult);
```

**Legitimate alternatives mapped to `/testing` exceptions:**

| Exception                | TypeScript pattern                         | Why coupling maintained                    |
| ------------------------ | ------------------------------------------ | ------------------------------------------ |
| 1. Failure modes         | Class implementing interface, throws error | Tests error handling of real integration   |
| 2. Interaction protocols | Class with call-recording array            | Tests call sequence against real interface |
| 3. Time/concurrency      | `vi.useFakeTimers()`                       | Tests timing logic with real code          |
| 4. Safety                | Class that records but doesn't execute     | Tests intent without destructive effects   |
| 5. Combinatorial cost    | Configurable class mirroring real behavior | Tests breadth with real-shaped data        |
| 6. Observability         | Class capturing request details            | Tests details real system hides            |
| 7. Contract testing      | Stub validated against schema              | Tests serialization against real contract  |

For each test double found:

1. Identify which exception applies (must be one of the 7)
2. Verify the double is a class/object implementing an interface — not `vi.mock`/`vi.spyOn`
3. If `vi.mock` or `vi.spyOn` is used → coupling is severed → REJECT

</supplement>

<supplement property="alignment">

**Property-based testing via fast-check is required for specific assertion types:**

| Code type               | Required property        | Framework                |
| ----------------------- | ------------------------ | ------------------------ |
| Parsers                 | `parse(format(x)) == x`  | fast-check / `fc.assert` |
| Serialization           | `decode(encode(x)) == x` | fast-check / `fc.assert` |
| Mathematical operations | Algebraic properties     | fast-check / `fc.assert` |
| Complex algorithms      | Invariant preservation   | fast-check / `fc.assert` |

If the spec assertion describes a Property-type claim about a parser, serializer, or math operation, and the test uses only example-based assertions:

**REJECT — "misaligned: Property assertion requires property-based test strategy."**

```typescript
// ❌ REJECT: Parser assertion with only example-based test
it("parses simple JSON", () => {
  const result = parse("{\"key\": \"value\"}");
  expect(result).toEqual({ key: "value" });
});
// Missing: fc.assert + roundtrip property

// ✅ PASS: Meaningful roundtrip property
it("roundtrips valid values", () => {
  fc.assert(
    fc.property(validJsonArbitrary(), (value) => {
      expect(parse(format(value))).toEqual(value);
    }),
  );
});
```

Verify property quality — `fc.assert` that only checks "doesn't throw" is not a meaningful property:

```typescript
// ❌ REJECT: Trivial property (only tests "doesn't throw")
fc.assert(
  fc.property(fc.string(), (text) => {
    parse(text); // No assertion
  }),
);
```

For filename conventions, source-owned values, inline diagnostics, fixtures, and harness placement, defer to `/standardizing-typescript-tests`. Treat those as standards issues unless they break coupling, falsifiability, alignment, or coverage directly.

</supplement>

<supplement property="coverage">

**TypeScript coverage commands (vitest):**

Baseline (excluding test under audit):

```bash
pnpm vitest run --coverage --exclude='path/to/test-under-audit.test.ts'
```

With test:

```bash
pnpm vitest run --coverage 'path/to/test-under-audit.test.ts'
```

**Alternative tooling:** Projects may use c8, istanbul, or v8 coverage providers. Check `vitest.config.ts` for the `coverage.provider` setting and adapt commands accordingly.

Report actual deltas:

```text
Baseline: src/config-parser.ts — 43.2%
With test: src/config-parser.ts — 67.8%
Delta: +24.6% — new coverage ✓
```

</supplement>

</typescript_supplements>

<concrete_examples>

**Example 1: APPROVED**

Auditing `spx/21-config.enabler/43-parser.outcome/`

Assertion mapping:

```text
Assertion: MUST: Given a config file with nested sections, when parsed,
           then all section values are accessible by dotted path
Type: Scenario
Test: tests/config-parser.scenario.l1.test.ts ✓ exists
```

Coupling:

```text
Import: import { parseConfig } from "../src/config-parser"
Classification: Direct — codebase import of module under test
```

Falsifiability:

```text
Module: src/config-parser.ts
Mutation: parseConfig returns empty object instead of parsed sections
Impact: expect(result.section.key).toBe("value") fails — genuine falsifiability
No vi.mock or vi.spyOn found.
```

Alignment:

```text
Assertion says: "nested sections → accessible by dotted path"
Test does: parseConfig(nestedInput) → asserts result.section.key
Match: exact behavior tested ✓
Assertion type: Scenario → example-based test strategy ✓
```

Coverage:

```text
Baseline: src/config-parser.ts — 43.2%
With test: src/config-parser.ts — 67.8%
Delta: +24.6% ✓
```

```text
Audit: spx/21-config.enabler/43-parser.outcome/
Verdict: APPROVED

| # | Assertion             | Coupling | Falsifiability             | Alignment | Coverage | Verdict |
|---|-----------------------|----------|----------------------------|-----------|----------|---------|
| 1 | Nested section access | Direct   | Empty object breaks assert | ✓         | +24.6%   | PASS    |
```

---

**Example 2: REJECT — coupling severed by vi.mock**

Auditing `spx/32-api.enabler/54-auth.outcome/`

```text
Assertion: MUST: Given valid credentials, when authenticating,
           then a session token is returned from the database
Test: tests/auth.scenario.l2.test.ts ✓ exists
```

Coupling:

```text
Import: import { database } from "../src/database"
Classification: Direct — but...
Line 8: vi.mock("../src/database", () => ({ query: vi.fn() }))
→ Coupling severed. Real database.query never runs.
```

```text
Audit: spx/32-api.enabler/54-auth.outcome/
Verdict: REJECT

| # | Assertion     | Property Failed | Finding          | Detail                           |
|---|---------------|-----------------|------------------|----------------------------------|
| 1 | Session token | Falsifiability  | coupling severed | vi.mock replaces database module |

How tests could pass while assertions fail:
Database module is entirely replaced with a fake. Any schema change,
connection failure, or constraint violation in the real database is invisible.
The test verifies behavior against a vi.fn() that always succeeds.
```

---

**Example 3: REJECT — type-only import disguised as coupling**

Auditing `spx/15-theme.enabler/22-contrast.outcome/`

```text
Assertion: MUST: All theme colors meet WCAG AA contrast ratio (4.5:1)
Test: tests/contrast.compliance.l1.test.ts ✓ exists
```

Coupling:

```text
Imports:
  import { describe, expect, it } from "vitest"     → Framework
  import type { ThemeColor } from "../src/theme"     → Type-only (erased at runtime)

Zero runtime codebase imports → no coupling (tautology).
```

```text
Audit: spx/15-theme.enabler/22-contrast.outcome/
Verdict: REJECT

| # | Assertion        | Property Failed | Finding     | Detail                                        |
|---|------------------|-----------------|-------------|-----------------------------------------------|
| 1 | WCAG AA contrast | Coupling        | no coupling | Only vitest + import type (erased at runtime) |

How tests could pass while assertions fail:
Test declares its own color constants and checks contrast math against them.
The actual theme colors in src/theme.ts are never read. If all theme colors
are changed to pure white, this test still passes.
```

</concrete_examples>

<failure_modes>

**Failure 1: Accepted type-only import as coupling**

Reviewer saw `import type { ThemeColor } from "../src/theme"` and classified it as direct coupling. But `import type` is erased at compile time — the test never touches the runtime module. The test declared its own OKLCH constants and verified contrast math with zero connection to any theme file.

How to avoid: Coupling supplement — `import type` does not count as a codebase import.

**Failure 2: Missed coupling severed by vi.mock**

Reviewer saw `import { database } from "../src/database"` and classified it as direct coupling. The next line was `vi.mock("../src/database")`. The real module never ran.

How to avoid: Falsifiability supplement — check for `vi.mock`/`vi.spyOn` after confirming coupling. Import + mock = coupling severed.

**Failure 3: Confused barrel import with direct coupling**

Test imported `{ validateConfig }` from `"../src/index"`. The assertion was about `parseConfig`. Both are exported from the same barrel, but the test never called `parseConfig`.

How to avoid: Coupling supplement — barrel re-exports can mask false coupling. Verify the specific export used matches the assertion.

**Failure 4: Distracted by code quality while test was a tautology**

Reviewer spent the entire audit checking for `as any`, verifying return types, and searching for skip patterns. The test had perfect TypeScript quality and zero evidentiary value — it imported only vitest.

How to avoid: Essential principles — no code quality checks. Check the four evidence properties only.

</failure_modes>

<rejection_triggers>

| Category           | Trigger                                                     | Property       |
| ------------------ | ----------------------------------------------------------- | -------------- |
| **Coupling**       | Zero codebase imports (only framework/library)              | Coupling       |
| **Coupling**       | Only `import type` — erased at runtime                      | Coupling       |
| **Coupling**       | Barrel import of wrong export (false coupling)              | Coupling       |
| **Coupling**       | Import present but assertion-relevant function never called | Coupling       |
| **Falsifiability** | `vi.mock` / `jest.mock` replaces imported module            | Falsifiability |
| **Falsifiability** | `vi.spyOn` / `jest.spyOn` with `.mockReturnValue`           | Falsifiability |
| **Falsifiability** | Cannot name a concrete mutation that would fail the test    | Falsifiability |
| **Alignment**      | Parser/serializer without `fc.assert` roundtrip             | Alignment      |
| **Alignment**      | Property assertion tested with only examples                | Alignment      |
| **Alignment**      | Test exercises different behavior than assertion describes  | Alignment      |
| **Coverage**       | Zero delta with baseline < 100% on assertion-relevant files | Coverage       |

</rejection_triggers>

<success_criteria>

Audit is complete when:

- [ ] `/auditing-tests` workflow executed (load context → map assertions → 4 properties → verdict)
- [ ] TypeScript supplements applied at each property step
- [ ] Coupling: imports classified (including `import type`, path aliases, barrel re-exports)
- [ ] Falsifiability: `vi.mock`/`vi.spyOn` patterns checked, exceptions identified
- [ ] Alignment: property-based testing verified for parsers/serializers/math/algorithms
- [ ] Coverage: actual deltas from vitest coverage command
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has property, finding category, detail
- [ ] For REJECT: "how tests could pass while assertions fail" explained

</success_criteria>
