---
name: standardizing-typescript-tests
disable-model-invocation: true
description: >-
  TypeScript testing standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Define TypeScript-specific test standards loaded by `/testing-typescript`, `/coding-typescript`, `/architecting-typescript`, and `/auditing-typescript-tests`.

Read `/testing` first when deciding what evidence to create. Read `/standardizing-typescript` before this reference when writing or reviewing TypeScript test code. These standards apply to all TypeScript tests.
</objective>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/typescript-tests.md` at the repository root. Read that file after this reference if it exists and apply it as the repo-local specialization.
</repo_local_overlay>

<core_model>
Every TypeScript test file name encodes three independent axes:

| Axis     | Tokens                                                         | Meaning                                    |
| -------- | -------------------------------------------------------------- | ------------------------------------------ |
| Evidence | `scenario`, `mapping`, `conformance`, `property`, `compliance` | What kind of proof the test provides       |
| Level    | `l1`, `l2`, `l3`                                               | How painful the test is to run             |
| Runner   | optional token such as `playwright`                            | Which non-default runner executes the file |

Evidence, level, and runner are orthogonal:

- A Playwright test can be `l2` or `l3`
- A filesystem test can be `l1` when it uses cheap temp dirs
- A `scenario` test can run at any level
- A runner token appears only when the runner is not the default

</core_model>

<file_naming>
Use this canonical TypeScript pattern:

```text
<subject>.<evidence>.<level>[.<runner>].test.ts
```

Examples:

| Purpose                               | File                                      |
| ------------------------------------- | ----------------------------------------- |
| Cheap behavior scenario               | `config-loader.scenario.l1.test.ts`       |
| Deterministic input-output mapping    | `route-parser.mapping.l1.test.ts`         |
| Local browser flow through Playwright | `checkout.scenario.l2.playwright.test.ts` |
| Live webhook contract                 | `stripe-webhook.conformance.l3.test.ts`   |
| Safety boundary                       | `pii-redaction.compliance.l1.test.ts`     |
| Generated invariant                   | `slug-roundtrip.property.l1.test.ts`      |

Do not use legacy file suffixes such as `.unit.test.ts`, `.integration.test.ts`, `.e2e.test.ts`, or `.spec.ts` as the signal for evidence, level, or runner.
</file_naming>

<level_tooling>
Choose the level from execution pain and dependency availability:

| Level | Infrastructure                                     | Default runner | Typical runtime |
| ----- | -------------------------------------------------- | -------------- | --------------- |
| `l1`  | Node.js stdlib, temp dirs, repo-required dev tools | Vitest         | milliseconds    |
| `l2`  | Docker, browsers, dev servers, project binaries    | Vitest         | seconds         |
| `l3`  | Remote services, credentials, shared environments  | Vitest         | seconds/minutes |

Use `playwright` as the runner token when Playwright is the non-default runner:

- `browser-menu.scenario.l2.playwright.test.ts` for a local browser flow
- `production-login.scenario.l3.playwright.test.ts` for a credentialed remote flow

Keep runner configuration aligned with the filename pattern:

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["spx/**/*.test.ts"],
    exclude: ["**/*.playwright.test.ts"],
  },
});
```

```typescript
// playwright.config.ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./spx",
  testMatch: "**/*.playwright.test.ts",
});
```

</level_tooling>

<router_mapping>
After `/testing` chooses the evidence and level, implement it with these TypeScript patterns:

| Router Decision                            | TypeScript implementation                                  |
| ------------------------------------------ | ---------------------------------------------------------- |
| Stage 2 -> `l1`                            | Vitest, test harnesses, typed factories, temp dirs         |
| Stage 2 -> `l2`                            | Vitest or Playwright with locally available real APIs      |
| Stage 2 -> `l3`                            | Vitest or Playwright with credentials or remote real APIs  |
| Stage 3A: pure computation                 | Direct tests of typed pure functions                       |
| Stage 3B: extract pure part                | Pure helper at `l1`, boundary at outer level               |
| Stage 5 exception 1: failure simulation    | Interface implementation that throws/errors                |
| Stage 5 exception 2: interaction protocols | Spy function or class with typed call recording            |
| Stage 5 exception 3: time/concurrency      | Injected clock or `vi.useFakeTimers()`                     |
| Stage 5 exception 4: safety                | Function or class that records intent without side effects |
| Stage 5 exception 5: combinatorial cost    | Configurable fake with real-shaped behavior                |
| Stage 5 exception 6: observability         | Spy that captures hidden boundary details                  |
| Stage 5 exception 7: contract probes       | Stub validated against the contract schema                 |

