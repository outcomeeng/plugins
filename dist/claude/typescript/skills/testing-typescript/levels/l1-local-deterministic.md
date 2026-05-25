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

<file_naming>
Use the canonical TypeScript test filename pattern from `/standardizing-typescript-tests`: `<subject>.<evidence>.<level>[.<runner>].test.ts`.

Examples: `config-loader.scenario.l1.test.ts`, `route-parser.mapping.l1.test.ts`, `slug-roundtrip.property.l1.test.ts`.
</file_naming>

<direct_function_example>

```typescript
import { buildArchiveCommand, COMMAND_FLAGS } from "@/archive-command";
import { describe, expect, it } from "vitest";

describe("buildArchiveCommand", () => {
  it("maps the checksum option to the command flag", () => {
    const command = buildArchiveCommand({ checksum: true });

    expect(command).toContain(COMMAND_FLAGS.checksum);
  });
});
```

This remains `l1` because the test calls deterministic source logic directly. The expected flag comes from the source-owned command registry rather than a test-owned constant.

</direct_function_example>

<generated_domain_example>

```typescript
import { normalizeSourcePath } from "@/paths";
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

</generated_domain_example>

<temp_dir_example>

```typescript
import { writeNormalizedSourceManifest } from "@/manifest";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";

describe("writeNormalizedSourceManifest", () => {
  let projectDir: string | undefined;

  afterEach(async () => {
    if (projectDir) {
      await rm(projectDir, { force: true, recursive: true });
    }
  });

  it("writes normalized source paths in a temp product", async () => {
    projectDir = await mkdtemp(join(tmpdir(), "manifest-"));
    const manifestPath = join(projectDir, "manifest.json");

    await writeNormalizedSourceManifest({
      outputPath: manifestPath,
      sourcePaths: ["./src/index.ts", "src/lib/../lib/runtime.ts"],
    });

    await expect(readFile(manifestPath, "utf8")).resolves.toContain("src/index.ts");
  });
});
```

This remains `l1` because the test uses only local temp-dir state and calls source code directly. Filesystem work becomes `l2` only when it needs heavyweight local infrastructure, product binaries, or shared services.

</temp_dir_example>

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
