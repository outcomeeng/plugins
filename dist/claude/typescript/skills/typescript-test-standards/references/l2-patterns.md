<l2_patterns>

Typed harness factories for tests that require real infrastructure (Docker, browsers, product binaries).

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

</l2_patterns>
