<l1_patterns>

Contents: `<pure_function>`, `<typed_factory>`, `<temp_dirs>`

<pure_function>

```typescript
import { ARCHIVE_FLAGS, buildCommand } from "@/archive-command";
import { archiveCommandCase } from "@testing/generators/archive-command";
import { archiveCommandIncludesSourcePathProperty } from "@testing/harnesses/archive-command/properties";
import { assertProperty } from "@testing/harnesses/properties";
import { describe, expect, it } from "vitest";

describe("buildCommand", () => {
  it("includes checksum flag when enabled", () => {
    expect(buildCommand(archiveCommandCase())).toContain(ARCHIVE_FLAGS.checksum);
  });

  it("preserves generated source paths", () => {
    assertProperty(archiveCommandIncludesSourcePathProperty(buildCommand));
  });
});
```

</pure_function>

<typed_factory>

Generate test data with full type inference. Never use arbitrary literals.

```typescript
import { analyzeResults } from "@/audit-results";
import { createFailingPerformanceAuditResult } from "@testing/generators/audits";
import { describe, expect, it } from "vitest";

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
import { loadConfig } from "@/config";
import { assertLoadsTempConfig } from "@testing/harnesses/config";
import { describe, it } from "vitest";

describe("loadConfig", () => {
  it("loads YAML config file", async () => {
    await assertLoadsTempConfig(loadConfig);
  });
});
```

</temp_dirs>

</l1_patterns>
