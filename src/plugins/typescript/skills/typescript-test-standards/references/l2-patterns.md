<l2_patterns>

Typed harness factories for tests that cross a local boundary (temp dirs, processes, Git, Docker, browsers, product binaries).

Verify the binary is available at harness construction time, not inside each test. Throw with an installation hint so the developer knows immediately what is missing.

```typescript
import { assertHugoBuildCreatesIndex, assertHugoBuildSucceeds } from "@testing/harnesses/hugo";
import { describe, it } from "vitest";

describe("Hugo build", () => {
  it("builds site without error", async () => {
    await assertHugoBuildSucceeds();
  });

  it("creates index.html in output", async () => {
    await assertHugoBuildCreatesIndex();
  });
});
```

<temp_dirs>

A temp dir is a file-system boundary, so a test that writes one is `l2`, however cheap.

```typescript
import { assertLoadsTempConfig } from "@testing/harnesses/config";
import { describe, it } from "vitest";

describe("loadConfig", () => {
  it("loads YAML config file", async () => {
    await assertLoadsTempConfig(loadConfig);
  });
});
```

</temp_dirs>

</l2_patterns>
