---
name: testing-typescript
description: >-
  ALWAYS invoke this skill when writing or fixing tests for TypeScript.
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript/SKILL.md" || echo "standardizing-typescript not found — invoke typescript:standardizing-typescript manually"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript-tests/SKILL.md" || echo "standardizing-typescript-tests not found — invoke typescript:standardizing-typescript-tests manually"`

!`cat "${CLAUDE_SKILL_DIR}/../../../spec-tree/skills/testing/SKILL.md" || echo "testing not found — invoke spec-tree:testing manually"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. `typescript:standardizing-typescript`
2. `typescript:standardizing-typescript-tests`
3. `spec-tree:testing`

</codex_fallback>

# TypeScript Testing Patterns

> The standards and `/testing` router are pre-loaded above. Apply the router's level and evidence decisions to the TypeScript patterns in this skill.
>
> Also check for `spx/local/typescript.md` and `spx/local/typescript-tests.md` at the repository root — these contain project-specific overrides.

**Note on Analysis sections:** When reading node specs, the Analysis section documents what the spec author examined. It provides context but is not binding — implementation may diverge as understanding deepens. Use it as a starting point, not a contract.

---

## Router Decision → TypeScript Implementation

After running through the `/testing` router, use this mapping:

| Router Decision                                 | TypeScript Implementation                        |
| ----------------------------------------------- | ------------------------------------------------ |
| **Stage 2 → `l1`**                              | Vitest + temp dirs + type-safe DI                |
| **Stage 2 → `l2`**                              | Vitest + harness classes + Docker                |
| **Stage 2 → `l3`**                              | Vitest (CLI/API) or Playwright (browser)         |
| **Stage 3A** (Pure computation)                 | Pure functions with explicit types               |
| **Stage 3B** (Extract pure part)                | Factor into typed pure functions + thin wrappers |
| **Stage 5 Exception 1** (Failure modes)         | Interface + stub class returning errors          |
| **Stage 5 Exception 2** (Interaction protocols) | Spy class with typed call recording              |
| **Stage 5 Exception 3** (Time/concurrency)      | `vi.useFakeTimers()` or injected clock           |
| **Stage 5 Exception 4** (Safety)                | Stub class that records but doesn't execute      |
| **Stage 5 Exception 6** (Observability)         | Spy class capturing typed request details        |

---

## TypeScript Tooling by Level

| Level     | Infrastructure                                  | Speed | Framework  |
| --------- | ----------------------------------------------- | ----- | ---------- |
| `l1`      | Node.js stdlib + temp dirs + standard dev tools | <50ms | Vitest     |
| `l2`      | Docker containers + project-specific binaries   | <1s   | Vitest     |
| `l3`      | Network services + external APIs                | <30s  | Vitest     |
| `l2`/`l3` | Chrome + real user flows                        | <30s  | Playwright |

**Standard dev tools** (`l1`): git, node, npm, curl—available in CI without setup.
**Project-specific tools** (`l2`): Docker, Hugo, Caddy, PostgreSQL—require installation.

---

## `l1`: Pure Computation (Stage 3A)

When the router determines your code is pure computation, test it directly with full type safety.

### Pure Function Testing

```typescript
import { describe, expect, it } from "vitest";

describe("buildLhciCommand", () => {
  it("includes checksum flag when enabled", () => {
    const cmd = buildLhciCommand({ checksum: true });

    expect(cmd).toContain("--checksum");
  });

  it("preserves unicode paths", () => {
    const cmd = buildLhciCommand({
      source: "/tank/фото",
      dest: "remote:резервная",
    });

    expect(cmd).toContain("/tank/фото");
    expect(cmd).toContain("remote:резервная");
  });
});

describe("validateConfig", () => {
  it("rejects empty URL sets", () => {
    const result = validateConfig({ url_sets: {} });

    expect(result.ok).toBe(false);
    expect(result.error).toContain("url_sets");
  });

  it("accepts valid config", () => {
    const result = validateConfig({
      site_dir: "./site",
      url_sets: { critical: ["/", "/about/"] },
    });

    expect(result.ok).toBe(true);
  });
});
```

### Type-Safe Data Factories

Generate test data with full type inference. Never use arbitrary literals.