</router_mapping>

<l1_patterns>
Pure computation and filesystem tests at `l1` use direct function calls, typed factories, and Node.js temp dirs. Read `${CLAUDE_SKILL_DIR}/references/l1-patterns.md` for full examples of each pattern.
</l1_patterns>

<exception_implementations>
When `/testing` routes to Stage 5, implement the exception in TypeScript using the pattern from `<router_mapping>`. Read `${CLAUDE_SKILL_DIR}/references/exception-implementations.md` for full TypeScript examples of exceptions 1–4 and 6.

Exception 5 (combinatorial cost: configurable fake with real-shaped behavior) is listed in `<router_mapping>` but does not yet have a TypeScript example.
</exception_implementations>

<l2_patterns>
Use typed harness factories when tests require real infrastructure (Docker, browsers, project binaries). Verify the binary is available at harness construction time, not inside each test. Throw with an installation hint so the developer knows immediately what is missing. Read `${CLAUDE_SKILL_DIR}/references/l2-patterns.md` for the full harness factory pattern.
</l2_patterns>

<l3_patterns>
`l3` tests require real credentials or remote services.

**Credential policy: always fail loudly. Skipping is forbidden.**

`it.skip`, `it.skipIf`, `test.skip`, and any other skip mechanism are forbidden for credentialed tests. A skipped test silently passes the suite while hiding missing evidence. When credentials are absent, the test must throw with a clear diagnostic.

```typescript
/**
 * l3 tests require these environment variables:
 *
 *   LHCI_SERVER_URL  - LHCI server base URL
 *   LHCI_TOKEN       - build token
 *
 * Where to find: 1Password "Engineering/Test Credentials"
 * Setup: cp .env.test.example .env.test and fill in values
 */

type Credentials = {
  serverUrl: string;
  token: string;
};

function requireCredentials(): Credentials {
  const serverUrl = process.env.LHCI_SERVER_URL;
  const token = process.env.LHCI_TOKEN;

  if (!serverUrl || !token) {
    throw new Error(
      "Missing LHCI_SERVER_URL or LHCI_TOKEN. See test file header for setup instructions.",
    );
  }

  return { serverUrl, token };
}

describe("LHCI", () => {
  let credentials: Credentials;

  beforeAll(() => {
    credentials = requireCredentials();
  });

  it("uploads audit results to server", async () => {
    const result = await uploadAuditResults({
      serverUrl: credentials.serverUrl,
      token: credentials.token,
      results: testResults,
    });

    expect(result.success).toBe(true);
  });
});
```

</l3_patterns>

<dependency_injection>
Tests verify behavior through real code paths. Avoid framework-level replacement of the dependency under test.

Forbidden patterns:

- `vi.mock(...)` replacing the module that should provide evidence
- `jest.mock(...)` replacing the module that should provide evidence
- `vi.spyOn(...).mockReturnValue(...)` replacing behavior that the test claims to verify

Allowed doubles are explicit objects or classes passed through dependency injection and mapped to a `/testing` Stage 5 exception, see `<router_mapping>` above

```typescript
interface PaymentGateway {
  charge(amountCents: number): Promise<ChargeResult>;
}

class RecordingGateway implements PaymentGateway {
  readonly charges: number[] = [];

  async charge(amountCents: number): Promise<ChargeResult> {
    this.charges.push(amountCents);
    return { id: "test-charge", status: "approved" };
  }
}
```

</dependency_injection>

<property_based_testing>
Property assertions about parsers, serializers, mathematical operations, or invariant-preserving algorithms require `fast-check` and a meaningful property.

| Code type               | Required property        | Pattern                  |
| ----------------------- | ------------------------ | ------------------------ |
| Parsers                 | `parse(format(x)) == x`  | `fc.assert(fc.property)` |
| Serialization           | `decode(encode(x)) == x` | `fc.assert(fc.property)` |
| Mathematical operations | algebraic laws           | `fc.assert(fc.property)` |
| Complex algorithms      | invariant preservation   | `fc.assert(fc.property)` |

`fc.assert` that only checks "does not throw" is insufficient. The property must fail when the requirement is broken.
</property_based_testing>

<test_data_policy>

**KEY INSIGHT:**Most code is not testable, or not testable in a maintainable way.

**REMEDIATION:**

