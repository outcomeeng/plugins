<debuggable_test_organization>

<principle>
Write tests in the order that exposes the source contract first:

1. Improve the code under test until behavior can be observed without copying internals.
2. Import source-owned registries, constructors, and protocol values directly.
3. Generate variable input domains with meaningful `fc.Arbitrary` values.
4. Derive expected outputs from generated inputs or independent standards.

Do not create shared test-value files or named example bags. Those collections preserve hand-picked examples and hide ownership.

Property failures report a seed and shrunk counterexample, but that output rarely explains which source contract the value represents. Without named contract cases, the first failure often has no stable regression anchor for debugging. Keep named contract tests for source-owned behavior that must remain documented, then use property tests to search the variable domain around that contract.
</principle>

<source_contract_first>

```typescript
import { createAbsentConfigReadResult, isAbsentConfigReadResult } from "@/config/read-result";
import { describe, expect, it } from "vitest";

describe("isAbsentConfigReadResult", () => {
  it("accepts the source-owned absent result", () => {
    const result = createAbsentConfigReadResult();

    expect(isAbsentConfigReadResult(result)).toBe(true);
  });
});
```

Use this pattern when the domain has exactly one valid source-owned shape. The constructor belongs in source because production code and tests both rely on the same protocol.

</source_contract_first>

<generated_domain_inputs>

```typescript
import { normalizeSourcePath } from "@/paths";
import { arbitrarySourceFilePath } from "@testing/generators/paths";
import * as fc from "fast-check";
import { describe, expect, it } from "vitest";

describe("normalizeSourcePath", () => {
  it("normalizes every generated source path idempotently", () => {
    fc.assert(
      fc.property(arbitrarySourceFilePath(), (path) => {
        const normalized = normalizeSourcePath(path);

        expect(normalizeSourcePath(normalized)).toBe(normalized);
      }),
    );
  });
});
```

Use this pattern when inputs vary across a real domain: paths, names, identifiers, content, option sets, encodings, counts, or structured product shapes.

For fast-check v4, use `fc.string({ unit: arbitrary })` when building strings from a character or token arbitrary. `fc.stringOf(arbitrary)` is a v3 API and must not appear in new examples.

</generated_domain_inputs>

<debugging_failures>
When a property failure exposes a bug, replay fast-check's reported seed and counterexample first. Add a named regression test only when the counterexample identifies a stable source-owned behavior that should remain documented. The regression input must come from a source constructor or a generator replay helper, not a handwritten shared constant.

```typescript
import { normalizeSourcePath } from "@/paths";
import { createSourcePath } from "@/paths/source-path";
import { describe, expect, it } from "vitest";

describe("normalizeSourcePath", () => {
  it("preserves the normalized form for the seed 87231 Windows path regression", () => {
    const path = createSourcePath({
      drive: "C",
      segments: ["workspace", "src", "index.ts"],
    });

    expect(normalizeSourcePath(path)).toBe("C:/workspace/src/index.ts");
  });
});
```

The test name records the replayed seed or counterexample source, while the input still comes from source-owned construction. Do not paste a shrunk object literal into a shared constant bag.
</debugging_failures>

<anti_patterns>

- Shared hardcoded test-value modules
- Constant-only generators for source-owned singleton shapes
- Expected outputs copied from fixtures instead of derived from inputs
- Fixtures that contain strings or numbers only to avoid literals in test files
- Example tests that pass on one hand-picked value while claiming domain coverage
- `fc.stringOf(arbitrary)` in new examples; use `fc.string({ unit: arbitrary })` for fast-check v4

</anti_patterns>

</debuggable_test_organization>