```typescript
import { describe, expect, it } from "vitest";

type AuditResult = {
  id: string;
  url: string;
  scores: {
    performance: number;
    accessibility: number;
  };
};

let idCounter = 0;

function createAuditResult(overrides: Partial<AuditResult> = {}): AuditResult {
  return {
    id: `audit-${++idCounter}`,
    url: `https://example.com/page-${idCounter}`,
    scores: {
      performance: 90,
      accessibility: 100,
    },
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

### Temporary Directories

Temp dirs are NOT external dependencies—use them freely at `l1`.

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
      `
site_dir: ./site
base_url: http://localhost:1313
`,
    );

    const config = await loadConfig(configPath);

    expect(config.site_dir).toBe("./site");
    expect(config.base_url).toBe("http://localhost:1313");
  });
});
```

---

## `l1`: Extracted Logic (Stage 3B)

When the router says "extract the pure part," factor your code with explicit types.

### Before: Tangled Code

```typescript
class OrderProcessor {
  constructor(private repository: OrderRepository) {}

  async process(order: Order): Promise<void> {
    // Validation (`l1`) mixed with persistence (`l2`, depends on database)
    if (!order.items.length) {
      throw new ValidationError("Empty order");
    }
    if (order.total < 0) {
      throw new ValidationError("Negative total");
    }
    await this.repository.save(order);
  }
}
```

### After: Extracted

```typescript
// Pure computation - test at `l1`, no doubles
type ValidationResult = { ok: true } | { ok: false; error: string };

function validateOrder(order: Order): ValidationResult {
  if (!order.items.length) {
    return { ok: false, error: "Empty order" };
  }
  if (order.total < 0) {
    return { ok: false, error: "Negative total" };
  }
  return { ok: true };
}

// Thin wrapper - test at `l2` with real database
class OrderProcessor {
  constructor(private repository: OrderRepository) {}

  async process(order: Order): Promise<void> {
    const result = validateOrder(order);
    if (!result.ok) {
      throw new ValidationError(result.error);
    }
    await this.repository.save(order);
  }
}
```

Test them separately:

```typescript
// l1: Test validation logic exhaustively
describe("validateOrder", () => {
  it("rejects empty order", () => {
    const result = validateOrder({ items: [], total: 0 });
    expect(result.ok).toBe(false);
  });

  it("rejects negative total", () => {
    const result = validateOrder({ items: [item], total: -10 });
    expect(result.ok).toBe(false);
  });

  it("accepts valid order", () => {
    const result = validateOrder({ items: [item], total: 100 });
    expect(result.ok).toBe(true);
  });
});

// l2: Test persistence with real database (see `l2` section)
```

---

## `l1`: Dependency Injection Pattern

When code has dependencies but you've determined `l1` is appropriate (via router Stage 3), use type-safe DI.

```typescript
// Define typed dependencies
type CommandResult = { exitCode: number; stdout: string; stderr: string };

type SyncDependencies = {
  runCommand: (cmd: string, args: string[]) => Promise<CommandResult>;
  getEnv: (key: string) => string | undefined;
};

async function syncToRemote(
  source: string,
  dest: string,
  deps: SyncDependencies,
): Promise<SyncResult> {
  const cmd = buildCommand(source, dest);
  const result = await deps.runCommand(cmd[0], cmd.slice(1));
  return {
    success: result.exitCode === 0,
    output: result.stdout,
  };
}

// Test with controlled implementation
describe("syncToRemote", () => {
  it("returns success on zero exit code", async () => {
    const deps: SyncDependencies = {
      runCommand: async () => ({ exitCode: 0, stdout: "Done", stderr: "" }),
      getEnv: () => undefined,
    };

    const result = await syncToRemote("/src", "remote:dest", deps);

    expect(result.success).toBe(true);
  });

  it("returns failure on non-zero exit code", async () => {
    const deps: SyncDependencies = {
      runCommand: async () => ({ exitCode: 1, stdout: "", stderr: "Error" }),
      getEnv: () => undefined,
    };

    const result = await syncToRemote("/src", "remote:dest", deps);

    expect(result.success).toBe(false);
  });
});
```

---

## Exception Case Implementations (TypeScript)

When the router reaches Stage 5 and an exception applies, here's how to implement each in TypeScript.

### Exception 1: Failure Modes

Testing retry logic, error handling, circuit breakers.

```typescript
type HttpClient = {
  fetch(url: string): Promise<{ status: number; body: unknown }>;
};

