---
name: standardizing-typescript-testing
disable-model-invocation: true
description: >-
  TypeScript testing standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Define TypeScript testing standards and patterns that other skills reference. Not invoked directly -- invoke `/testing-typescript` to write tests or `/auditing-typescript-tests` to audit them instead. Load `/standardizing-typescript` before this reference. These standards apply to ALL TypeScript test code.
</objective>

<quick_start>
Reference this skill for:

- Level routing from `/testing` decisions into TypeScript
- Level tooling and framework expectations
- File naming conventions
- Dependency injection and allowed doubles
- Harness ownership and path alias usage
- Property-based testing requirements
- Source-owned values, inline diagnostics, and test-data policy
- Fixture and harness placement
- Test anti-patterns to reject

</quick_start>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/typescript-tests.md` at the repository root. Read that file after `spx/local/typescript.md` if it exists and apply it as the repo-local specialization.
</repo_local_overlay>

<router_to_typescript_mapping>
After running through `/testing`, use this mapping:

| Router Decision                                 | TypeScript Implementation                        |
| ----------------------------------------------- | ------------------------------------------------ |
| **Stage 2 → Level 1**                           | Vitest + temp dirs + type-safe DI                |
| **Stage 2 → Level 2**                           | Vitest + harness classes + Docker                |
| **Stage 2 → Level 3**                           | Vitest (CLI/API) or Playwright (browser)         |
| **Stage 3A** (Pure computation)                 | Pure functions with explicit types               |
| **Stage 3B** (Extract pure part)                | Factor into typed pure functions + thin wrappers |
| **Stage 5 Exception 1** (Failure modes)         | Interface + stub class returning errors          |
| **Stage 5 Exception 2** (Interaction protocols) | Spy class with typed call recording              |
| **Stage 5 Exception 3** (Time/concurrency)      | `vi.useFakeTimers()` or injected clock           |
| **Stage 5 Exception 4** (Safety)                | Stub class that records but doesn't execute      |
| **Stage 5 Exception 6** (Observability)         | Spy class capturing typed request details        |

</router_to_typescript_mapping>

<level_tooling>

| Level          | Infrastructure                                  | Framework  | Speed |
| -------------- | ----------------------------------------------- | ---------- | ----- |
| 1: Unit        | Node.js stdlib + temp dirs + standard dev tools | Vitest     | <50ms |
| 2: Integration | Docker containers + project-specific binaries   | Vitest     | <1s   |
| 3: E2E         | Network services + external APIs                | Vitest     | <30s  |
| 3: Browser E2E | Chrome + real user flows                        | Playwright | <30s  |

**Standard dev tools** (Level 1): git, node, npm, curl -- available in CI without setup.
**Project-specific tools** (Level 2): Docker, Hugo, Caddy, PostgreSQL -- require installation.

</level_tooling>

<file_naming>
Test filenames encode the evidence level:

| Level | Filename suffix        | Example                       |
| ----- | ---------------------- | ----------------------------- |
| 1     | `.unit.test.ts`        | `uart-tx.unit.test.ts`        |
| 2     | `.integration.test.ts` | `uart-tx.integration.test.ts` |
| 3     | `.e2e.test.ts`         | `uart-tx.e2e.test.ts`         |

</file_naming>

<dependency_injection>
Tests verify behavior against real code paths. Do not use `vi.mock`, `jest.mock`, or `vi.spyOn(...).mockReturnValue(...)` as substitutes for the dependency itself.

Use controlled implementations that preserve the real interface:

- **Failure modes**: class implementing an interface and throwing realistic errors
- **Interaction protocols**: class with call-recording state
- **Time/concurrency**: `vi.useFakeTimers()` or injected clock dependency
- **Safety**: class that records intent without destructive effects
- **Observability**: class capturing request details that the real integration hides

These doubles belong in test-owned code. They live next to the test, in `testing/harnesses/`, or in a shared helper package behind a stable alias such as `@testing/*`.
</dependency_injection>

<property_based_testing>
Property assertions about parsers, serializers, mathematical operations, or invariant-preserving algorithms require `fast-check` and a meaningful property. Example-based tests alone are insufficient.

| Code type               | Required property        | Framework                |
| ----------------------- | ------------------------ | ------------------------ |
| Parsers                 | `parse(format(x)) == x`  | fast-check / `fc.assert` |
| Serialization           | `decode(encode(x)) == x` | fast-check / `fc.assert` |
| Mathematical operations | Algebraic properties     | fast-check / `fc.assert` |
| Complex algorithms      | Invariant preservation   | fast-check / `fc.assert` |

Properties must assert something falsifiable. `fc.assert` that only checks "does not throw" is a rejection case.
</property_based_testing>

<test_data_policy>
Prefer canonical sources over duplicated literals in tests.

- Import source-owned copy, selectors, ids, routes, feature-flag keys, and similar declarations from the production module that owns them.
- Keep descriptive test titles and `expect(..., "message")` diagnostics inline at the call site. Do not wrap them in local constants.
- When a repeated value is test-local, generate it or place it in a harness instead of creating ad hoc local constants.
- Stable test-only fixture strings, dates, ids, and expected-output snippets belong in `testing/fixtures/{domain}.ts`.
- When tests need an aggregate of source-owned values for convenience, create a test-owned harness module. Do not create production re-export wrappers only to simplify test imports.

</test_data_policy>

<harness_ownership>
Test-owned infrastructure stays in test-owned code:

- Shared helpers and doubles: `testing/harnesses/`
- Stable fixture data: `testing/fixtures/`
- Co-located helpers that exist only for one test file: `./helpers`

Use path aliases such as `@testing/*` for shared test infrastructure. Avoid deep relative imports into stable test infrastructure.
</harness_ownership>

<script_testing>
Checked-in entrypoints under `scripts/` get thin tests.

- Test argument parsing through the repository's canonical parser
- Test dispatch into the orchestrator
- Test exit-code mapping and observable terminal output

Do NOT treat the script file as the main unit of behavior. The imported orchestrator module carries the real specification and evidence.

For script-driven work, ask the same harness-first questions:

1. Where is the harness for the orchestrator's boundary?
2. If there is no harness, where is the fixture data?
3. Where is the spec for the orchestrator or harness?
4. Where are the tests for the orchestrator or harness?

</script_testing>

<anti_patterns>
Reject these patterns in TypeScript tests:

- `vi.mock`, `jest.mock`, or `vi.spyOn(...).mockReturnValue(...)` replacing the dependency under test
- Property assertions implemented only with examples
- Source-owned values copied into local constants instead of imported from production modules
- Titles and assertion diagnostics extracted into constant declarations
- Production `src/` modules created only to aggregate values for tests
- Deep relative imports into stable shared test infrastructure
- Manual argument parsing in checked-in script tests when the repo has a canonical parser

</anti_patterns>

<success_criteria>
TypeScript tests follow this reference when:

- `/testing` determines the level and exception path first
- Filenames communicate the intended evidence level
- Doubles preserve the real interface instead of replacing it with mocking APIs
- Property assertions use `fast-check` with meaningful properties
- Source-owned values are imported from their canonical modules
- Repeated test-local data lives in generators, fixtures, or harnesses
- Shared test infrastructure lives in test-owned code behind stable aliases
- Script entrypoints stay thin while orchestrators carry the real harness-backed evidence

</success_criteria>
