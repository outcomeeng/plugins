<l1_patterns>

Table of contents: [pure_function](#pure_function) · [typed_factory](#typed_factory) · [temp_dirs](#temp_dirs)

<pure_function>

```typescript
import { ARCHIVE_FLAGS } from "@/archive-command";
import { arbitraryArchiveCommandCase, archiveCommandCase } from "@testing/generators/archive-command";
import { assertProperty } from "@testing/harnesses/properties";
import * as fc from "fast-check";
import { describe, expect, it } from "vitest";

describe("buildCommand", () => {
  it("includes checksum flag when enabled", () => {
    expect(buildCommand(archiveCommandCase())).toContain(ARCHIVE_FLAGS.checksum);
  });

  it("preserves generated source paths", () => {
    assertProperty(
      fc.property(arbitraryArchiveCommandCase(), (archiveCase) => {
        expect(buildCommand(archiveCase.options)).toContain(archiveCase.sourcePath);
      }),
    );
  });
});
```

</pure_function>

<typed_factory>

Generate test data with full type inference. Never use arbitrary literals.

```typescript
import { createFailingPerformanceAuditResult } from "@testing/generators/audits";

describe("analyzeResults", () => {
  it("fails on low performance", () => {
    expect(analyzeResults([createFailingPerformanceAuditResult()]).passed).toBe(false);
  });
});
```

</typed_factory>

<temp_dirs>

Temp dirs are not external dependencies -- use them freely at `l1`.

```typescript
import { withTempConfig } from "@testing/harnesses/config";
import { describe, expect, it } from "vitest";

describe("loadConfig", () => {
  it("loads YAML config file", async () => {
    await withTempConfig(async (configPath, expectedConfig) => {
      await expect(loadConfig(configPath)).resolves.toMatchObject(expectedConfig);
    });
  });
});
```

</temp_dirs>

</l1_patterns>