describe("fetchWithRetry", () => {
  it("retries on timeout", async () => {
    let attempts = 0;

    const client: HttpClient = {
      async fetch(url) {
        attempts++;
        if (attempts < 3) {
          throw new TimeoutError("Request timed out");
        }
        return { status: 200, body: "ok" };
      },
    };

    const result = await fetchWithRetry("https://api.example.com", client);

    expect(attempts).toBe(3);
    expect(result.status).toBe(200);
  });

  it("stops retrying after max attempts", async () => {
    const client: HttpClient = {
      async fetch() {
        throw new TimeoutError("Always fails");
      },
    };

    await expect(
      fetchWithRetry("https://api.example.com", client, { maxRetries: 3 }),
    ).rejects.toThrow(TimeoutError);
  });
});

describe("CircuitBreaker", () => {
  it("opens after threshold failures", async () => {
    let callCount = 0;

    const client: HttpClient = {
      async fetch() {
        callCount++;
        throw new Error("Connection refused");
      },
    };

    const breaker = new CircuitBreaker(client, { threshold: 3 });

    // First 3 calls go through and fail
    for (let i = 0; i < 5; i++) {
      try {
        await breaker.fetch("/");
      } catch {}
    }

    expect(callCount).toBe(3); // Circuit opened after 3
    expect(breaker.state).toBe("open");
  });
});
```

### Exception 2: Interaction Protocols

Testing call sequences, saga compensation, "no extra calls."

```typescript
describe("Saga", () => {
  it("compensates in reverse order on failure", async () => {
    const calls: string[] = [];

    const steps = [
      {
        execute: async () => calls.push("step1-execute"),
        compensate: async () => calls.push("step1-compensate"),
      },
      {
        execute: async () => {
          calls.push("step2-execute");
          throw new Error("Step 2 failed");
        },
        compensate: async () => calls.push("step2-compensate"),
      },
    ];

    const saga = new Saga(steps);

    await expect(saga.run()).rejects.toThrow();

    expect(calls).toEqual([
      "step1-execute",
      "step2-execute",
      "step2-compensate",
      "step1-compensate",
    ]);
  });
});

describe("CachingWrapper", () => {
  it("does not refetch cached values", async () => {
    let fetchCount = 0;

    const client = {
      async getUser(id: string) {
        fetchCount++;
        return { id, name: "Test" };
      },
    };

    const cache = new CachingWrapper(client);

    await cache.getUser("123");
    await cache.getUser("123");
    await cache.getUser("123");

    expect(fetchCount).toBe(1);
  });
});
```

### Exception 3: Time and Concurrency

Testing time-dependent behavior with Vitest fake timers or injected clock.

```typescript
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("Lease", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renews before expiry", async () => {
    let renewCount = 0;

    const lease = new Lease({
      ttl: 30_000,
      renewAt: 25_000,
      onRenew: () => renewCount++,
    });

    // Before renewal threshold
    await vi.advanceTimersByTimeAsync(24_000);
    expect(renewCount).toBe(0);

    // After renewal threshold
    await vi.advanceTimersByTimeAsync(2_000);
    expect(renewCount).toBe(1);
  });
});

// Alternative: Injected clock for more control
type Clock = {
  now(): number;
};

describe("TokenRefresher with injected clock", () => {
  it("refreshes token before expiry", async () => {
    let currentTime = 1000;
    const clock: Clock = { now: () => currentTime };

    let refreshed = false;
    const refresher = new TokenRefresher({
      expiresAt: 2000,
      refreshBuffer: 100,
      clock,
      onRefresh: () => {
        refreshed = true;
      },
    });

    // Before refresh window
    currentTime = 1899;
    refresher.tick();
    expect(refreshed).toBe(false);

    // Inside refresh window
    currentTime = 1901;
    refresher.tick();
    expect(refreshed).toBe(true);
  });
});
```

### Exception 4: Safety

Testing destructive operations without executing them.

```typescript
type PaymentProvider = {
  charge(amount: number, token: string): Promise<{ chargeId: string }>;
  refund(chargeId: string, amount: number): Promise<{ refundId: string }>;
};

