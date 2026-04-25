---
name: standardizing-typescript-tests
user-invocable: false
description: >-
  TypeScript testing standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Define TypeScript-specific test standards loaded by `/testing-typescript`, `/coding-typescript`, `/architecting-typescript`, and `/auditing-typescript-tests`.

Read `/testing` first when deciding what evidence to create. Read `/standardizing-typescript` before this reference when writing or reviewing TypeScript test code. These standards apply to all TypeScript tests.
</objective>

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

| Router Decision                            | TypeScript implementation                         |
| ------------------------------------------ | ------------------------------------------------- |
| Stage 2 -> `l1`                            | Vitest, typed factories, temp dirs, pure helpers  |
| Stage 2 -> `l2`                            | Vitest or Playwright with local real dependencies |
| Stage 2 -> `l3`                            | Vitest or Playwright with credentials or network  |
| Stage 3A: pure computation                 | Direct tests of typed pure functions              |
| Stage 3B: extract pure part                | Pure helper at `l1`, boundary at outer level      |
| Stage 5 exception 1: failure simulation    | Interface implementation that throws/errors       |
| Stage 5 exception 2: interaction protocols | Spy class with typed call recording               |
| Stage 5 exception 3: time/concurrency      | Injected clock or `vi.useFakeTimers()`            |
| Stage 5 exception 4: safety                | Class that records intent without side effects    |
| Stage 5 exception 5: combinatorial cost    | Configurable fake with real-shaped behavior       |
| Stage 5 exception 6: observability         | Spy that captures hidden boundary details         |
| Stage 5 exception 7: contract probes       | Stub validated against the contract schema        |

</router_mapping>

<dependency_injection>
Tests verify behavior through real code paths. Avoid framework-level replacement of the dependency under test.

Forbidden patterns:

- `vi.mock(...)` replacing the module that should provide evidence
- `jest.mock(...)` replacing the module that should provide evidence
- `vi.spyOn(...).mockReturnValue(...)` replacing behavior that the test claims to verify

Allowed doubles are explicit objects or classes passed through dependency injection and mapped to a `/testing` Stage 5 exception.

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
Use source-owned values when the production system owns them.

- Import routes, selectors, ids, feature flags, registry names, and public constants from the module that owns them
- Keep descriptive test titles and assertion diagnostics inline
- Put stable test-only strings, ids, dates, and expected-output snippets in `testing/fixtures/{domain}.ts`
- Put shared harnesses, generated data, and Stage 5 doubles in `testing/harnesses/`
- Use aliases such as `@testing/*` for shared test infrastructure
- Use co-located `./helpers` only when the helper serves one test file

</test_data_policy>

<script_testing>
Checked-in `scripts/` entrypoints get thin tests:

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

</anti_patterns>

<lint_enforcement>
These standards are mechanically enforced by ESLint rules shipped in `${CLAUDE_SKILL_DIR}/eslint-rules/`. Coding agents MUST be able to see these rules while writing tests — this is where the standards live, not in the audit skill. The audit just invokes them.

| Rule                                  | Check ID | Standard enforced                                                                                                                                                   |
| ------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `audit/no-test-filename-violations`   | F1–F5    | `<file_naming>` — canonical `<subject>.<evidence>.<level>[.<runner>].test.ts`; legacy suffixes (`.unit`, `.integration`, `.e2e`, `.spec`) rejected                  |
| `audit/no-literal-test-strings`       | L1       | `<test_data_policy>` — source-owned values; literals only in descriptive callsites (`it`/`describe`/`test`/`expect` message) and policy-defined protocol exceptions |
| `audit/no-literal-test-numbers`       | L2       | `<test_data_policy>` — numeric literals only in `{-1, 0, 1, 2}`; precision args to `toBeCloseTo` must be named                                                      |
| `audit/no-ad-hoc-test-constants`      | C1       | `<test_data_policy>` — module-scope `const` backed by literal data is an ad-hoc constant regardless of naming                                                       |
| `audit/no-bdd-try-catch-anti-pattern` | B1       | BDD assertion behaviour — `expect()` inside `try/catch` without re-throw silently swallows failures                                                                 |
| `audit/no-mock-api` (warn)            | M1–M2    | `<dependency_injection>` — surfaces mock/stub/network-replacement call sites so they can be mapped to a `/testing` Stage 5 exception                                |
| `no-restricted-imports`               | H2       | `<test_data_policy>` — no deep relative imports into `testing/`; use `@testing/*` alias                                                                             |

The cross-file literal-reuse check (check IDs `L3`/`L4`: literal in a test also present in `src/`, or duplicated across test files) is not an ESLint rule — it runs as `spx validation literal` because cross-file analysis doesn't fit ESLint's per-file execution model. The heuristics (`MIN_STRING_LENGTH`, `MIN_NUMBER_DIGITS`, and the `COMMON_LITERAL_ALLOWLIST` covering HTTP methods, JS type names, Node.js builtin module specifiers, common CSS keywords) are shared between the per-file rules and the cross-file detector via `${CLAUDE_SKILL_DIR}/eslint-rules/literal-signal.ts`.

The default policy files at `${CLAUDE_SKILL_DIR}/eslint-rules/config/test-string-policy.ts` and `${CLAUDE_SKILL_DIR}/eslint-rules/config/test-number-policy.ts` permit the descriptive callsites for Vitest, Jest, and Playwright, plus ARIA-role, Playwright load-state, and DOM-attribute protocol exceptions. Consumers override by shipping an `eslint.audit.config.ts` at the repo root.

To invoke locally while writing tests (equivalent to what Gate 0 runs):

```bash
pnpm eslint \
  --config ${CLAUDE_SKILL_DIR}/eslint-rules/eslint.audit.config.ts \
  --format stylish \
  <your-tests>/
```

</lint_enforcement>

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
