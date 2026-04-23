<objective>
TypeScript `l1` test patterns for evidence that can be proven with cheap local execution.
</objective>

<when_to_use>
Use `l1` when the evidence is available through:

- Pure computation
- Temp dirs and local filesystem work
- Standard repo-required tools such as node, npm, git, and curl
- Dependency-injected collaborators whose real dependency is outside the proof
- Stage 5 doubles that are explicit classes or objects

Do not move a test to `l2` only because it touches the filesystem. Temp-dir file work remains `l1` when it is cheap, deterministic, and safe.
</when_to_use>

<file_naming>
Use the `/standardizing-typescript-tests` filename pattern:

```text
<subject>.<evidence>.l1.test.ts
```

Examples:

- `config-loader.scenario.l1.test.ts`
- `route-parser.mapping.l1.test.ts`
- `slug-roundtrip.property.l1.test.ts`
- `pii-redaction.compliance.l1.test.ts`

</file_naming>

<patterns>
Pure function example:

```typescript
import { describe, expect, it } from "vitest";

describe("buildCommand", () => {
  it("maps checksum option to the command flag", () => {
    const command = buildCommand({ checksum: true });

    expect(command).toContain("--checksum");
  });
});
```

Temp-dir example:

```typescript
import { mkdtemp, rm, writeFile } from "fs/promises";
import { tmpdir } from "os";
import { join } from "path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

describe("loadConfig", () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await mkdtemp(join(tmpdir(), "config-"));
  });

  afterEach(async () => {
    await rm(tempDir, { recursive: true });
  });

  it("loads config from disk", async () => {
    const configPath = join(tempDir, "config.yaml");
    await writeFile(configPath, "base_url: http://localhost:3000\n");

    const config = await loadConfig(configPath);

    expect(config.baseUrl).toBe("http://localhost:3000");
  });
});
```

Stage 5 spy example:

```typescript
class RecordingRunner implements CommandRunner {
  readonly commands: string[][] = [];

  async run(command: readonly string[]): Promise<CommandResult> {
    this.commands.push([...command]);
    return { exitCode: 0, stdout: "", stderr: "" };
  }
}
```

</patterns>

<success_criteria>
An `l1` TypeScript test is correct when it proves the chosen evidence without remote services, shared state, heavyweight local setup, or framework mocks.
</success_criteria>