Use the following decision table to determine, how to invoke the code under test. Run through this table for every assertion in the spec file separately. Every test file can only cover assertions of the same evidence type: mapping goes in one file, compliance goes in another file. See `<core_model>` above.

1. **Data that the source imports or should import**

ALWAYS verify that the code under test imports routes, selectors, ids, feature flags, registry names, and all other public constants from the module that owns them.

ALWAYS verify that the code under test imports standard values like HTTP status codes from the canonical source of the runtime (Node) or framework (e.g., React or Next.js).

<invalid_source_owned_constant>

```typescript
const PATH_SEPARATOR = "/";
```

</invalid_source_owned_constant>

<valid_source_owned_constant>

```typescript
// Use `-` to safely encode non-alphanumeric characters across branch names,
// Github actions and Vercel preview environment hostnames
const ENCODED_SEPARATOR = "-";
```

</valid_source_owned_constant>

2. **Data that the code under test owns or should own**

Most code under test Claude encounters will hardcode the same numbers and string literals several times in the source code.

This means the code is not testable in a maintainable way because any change to the source file will invalidate the test and lead to churn and extra work.

ALWAYS refactor the code under test so that it defines all constants, including numbers and string literals, in a constant dict or other suitable data structure.

<invalid_source_owned_constant>

```typescript
export function validateSemantics(verdict: AuditVerdict): readonly string[] {
  const hasFail = verdict.gates.some((g) => g.status === "FAIL");
  const hasSkipped = verdict.gates.some((g) => g.status === "SKIPPED");
  const hasPass = verdict.gates.some((g) => g.status === "PASS");
  // ...
}
```

</invalid_source_owned_constant>

<valid_source_owned_constant>

```typescript
export const VERDICT_STATUSES = {
  FAIL: "fail",
  SKIPPED: "skipped",
  PASS: "pass",
} as const;
export type AuthProviderType = (typeof VERDICT_STATUSES)[keyof typeof VERDICT_STATUSES];
export const authProviderSchema = z.enum(
  Object.values(VERDICT_STATUSES) as [string, ...string[]],
);
```

</valid_source_owned_constant>

ALWAYS make sure that these data structures reflect semantically what they represent.

<invalid_test_owned_constant>

```typescript
const VALID_VERDICTS = ["fail", "skipped", "pass"] as const;
```

</invalid_test_owned_constant>

3. **Data that only the test needs and hence owns**

**THERE ARE NO VALID TEST-OWNED CONSTANTS!**

ALWAYS refactor the code under test so it exports the semantically structured constant the test asserts on.

Then import one or very few of these constant objects into the test file. Any changes to the code under test are automatically reflected and the test requires zero maintenance.

<valid_test_data_sources>

<generators>

Use generators for inputs that vary per run. A generator is a pure function — it emits values, holds no state, and has no side effects. Use fast-check or faker.js for randomized scalars; use `fc.Arbitrary` for structured domain values.

```typescript
// testing/generators/{domain}.ts

// Generates valid spec-tree node paths drawn from config kinds
export function arbitraryNodePath(config: Config): fc.Arbitrary<string>;

// Generates valid spec-tree decision paths drawn from config kinds
export function arbitraryDecisionPath(config: Config): fc.Arbitrary<string>;

// Generates arbitrary SpecTreeFixture instances (arrays of typed path entries)
export function arbitrarySpecTree(config: Config): fc.Arbitrary<SpecTreeFixture>;
```

</generators>

<harnesses>

Use harnesses for tests that interact with external systems — filesystems, browsers, APIs, Docker. A harness manages setup and teardown of the external resource; it is not self-contained.

```typescript
// testing/harnesses/{domain}.ts

// Filesystem harness: manages a temp project directory for spec-tree operations
export async function withTestEnv(
  config: Config,
  callback: (env: SpecTreeEnv) => Promise<void>,
): Promise<void>;

// Browser harness: wraps Playwright with page lifecycle management
export function withPlaywright(testFn: BasePlaywrightTest): PlaywrightHarnessTest {
  return testFn.extend<PlaywrightHarnessFixtures>({
    playwrightHarness: async ({ page }, provideFixture) => {
      await provideFixture(createPlaywrightHarness(page));
    },
  });
}

export const test = withPlaywright(baseTest);
```

</harnesses>

<fixtures>

Use fixture files for real-world data the code under test would encounter: a captured JSONL from a chat session, a saved API response payload, a document the parser must handle. Fixture files live in `tests/fixtures/` alongside the test that uses them.

