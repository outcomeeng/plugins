---
name: test-typescript
description: >-
  ALWAYS invoke this skill when writing or fixing tests for TypeScript.
argument-hint: "<full-spx-node-path>"
arguments: node_path
allowed-tools: Read, Glob, Grep, Write, Edit, Skill, Bash(npx tsc:*), Bash(npx eslint:*), Bash(npx vitest:*)
---

Invoke the `typescript:typescript-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `typescript:typescript-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `spec-tree:test` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
TypeScript test files that supply evidence for a node specification's assertions.
</objective>

<input_contract>
`$node_path` is the full `spx/...` path to the governing node. If `$node_path` is empty, stop and report that the governing node path is required before test evidence can be written or repaired.
</input_contract>

<mode_detection>
**Determine the current mode:**

1. **WRITE mode** - Tests do not exist yet, or starting fresh
   - Check: Glob `$node_path/tests/*.ts`; no matches or only scaffold files means WRITE mode
   - Action: Follow full workflow below

2. **FIX mode** - Tests exist but were rejected by reviewer
   - Check: Recent `/audit-typescript-tests` output shows `REJECTED` with specific failing rows or findings
   - Action: Read the rejection, fix the specific issues, re-run tests

**Always check which mode before proceeding.**
</mode_detection>

<quick_start>
**Input:** Governing node path from `$node_path`

**Output:** Test files written to `$node_path/tests/` directory

**Prerequisites:** Standards and the `/test` router are pre-loaded above. After `/verify` selects test, `/test` chooses the assertion type and level; this skill implements those decisions in TypeScript.

**Command placeholders:** Resolve `<product-test-command>`, `<product-typecheck-command>`, `<product-lint-command>`, and optional `<product-lint-fix-command>` from repository docs, package scripts, Makefile, Justfile, or local agent instructions. When sources conflict, use this priority: local agent instructions, repository docs, Justfile, Makefile, package scripts, raw tool fallback. Fallback examples for repos without wrappers: `npx vitest run`, `npx tsc --noEmit`, `npx eslint src/ test/`, and `npx eslint src/ test/ --fix`. If a wrapper rejects a path suffix, run the closest supported focused command and record the exact command used.

`allowed-tools` preapproves only the listed raw-tool fallbacks. A repository-canonical wrapper outside those patterns uses the runtime's normal per-call approval path; NEVER select a fallback merely to avoid that approval.

**Workflow:**

```
Check mode -> WRITE or FIX -> Execute -> Verify -> Report
```

</quick_start>

<write_mode_workflow>

**WRITE Mode: Creating New Tests**

**Step 1: Load Context**

Require a live `<SPEC_TREE_FOUNDATION>` marker, invoking `/understand` when absent. Invoke `/contextualize` with the full node path and require the matching live `<SPEC_TREE_CONTEXT>` marker before reading test bodies or writing evidence. Use that context rather than reconstructing ancestor, sibling, or decision reads with shell commands.

Extract from the spec:

- **Assertions** - Typed assertions to verify
- **Test Strategy** - Which levels are specified
- **Harnesses** - Any referenced test harnesses

**Step 2: Determine Evidence and Level**

For each assertion, apply the `/test` methodology:

| Evidence location               | Minimum level |
| ------------------------------- | ------------- |
| Pure computation/algorithm      | `l1`          |
| File I/O with temp dirs         | `l1`          |
| Standard dev tools (git, curl)  | `l1`          |
| Product-specific binary         | `l2`          |
| Database, Docker                | `l2`          |
| Real credentials, external APIs | `l3`          |

**Step 3: Apply the source-contract-first gate**

Read the assertion, the existing or planned test, and the TypeScript code under test. State the production contract the evidence exercises. If the source does not expose the needed type, enum, constructor, schema, parser entry point, registry, route, command, dependency boundary, or observable behavior, fix the source contract before writing test predicates.

Do not patch a predicate around a reviewer example, copy source literals into tests, hide values in fixtures or generators, or replace the behavior under test with a mock.

**Step 4: Write Test Files**

Create test files following `/typescript-test-standards`:

**Mandatory elements:**

- File naming: `<subject>.<evidence>.<level>[.<runner>].test.ts`
- Type annotations on all interfaces and function parameters
- No test-file `const`, `let`, `var`, fixture-parameter, or property-parameter declarations; import source-owned values from production modules and call harnesses or generators inline
- Property-based tests for parsers/serializers/math (`assertProperty(parserRoundtripProperty())`)
- No `vi.mock()` or `vi.fn()` replacing the dependency under test -- use typed DI interfaces
- Vitest as default runner; `playwright` runner token when needed

**Step 5: Verify Tests Fail (RED)**

```bash
# Resolve from repo docs or scripts; fallback: npx vitest run
<product-test-command> $node_path/tests/
```

If the canonical wrapper rejects a path suffix, run the closest supported focused command and record the exact command used. For example, use a wrapper-provided filter flag, a package script that accepts `--`, or the full product test command when no focused form exists.

