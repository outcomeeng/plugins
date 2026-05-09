<l1_local_deterministic>

<purpose>
Use `l1` when evidence is available through deterministic local execution: pure functions, cheap temp-dir filesystem work, standard repo-required tools, or dependency-injected collaborators that represent a Stage 5 exception.
</purpose>

<source_shape>
Existing code often needs to change before `l1` evidence is possible. Extract pure logic from command boundaries, inject filesystem/process dependencies, and export source-owned constructors or registries before writing the test.
</source_shape>

<test_shape>

- Call source functions directly.
- Use Node temp dirs for cheap filesystem state.
- Use typed Stage 5 doubles only when the spec-tree testing router selected an exception.
- Import source-owned singleton values directly.
- Use generators for variable inputs such as paths, names, option sets, and file contents.

</test_shape>

<example>

```typescript
import { arbitrarySourceFilePath } from "@testing/generators/paths";
import * as fc from "fast-check";
import { describe, expect, it } from "vitest";

describe("normalizeSourcePath", () => {
  it("normalizes generated source paths idempotently", () => {
    fc.assert(
      fc.property(arbitrarySourceFilePath(), (path) => {
        const normalized = normalizeSourcePath(path);

        expect(normalizeSourcePath(normalized)).toBe(normalized);
      }),
    );
  });
});
```

This remains `l1` because the test calls deterministic source logic directly and the generator expands a variable input domain without remote services or heavy setup.

</example>

<reject>

- Moving a filesystem test to `l2` only because it touches temp dirs
- Mocking the dependency under test instead of improving injection seams
- Constant-only generators for singleton source protocols
- Handwritten example values that claim to cover a domain

</reject>

<success_criteria>
An `l1` TypeScript test is correct when it proves the selected assertion without remote services, shared state, heavyweight local setup, or framework mocks.
</success_criteria>

</l1_local_deterministic>