describe("OrderProcessor", () => {
  it("processes refund for cancelled order", async () => {
    const refunds: Array<{ chargeId: string; amount: number }> = [];

    const payment: PaymentProvider = {
      async charge() {
        return { chargeId: "ch_123" };
      },
      async refund(chargeId, amount) {
        refunds.push({ chargeId, amount });
        return { refundId: "re_123" };
      },
    };

    const processor = new OrderProcessor({ payment });
    await processor.cancelOrder(orderWithCharge);

    expect(refunds).toEqual([{ chargeId: "ch_123", amount: 99.99 }]);
  });
});

type EmailService = {
  send(to: string, subject: string, body: string): Promise<void>;
};

describe("OrderNotifier", () => {
  it("sends shipping notification without real email", async () => {
    const sentEmails: Array<{ to: string; subject: string }> = [];

    const email: EmailService = {
      async send(to, subject) {
        sentEmails.push({ to, subject });
      },
    };

    const notifier = new OrderNotifier({ email });
    await notifier.notifyShipped(order);

    expect(sentEmails).toHaveLength(1);
    expect(sentEmails[0].to).toBe(order.customerEmail);
  });
});
```

### Exception 6: Observability

Testing request details the real system can't expose.

```typescript
type HttpClient = {
  post(url: string, options: { headers: Record<string, string>; body: unknown }): Promise<unknown>;
};

describe("PaymentClient", () => {
  it("includes idempotency key in request", async () => {
    const requests: Array<{ headers: Record<string, string> }> = [];

    const http: HttpClient = {
      async post(url, options) {
        requests.push({ headers: options.headers });
        return { id: "charge_123" };
      },
    };

    const client = new PaymentClient({ http });
    await client.charge(100, "tok_123");

    expect(requests).toHaveLength(1);
    expect(requests[0].headers["Idempotency-Key"]).toBeDefined();
  });
});

type Database = {
  query(sql: string, params: unknown[]): Promise<unknown>;
};

describe("UserRepository", () => {
  it("batches inserts", async () => {
    const queries: string[] = [];

    const db: Database = {
      async query(sql) {
        queries.push(sql);
        return { rowCount: 1 };
      },
    };

    const repo = new UserRepository({ db });
    await repo.bulkInsert([user1, user2, user3]);

    // Should be ONE batch insert, not three
    expect(queries).toHaveLength(1);
    expect(queries[0]).toContain("INSERT INTO users");
  });
});
```

---

## `l2` Patterns

When the router determines `l2` is appropriate, use real dependencies via typed harnesses.

### Harness Pattern

```typescript
import { execa } from "execa";
import { cp, mkdtemp, rm } from "fs/promises";
import { tmpdir } from "os";
import { join } from "path";

type HugoHarness = {
  siteDir: string;
  outputDir: string;
  build(args?: string[]): Promise<{ exitCode: number; stdout: string }>;
  cleanup(): Promise<void>;
};