Tests should FAIL with import errors or assertion errors (implementation does not exist yet).

**Step 6: Handle Specified Nodes**

If the implementation module does not exist yet, tests fail on import -- breaking the quality gate. Add the portion of `$node_path` relative to `spx/` to `spx/EXCLUDE` using the repository's file-editing tool.

The `spx` CLI reads this file and skips excluded nodes when running `spx test passing`. Remove the entry from `spx/EXCLUDE` when implementation begins.

</write_mode_workflow>

<literal_reuse_remediation>

**Literal-Reuse Findings: What They Mean and How to Fix Them**

The literal checker (`spx validation literal`) reports two finding kinds:

- `[reuse]` — a string/number in a test file also appears in a source file
- `[dupe]` — the same string/number appears in two or more test files

**These findings are a test quality signal, not a naming problem.**

When a specific value like `"src/foo.ts"` appears in three test files, those three tests are asserting that the code handles exactly that path. They confirm the author's expectation about one hand-picked input. They reveal nothing about inputs the author didn't think of.

**The WRONG fix: shared constants ("literal laundering")**

```typescript
// ❌ REJECTED: moving the hardcoded string to a constant changes nothing
const FIXTURE_SOURCE_PATH = "src/foo.ts";
expect(result).toBe(FIXTURE_SOURCE_PATH);
```

This is literal laundering. The test now uses a named constant, but it still asserts on a single specific value chosen by the test author. The bug-finding surface is identical — zero.

Shared test-owned constants that group hardcoded values (`TEST_FIXTURES`, `SAMPLE_PATHS`, etc.) are the same antipattern at scale.

**The RIGHT fix: source contracts and domain generators**

Every string or number in a test represents either source-owned protocol data or an input domain. Identify the owner first.

When the value is source-owned, improve the code under test so the owner exports a registry, typed constructor, or source-owned constant, then import that source API directly. When the value is test input with a real domain, use or create an `fc.Arbitrary` for it:

```typescript
import { arbitrarySourceFilePath } from "@testing/generators/paths";
import { assertProperty } from "@testing/harnesses/properties";
import { sourcePathProcessingProperty } from "@testing/harnesses/properties/source-paths";

assertProperty(
  sourcePathProcessingProperty(arbitrarySourceFilePath(), processPath),
);
```

**Decision table for literal-reuse findings**

| Finding                                                | What the value represents                                | Fix                                                                   |
| ------------------------------------------------------ | -------------------------------------------------------- | --------------------------------------------------------------------- |
| Value also appears in `src/`                           | Source-owned constant (command name, status token, etc.) | Import the constant from the production module                        |
| Value is a source-owned singleton shape                | Source contract                                          | Export a typed constructor or registry from source, then import it    |
| Value is variable input data (path, name, ID, content) | Domain value                                             | Use or create an `fc.Arbitrary` in `testing/generators/`              |
| Value is an expected output                            | Derived from input                                       | Compute it from the input inside the property test                    |
| Value is a specific error message that IS the contract | Exact error text                                         | Allowed only in compliance tests that assert the exact message format |

**When no generator exists for the domain**

Create one only when the domain has meaningful variability or composition. The generator lives in `testing/generators/{domain}.ts` and is imported via `@testing/generators/{domain}`.

Do not create a generator that only returns `fc.constant(...)` for a singleton object. Improve the source module so it owns that constructor, then import it directly.

**The only valid hardcoded strings in test files**

- `describe` / `it` block titles
- Exact error message text in compliance tests where the format IS the contract (not a guess)
- Import paths

Everything else is source-owned data (import it), source-owned construction (export and import it), or variable input data (generate it).

</literal_reuse_remediation>

<fix_mode_workflow>

**FIX Mode: Fixing Rejected Tests**

**Step 1: Read Rejection Feedback**

Find the most recent `/audit-typescript-tests` output. Look for:

- Specific file:line locations
- Issue categories (evidentiary gap, missing property tests, etc.)
- Required fixes

**Step 2: Apply Fixes**

For each rejection reason:

| Rejection Category             | Fix Action                                                              |
| ------------------------------ | ----------------------------------------------------------------------- |
| Evidentiary gap                | Rewrite test to actually verify the assertion                           |
| `vi.mock()` detected           | Replace with typed DI interface                                         |
| `vi.fn()` testing call details | Replace with typed spy class or recording object                        |
| Missing property tests         | Add `assertProperty(parserRoundtripProperty())` for parsers/serializers |
| Source-owned value redefined   | Import from production module instead                                   |
| Wrong filename axes            | Rename to `<subject>.<evidence>.<level>[.<runner>].test.ts`             |
| Literal `[dupe]` / `[reuse]`   | See `<literal_reuse_remediation>` — generators, not shared constants    |

**Step 3: Verify Fixes**