Strings and numbers are never valid fixtures. A string literal that represents a domain value belongs in the production module or a generator, not a static file or a test-file constant.

</fixtures>

- Keep descriptive test titles and assertion diagnostics inline; they are the only valid string literals in a test file.
- Use aliases such as `@testing/*` for shared test infrastructure
- Use co-located `./helpers` only when the helper serves one test file

</valid_test_data_sources>

</test_data_policy>

<test_infrastructure>
Shared test infrastructure lives in a `testing/` directory at the project root and is imported via path aliases.

```text
testing/
+-- harnesses/
|   +-- index.ts
|   +-- hugo.ts          # Hugo build harness
|   +-- postgres.ts      # PostgreSQL harness
|   +-- factories.ts     # Typed domain factories
+-- fixtures/
    +-- values.ts        # TYPICAL, EDGES collections
```

Configure the `@testing` alias in `tsconfig.json` and `vitest.config.ts`:

```typescript
import { createAuditResult } from "@testing/harnesses/factories";
import { createHugoHarness } from "@testing/harnesses/hugo";
```

Co-located `./helpers` are acceptable only when the helper serves a single test file. Anything shared across two or more test files belongs in `testing/`.

</test_infrastructure>

<script_testing>
Committed `scripts/` entrypoints get thin tests:

- Argument parsing through the repository's canonical parser
- Dispatch into the imported orchestrator
- Exit-code mapping and observable terminal output

The orchestrator carries the main behavioral evidence. Script files should stay small and route to tested modules.
</script_testing>

<anti_patterns>
Reject or rewrite these patterns:

- Legacy file suffixes: `.unit.test.ts`, `.integration.test.ts`, `.e2e.test.ts`, `.spec.ts`
- Runner-level collapse: assuming Playwright means `l3`
- Level-evidence collapse: assuming `scenario` means high-cost execution
- Framework mocks replacing the dependency under test
- Property claims implemented only with examples
- Source-owned values copied into local constants
- Production modules created only to aggregate values for tests
- Deep relative imports into stable shared test infrastructure
- Manual argument parsing in script tests when the repo has a canonical parser
- `it.skip`, `it.skipIf`, and `test.skip` on credentialed evidence -- use `requireCredentials()` that throws instead

The cross-file literal-reuse check (check IDs `L3`/`L4`: literal in a test also present in `src/`, or duplicated across test files) is not an ESLint rule — it runs as `spx validation literal` because cross-file analysis doesn't fit ESLint's per-file execution model.

<playwright_request_context>

Playwright's `{ request }` fixture uses its own `APIRequestContext` that does NOT share cookies with the `BrowserContext`. Cookies set via `context.addCookies(...)` do not reach `{ request }`.

```typescript
// WRONG: request fixture -- no cookie inheritance
test("API returns flag-gated payload", async ({ request }) => {
  const response = await request.get("/api/data"); // cookie absent
  expect(await response.json()).toContain(FLAGGED_ITEM); // fails
});

// RIGHT: context.request -- shares cookies with browser context
test("API returns flag-gated payload", async ({ context }) => {
  const response = await context.request.get("/api/data"); // cookie present
  expect(await response.json()).toContain(FLAGGED_ITEM);
});
```

`page.request` also shares cookies with the browser context and works when a test already uses a page.

</playwright_request_context>

</anti_patterns>

<reference_guides>

| File                                                          | When to read                                                  |
| ------------------------------------------------------------- | ------------------------------------------------------------- |
| `${CLAUDE_SKILL_DIR}/references/l1-patterns.md`               | Writing pure function, typed factory, or temp dir tests       |
| `${CLAUDE_SKILL_DIR}/references/exception-implementations.md` | Implementing a Stage 5 exception from `/testing`              |
| `${CLAUDE_SKILL_DIR}/references/l2-patterns.md`               | Writing tests that require real infrastructure (Docker, etc.) |

</reference_guides>

<success_criteria>
TypeScript test guidance follows this standard when:

- `/testing` determines the evidence mode, execution level, and exception path before implementation
- Test filenames use `<subject>.<evidence>.<level>[.<runner>].test.ts`
- Runner configuration uses explicit runner tokens instead of `.spec.ts`
- Doubles are passed through dependency injection and mapped to a Stage 5 exception
- Property assertions use meaningful `fast-check` properties
- Source-owned values come from the owning production module
- Shared test infrastructure lives in test-owned code behind stable aliases

</success_criteria>
