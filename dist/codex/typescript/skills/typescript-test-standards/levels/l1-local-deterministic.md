<l1_local_deterministic>

<purpose>
Use `l1` when evidence is available through deterministic in-process execution: pure functions, read-only reads of committed files, or dependency-injected collaborators that represent a Stage 5 exception. An `l1` test starts no process, runs no Git, writes no file, and makes no temporary directory.
</purpose>

<source_shape>
Existing code often needs to change before `l1` evidence is possible. Extract pure logic from command boundaries, inject filesystem/process dependencies, and export source-owned constructors or registries before writing the test.
</source_shape>

<test_shape>

- Call source functions directly.
- Use typed Stage 5 doubles only when the product-tree testing router selected an exception.
- Import source-owned singleton values directly.
- Use generators for variable inputs such as paths, names, option sets, and file contents.

</test_shape>

<file_naming>
Use the canonical TypeScript test filename pattern from `/typescript-test-standards`: `<subject>.<evidence>.<level>[.<runner>].test.ts`.

Examples: `config-loader.scenario.l1.test.ts`, `route-parser.mapping.l1.test.ts`, `slug-roundtrip.property.l1.test.ts`.
</file_naming>

<direct_function_example>

```typescript
import { buildArchiveCommand, COMMAND_FLAGS } from "@/archive-command";
import { describe, expect, it } from "vitest";

describe("buildArchiveCommand", () => {
  it("maps the checksum option to the command flag", () => {
    expect(buildArchiveCommand({ checksum: true })).toContain(COMMAND_FLAGS.checksum);
  });
});
```

This remains `l1` because the test calls deterministic source logic directly. The expected flag comes from the source-owned command registry rather than a test-owned constant.

</direct_function_example>

<generated_domain_example>

```typescript
import { normalizeSourcePath } from "@/paths";
import { sourcePathNormalizationProperty } from "@testing/harnesses/paths/properties";
import { assertProperty } from "@testing/harnesses/properties";
import { describe, it } from "vitest";

describe("normalizeSourcePath", () => {
  it("normalizes generated source paths idempotently", () => {
    assertProperty(sourcePathNormalizationProperty(normalizeSourcePath));
  });
});
```

This remains `l1` because the test calls deterministic source logic directly and the generator expands a variable input domain without remote services or heavy setup.

</generated_domain_example>

<reject>

- Declaring a test `l1` that writes a temp dir, runs Git, or starts a process
- Mocking the dependency under test instead of improving injection seams
- Constant-only generators for singleton source protocols
- Handwritten example values that claim to cover a domain

</reject>

<success_criteria>
An `l1` TypeScript test is correct when it proves the selected assertion in process, without a file write, a temp dir, Git, a process, or framework mocks.
</success_criteria>

</l1_local_deterministic>
