<l2_patterns>

Typed harness factories for tests that require real infrastructure (Docker, browsers, project binaries).

Verify the binary is available at harness construction time, not inside each test. Throw with an installation hint so the developer knows immediately what is missing.

```typescript
import { execa } from "execa";
import { existsSync } from "fs";
import { cp, mkdtemp, rm } from "fs/promises";
import { tmpdir } from "os";
import { join } from "path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

type HugoHarness = {
  siteDir: string;
  build(args?: string[]): Promise<{ exitCode: number; stdout: string }>;
  cleanup(): Promise<void>;
};

async function createHugoHarness(fixturePath?: string): Promise<HugoHarness> {
  try {
    await execa("hugo", ["version"]);
  } catch {
    throw new Error("Hugo not installed. Run: brew install hugo");
  }

  const siteDir = await mkdtemp(join(tmpdir(), "hugo-test-"));

  if (fixturePath) {
    await cp(fixturePath, siteDir, { recursive: true });
  } else {
    await createMinimalSite(siteDir);
  }

  return {
    siteDir,
    async build(args = []) {
      const result = await execa("hugo", ["--source", siteDir, ...args], {
        reject: false,
      });
      return { exitCode: result.exitCode, stdout: result.stdout };
    },
    async cleanup() {
      await rm(siteDir, { recursive: true, force: true });
    },
  };
}

describe("Hugo build", () => {
  let harness: HugoHarness;

  beforeAll(async () => {
    harness = await createHugoHarness();
  });

  afterAll(async () => {
    await harness.cleanup();
  });

  it("builds site without error", async () => {
    const result = await harness.build();

    expect(result.exitCode).toBe(0);
  });

  it("creates index.html in output", async () => {
    await harness.build();

    expect(existsSync(join(harness.siteDir, "public/index.html"))).toBe(true);
  });
});
```

</l2_patterns>