async function createHugoHarness(fixturePath?: string): Promise<HugoHarness> {
  // Verify Hugo is installed
  try {
    await execa("hugo", ["version"]);
  } catch {
    throw new Error("Hugo not installed. Run: brew install hugo");
  }

  const siteDir = await mkdtemp(join(tmpdir(), "hugo-test-"));
  const outputDir = join(siteDir, "public");

  if (fixturePath) {
    await cp(fixturePath, siteDir, { recursive: true });
  } else {
    await createMinimalSite(siteDir);
  }

  return {
    siteDir,
    outputDir,
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
```

### Using Harnesses

```typescript
import { afterAll, beforeAll, describe, expect, it } from "vitest";

describe("Hugo build", () => {
  let harness: HugoHarness;

  beforeAll(async () => {
    harness = await createHugoHarness();
  });

  afterAll(async () => {
    await harness.cleanup();
  });

  it("builds site successfully", async () => {
    const result = await harness.build();

    expect(result.exitCode).toBe(0);
  });

  it("creates index.html in output", async () => {
    await harness.build();

    const indexPath = join(harness.outputDir, "index.html");
    expect(existsSync(indexPath)).toBe(true);
  });

  it("minifies output when flag is set", async () => {
    const result = await harness.build(["--minify"]);

    expect(result.exitCode).toBe(0);
    // Verify minification by checking output size or content
  });
});
```

### Database Harness

```typescript
import { Pool } from "pg";

type PostgresHarness = {
  connectionString: string;
  pool: Pool;
  query<T>(sql: string, params?: unknown[]): Promise<T[]>;
  reset(): Promise<void>;
  cleanup(): Promise<void>;
};

async function createPostgresHarness(): Promise<PostgresHarness> {
  const config = {
    host: process.env.TEST_DB_HOST || "localhost",
    port: parseInt(process.env.TEST_DB_PORT || "5432"),
    database: "test_db",
    user: "postgres",
    password: "postgres",
  };

  const pool = new Pool(config);

  // Verify connection
  try {
    await pool.query("SELECT 1");
  } catch (error) {
    throw new Error(
      `Cannot connect to test database. Start it with: docker-compose up -d postgres`,
    );
  }

  return {
    connectionString: `postgresql://${config.user}:${config.password}@${config.host}:${config.port}/${config.database}`,
    pool,
    async query<T>(sql: string, params?: unknown[]): Promise<T[]> {
      const result = await pool.query(sql, params);
      return result.rows as T[];
    },
    async reset() {
      await pool.query("DROP SCHEMA public CASCADE; CREATE SCHEMA public;");
    },
    async cleanup() {
      await pool.end();
    },
  };
}
```

---

## `l3` Patterns

When the router determines `l3` is required (real credentials, external services).

### Credential Management

```typescript
/**
 * l3 tests require these environment variables:
 *
 * Required:
 *   LHCI_SERVER_URL    - LHCI server URL
 *   LHCI_TOKEN         - LHCI build token
 *
 * Where to find:
 *   - 1Password: "Engineering/Test Credentials"
 *
 * Setup:
 *   cp .env.test.example .env.test
 *   # Fill in values from 1Password
 */

type Credentials = {
  lhciServerUrl: string;
  lhciToken: string;
};

function loadCredentials(): Credentials | null {
  const lhciServerUrl = process.env.LHCI_SERVER_URL;
  const lhciToken = process.env.LHCI_TOKEN;

  if (!lhciServerUrl || !lhciToken) {
    return null;
  }

  return { lhciServerUrl, lhciToken };
}

function requireCredentials(): Credentials {
  const creds = loadCredentials();
  if (!creds) {
    throw new Error(
      "Missing required credentials. See test file for setup instructions.",
    );
  }
  return creds;
}
```

### Skip If No Credentials

```typescript
import { describe, expect, it } from "vitest";

describe("LHCI", () => {
  const credentials = loadCredentials();

  it.skipIf(!credentials)("uploads audit results", async () => {
    const creds = requireCredentials();

    const result = await uploadAuditResults({
      serverUrl: creds.lhciServerUrl,
      token: creds.lhciToken,
      results: testResults,
    });

    expect(result.success).toBe(true);
  });
});
```

### Playwright for Browser

```typescript
// spx/.../tests/checkout.scenario.l2.playwright.test.ts
import { expect, test } from "@playwright/test";

test.describe("Checkout Flow", () => {
  test("user can complete purchase", async ({ page }) => {
    await page.goto("/products");
    await page.click("[data-testid=\"add-to-cart\"]");
    await page.click("[data-testid=\"checkout\"]");

    await page.fill("[data-testid=\"email\"]", "test@example.com");
    await page.fill("[data-testid=\"card-number\"]", "4242424242424242");
    await page.click("[data-testid=\"submit\"]");

    await expect(page.locator("[data-testid=\"confirmation\"]")).toBeVisible();
  });
});
```

---

## Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["spx/**/*.test.ts"],
    exclude: ["**/*.playwright.test.ts"],
    testTimeout: 30000,
    hookTimeout: 30000,
  },
});
```

```typescript
// playwright.config.ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./spx",
  testMatch: "**/*.playwright.test.ts",
  fullyParallel: true,
  use: {
    baseURL: process.env.TEST_BASE_URL || "http://localhost:3000",
  },
});
```

---

## Test Organization (Outcome Engineering Framework)

Tests are co-located with specs in `spx/`. Filenames encode subject, evidence, level, and optional runner:

```
spx/
└── {NN}-{slug}.enabler/
    └── {NN}-{slug}.outcome/
        ├── {slug}.outcome.md             # Node spec
        └── tests/
            ├── {name}.mapping.l1.test.ts
            ├── {name}.scenario.l2.test.ts
            ├── {name}.conformance.l3.test.ts
            └── {name}.scenario.l2.playwright.test.ts
```

Run by runner:

```bash
vitest spx/                    # Runs default-runner *.test.ts files
npx playwright test spx/       # Runs *.playwright.test.ts files
```

### Shared Test Infrastructure

```
testing/
├── harnesses/
│   ├── index.ts
│   ├── hugo.ts               # Hugo harness
│   ├── postgres.ts           # PostgreSQL harness
│   └── factories.ts          # Type-safe factories
└── fixtures/
    └── values.ts             # TYPICAL, EDGES collections
```

Import in tests:

```typescript
import { createAuditResult } from "@testing/harnesses/factories";
import { createHugoHarness } from "@testing/harnesses/hugo";
```

---

## Quick Reference

| Aspect       | `l1`                     | `l2`               | `l3`                 |
| ------------ | ------------------------ | ------------------ | -------------------- |
| Dependencies | DI with typed interfaces | Real via harness   | Real via credentials |
| Data         | Type-safe factories      | Fixtures + harness | Test accounts        |
| Speed        | <50ms                    | <1s                | <30s                 |
| CI           | Every commit             | Every commit       | Nightly/pre-release  |

---

## TypeScript-Specific Anti-Patterns

### Using vi.mock() on Modules

```typescript
// ❌ WRONG: Module-level mocking
vi.mock("execa", () => ({ execa: vi.fn() }));

it("runs hugo", async () => {
  await buildHugo(siteDir);
  expect(execa).toHaveBeenCalled(); // Proves nothing
});

// ✅ RIGHT: Dependency injection
type BuildDeps = {
  runCommand: (cmd: string, args: string[]) => Promise<{ exitCode: number }>;
};

it("returns success on zero exit", async () => {
  const deps: BuildDeps = {
    runCommand: async () => ({ exitCode: 0 }),
  };

  const result = await buildHugo(siteDir, deps);

  expect(result.success).toBe(true);
});
```

### Using vi.fn() for Behavior Testing

```typescript
// ❌ WRONG: vi.fn() tests HOW, not WHAT
it("calls execa with args", async () => {
  const deps = { execa: vi.fn().mockResolvedValue({ exitCode: 0 }) };
  await buildHugo(siteDir, deps);
  expect(deps.execa).toHaveBeenCalledWith("hugo", ["--minify"]);
});

// ✅ RIGHT: Test observable behavior
it("produces minified output", async () => {
  const result = await buildHugo(siteDir, realDeps);
  expect(result.minified).toBe(true);
});
```

### Losing Type Safety in Tests

```typescript
// ❌ WRONG: Casting to any
const deps = { runCommand: vi.fn() } as any;

// ✅ RIGHT: Full type safety
const deps: BuildDeps = {
  runCommand: async () => ({ exitCode: 0 }),
};
```

### Testing Library Behavior

```typescript
// ❌ WRONG: Testing that Zod works
it("validates with Zod schema", () => {
  const schema = z.object({ url: z.string().url() });
  expect(schema.parse({ url: "http://example.com" })).toBeDefined();
});

// ✅ RIGHT: Test YOUR behavior that uses validation
it("rejects invalid config with descriptive error", () => {
  const result = loadConfig({ url: "not-a-url" });

  expect(result.ok).toBe(false);
  expect(result.error).toContain("url");
});
```

### Playwright `{ request }` fixture does not inherit browser-context cookies

Playwright's `{ request }` fixture uses its own test-scoped `APIRequestContext` that does NOT share cookies with the browser `BrowserContext`. Cookies set via `context.addCookies([...])` (e.g. by a `beforeEach` helper that encrypts a flag-override cookie) do not reach `{ request }`.

```typescript
// ❌ WRONG: request fixture — no cookie inheritance
test.beforeEach(async ({ context }) => {
  await context.addCookies([{ name: "override", value: ENCRYPTED, path: "/", domain: "localhost" }]);
});

test("API returns flag-gated payload", async ({ request }) => {
  const response = await request.get("/api/data"); // cookie absent
  expect(await response.json()).toContain(FLAGGED_ITEM); // fails
});

// ✅ RIGHT: context.request — shares cookies with browser context
test("API returns flag-gated payload", async ({ context }) => {
  const response = await context.request.get("/api/data"); // cookie present
  expect(await response.json()).toContain(FLAGGED_ITEM);
});
```

`page.request` also shares cookies with the browser context and works when a test already needs a page.
