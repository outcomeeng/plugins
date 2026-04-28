<l1_patterns>

Table of contents: [pure_function](#pure_function) · [typed_factory](#typed_factory) · [temp_dirs](#temp_dirs)

<pure_function>

```typescript
import { describe, expect, it } from "vitest";

describe("buildCommand", () => {
  it("includes checksum flag when enabled", () => {
    const cmd = buildCommand({ checksum: true });

    expect(cmd).toContain("--checksum");
  });

  it("preserves unicode paths", () => {
    const cmd = buildCommand({
      source: "/tank/photos",
      dest: "remote:backup",
    });

    expect(cmd).toContain("/tank/photos");
  });
});
```

</pure_function>

<typed_factory>

Generate test data with full type inference. Never use arbitrary literals.

```typescript
type AuditResult = {
  id: string;
  url: string;
  scores: { performance: number; accessibility: number };
};

let idCounter = 0;

function createAuditResult(overrides: Partial<AuditResult> = {}): AuditResult {
  return {
    id: `audit-${++idCounter}`,
    url: `https://example.com/page-${idCounter}`,
    scores: { performance: 90, accessibility: 100 },
    ...overrides,
  };
}

describe("analyzeResults", () => {
  it("fails on low performance", () => {
    const result = createAuditResult({
      scores: { performance: 45, accessibility: 100 },
    });

    const analysis = analyzeResults([result], { minPerformance: 90 });

    expect(analysis.passed).toBe(false);
  });
});
```

</typed_factory>

<temp_dirs>

Temp dirs are not external dependencies -- use them freely at `l1`.

```typescript
import { mkdtemp, rm, writeFile } from "fs/promises";
import { tmpdir } from "os";
import { join } from "path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

describe("loadConfig", () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await mkdtemp(join(tmpdir(), "config-test-"));
  });

  afterEach(async () => {
    await rm(tempDir, { recursive: true });
  });

  it("loads YAML config file", async () => {
    const configPath = join(tempDir, "config.yaml");
    await writeFile(
      configPath,
      "site_dir: ./site\nbase_url: http://localhost:1313\n",
    );

    const config = await loadConfig(configPath);

    expect(config.site_dir).toBe("./site");
    expect(config.base_url).toBe("http://localhost:1313");
  });
});
```

</temp_dirs>

</l1_patterns>