```bash
# Run the node tests through the repository's canonical test command; fallback: npx vitest run
<product-test-command> $node_path/tests/

# Run the repository's canonical TypeScript validation; fallback: npx tsc --noEmit
<product-typecheck-command>

# Run the repository's canonical lint validation for the changed files; fallback: npx eslint src/ test/
<product-lint-command> $node_path/tests/
```

**Step 4: Report What Was Fixed**

```markdown
**Tests Fixed**

**Issues Addressed**

| Issue           | Location       | Fix Applied                       |
| --------------- | -------------- | --------------------------------- |
| vi.mock() usage | foo.test.ts:15 | Replaced with typed DI interface  |
| Magic value     | foo.test.ts:23 | Imported STATUS_CODES from module |

**Verification**

- Test command: `<exact command>` — `<required RED or GREEN result>`
- Type-check command: `<exact command>` — passed
- Lint/format command: `<exact command>` — passed

If a required command cannot pass, report the exact command and blocking cause instead of claiming the tests are ready for re-review.
```

</fix_mode_workflow>

<test_writing_checklist>

Before declaring tests complete:

- [ ] Each spec assertion has at least one test
- [ ] Assertion type and level match `/test` Stage 2
- [ ] File names use `<subject>.<evidence>.<level>[.<runner>].test.ts`
- [ ] Test files contain no `const`, `let`, `var`, fixture-parameter, or property-parameter declarations
- [ ] No `vi.mock()` or `vi.fn()` replacing the dependency under test
- [ ] Doubles are typed interfaces passed through DI
- [ ] Property assertions use meaningful `fast-check` properties through a seed-reporting wrapper
- [ ] Source-owned values imported from production modules
- [ ] Source-owned singleton shapes come from production constructors, not test constants or constant-only generators
- [ ] Variable input data comes from generators (`fc.Arbitrary`), not hardcoded constants
- [ ] No test-owned constant groups like `TEST_FIXTURES`, `SAMPLE_PATHS`, etc.
- [ ] Tests run and fail for expected reasons (RED phase)

</test_writing_checklist>

<patterns_reference>

See `/typescript-test-standards` for:

- **File naming** - Evidence, level, and runner axes
- **Level tooling** - Vitest vs Playwright, l1/l2/l3 infrastructure
- **Router mapping** - `/test` Stage decisions to TypeScript patterns
- **l1 patterns** - Pure functions, typed factories, temp dirs
- **Exception implementations** - The 6 exception cases in TypeScript
- **l2 patterns** - Typed harness factory and usage
- **l3 patterns** - Credential management, fail-loudly policy
- **Dependency injection** - Typed interfaces and recording doubles
- **Property-based testing** - `fast-check` patterns
- **Test data policy** - Source-owned constants, generators, harnesses, fixtures
- **Anti-patterns** - What to reject or rewrite

Read the matching level guide from `/typescript-test-standards` after choosing a level:

- `/typescript-test-standards` `levels/l1-local-deterministic.md` - pure functions, temp dirs, standard local tools, Stage 5 doubles
- `/typescript-test-standards` `levels/l2-local-infrastructure.md` - Docker, local services, browsers, and product binaries
- `/typescript-test-standards` `levels/l3-remote-credentialed.md` - remote services, shared environments, and credentials

Also check for `spx/local/typescript-tests.md` at the repository root -- product-specific overrides apply after this reference.

</patterns_reference>

<output_format>

**WRITE mode output:**

```markdown
**Tests Written**

**Node: $node_path**

**Test Files Created**

| File                            | Level | Assertions Covered |
| ------------------------------- | ----- | ------------------ |
| `tests/foo.scenario.l1.test.ts` | `l1`  | Assertion 1, 2     |

**Test Run (RED Phase)**

Tests fail as expected. Ready for review.
```

**FIX mode output:**

```markdown
**Tests Fixed**

**Issues Addressed**

| Issue   | Location    | Fix Applied |
| ------- | ----------- | ----------- |
| {issue} | {file:line} | {fix}       |

**Verification**

- Test command: `{exact command}` — `{required RED or GREEN result}`
- Type-check command: `{exact command}` — passed
- Lint/format command: `{exact command}` — passed

The checklist and every required validation pass. Ready for re-review.
```

</output_format>

<success_criteria>

Test evidence is ready for review when:

- [ ] Every created or changed test file lives in the governed node's `tests/` directory and is linked from the corresponding spec assertion
- [ ] The test filenames and assertion mapping follow `/typescript-test-standards` and any `spx/local/typescript-tests.md` overlay loaded for the repository
- [ ] The product's resolved TypeScript test command demonstrates the required RED or GREEN phase result for the governed node or changeset
- [ ] FIX mode addresses every supplied reviewer finding with a test change or a stated evidence-based rejection
- [ ] In FIX mode, the product's resolved TypeScript type-check and lint/format commands pass; otherwise the report names each blocked command and its exact blocking cause and does not claim readiness

</success_criteria>
