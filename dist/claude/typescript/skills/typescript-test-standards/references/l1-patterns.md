<l1_patterns>

Table of contents: [pure_function](#pure_function) · [typed_factory](#typed_factory)

<pure_function>

```typescript
import { ARCHIVE_FLAGS } from "@/archive-command";
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
import { createFailingPerformanceAuditResult } from "@testing/generators/audits";

describe("analyzeResults", () => {
  it("fails on low performance", () => {
    expect(analyzeResults([createFailingPerformanceAuditResult()]).passed).toBe(false);
  });
});
```

</typed_factory>

</l1_patterns>
