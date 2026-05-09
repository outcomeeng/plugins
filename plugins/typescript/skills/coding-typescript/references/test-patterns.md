<debuggable_test_organization>

<principle>
Write tests in the order that exposes the source contract first:

1. Improve the code under test until behavior can be observed without copying internals.
2. Import source-owned registries, constructors, and protocol values directly.
3. Generate variable input domains with meaningful `fc.Arbitrary` values.
4. Derive expected outputs from generated inputs or independent standards.

Do not create shared test-value files or named example bags. Those collections preserve hand-picked examples and hide ownership.
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

Use this pattern when inputs vary across a real domain: paths, names, identifiers, content, option sets, encodings, counts, or structured project shapes.

</generated_domain_inputs>

<debugging_failures>
When a property failure needs a stable repro, use fast-check's reported seed and counterexample. Add a named regression test only if the counterexample identifies a distinct source-owned behavior that should remain documented. The regression input must come from a source constructor or a generator replay helper, not a handwritten shared constant.
</debugging_failures>

<anti_patterns>

- Shared hardcoded test-value modules
- Constant-only generators for source-owned singleton shapes
- Expected outputs copied from fixtures instead of derived from inputs
- Fixtures that contain strings or numbers only to avoid literals in test files
- Example tests that pass on one hand-picked value while claiming domain coverage

</anti_patterns>

</debuggable_test_organization>
