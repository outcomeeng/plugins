---
name: test-typescript
description: >-
  ALWAYS invoke this skill when writing or fixing tests for TypeScript.
argument-hint: "<full-spx-node-path>"
arguments: node_path
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, Skill
---

{!% require_skill 'typescript:typescript-standards' %!}

{!% require_skill 'typescript:typescript-test-standards' %!}

{!% require_skill 'test' %!}

<context>

!`test -f spx/local/typescript.md && sed -n '1,400p' spx/local/typescript.md || true`

!`test -f spx/local/typescript-tests.md && sed -n '1,400p' spx/local/typescript-tests.md || true`

</context>

<objective>
TypeScript test files that supply evidence for a node specification's assertions.
</objective>

<input_contract>
Resolve `$node_path` from the optional argument. When it is empty, use the full target node path from the live `<SPEC_TREE_CONTEXT>` marker. Stop only when neither source provides a governing node path.
</input_contract>

<mode_detection>
**Determine the current mode:**

1. **WRITE mode** - Tests do not exist yet, or starting fresh
   - Check: `ls $node_path/tests/*.ts` returns nothing or minimal files
   - Action: Follow full workflow below

2. **FIX mode** - Tests exist but were rejected by `test-evidence-auditor`
   - Check: Merged `test-evidence-auditor` JSON has `overall: REJECTED` or a `FAIL` row with TypeScript findings
   - Action: Read the rejection, fix the specific issues, re-run tests

**Always check which mode before proceeding.**
</mode_detection>

<quick_start>
**Input:** Governing node path from `$node_path`

**Output:** Test files written to `$node_path/tests/` directory

**Prerequisites:** Standards and the `/test` router are pre-loaded above. The router chooses evidence and level; this skill implements those decisions in TypeScript.

**Command placeholders:** Resolve `<product-test-command>`, `<product-typecheck-command>`, `<product-lint-command>`, and optional `<product-lint-fix-command>` from repository docs, package scripts, Makefile, Justfile, or local agent instructions. When sources conflict, use this priority: local agent instructions, repository docs, Justfile, Makefile, package scripts, raw tool fallback. Fallback examples for repos without wrappers: `npx vitest run`, `npx tsc --noEmit`, `npx eslint src/ test/`, and `npx eslint src/ test/ --fix`. If a wrapper rejects a path suffix, run the closest supported focused command and record the exact command used.

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

Complete the generic `/test` assertion-to-evidence matrix with the TypeScript form required by `/typescript-test-standards`:

| Assertion type | Required TypeScript evidence form                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------------ |
| Scenario       | A concrete behavior path with assertion-relevant expectations for every clause                               |
| Mapping        | `it.each`, `describe.each`, or `test.each` over at least two source-owned or generated cases                 |
| Conformance    | The applicable schema or external validator                                                                  |
| Property       | A meaningful arbitrary and invariant executed through the seed-reporting `assertProperty(...)` harness       |
| Compliance     | For `[test]`, a deliberate violating fixture that proves enforcement; route semantic-only rules to `[audit]` |

For every row, record the linked evidence file, coupling path through imported infrastructure to source behavior, concrete falsifying mutation, and assertion-relevant source branches reached by reading. Stop before Step 3 when any assertion lacks a complete row or any planned evidence lives in a file whose evidence lane differs from the assertion link.

**Step 3: Apply the source-contract-first gate**

Read the assertion, the existing or planned test, and the TypeScript code under test. State the production contract the evidence exercises. If the source does not expose the needed type, enum, constructor, schema, parser entry point, registry, route, command, dependency boundary, or observable behavior, fix the source contract before writing test predicates.

Do not patch a predicate around one audit finding, copy source literals into tests, hide values in fixtures or generators, or replace the behavior under test with a mock.

**Step 4: Write Test Files**

Create test files following `/typescript-test-standards`:

**Mandatory elements:**

- File naming: `<subject>.<evidence>.<level>[.<runner>].test.ts`
- Type annotations on all interfaces and function parameters
- No test-file `const`, `let`, `var`, fixture-parameter, or property-parameter declarations; import source-owned values from production modules and call harnesses or generators inline
- Property-based tests for parsers/serializers/math (`assertProperty(parserRoundtripProperty())`)
- No `vi.mock()` or `vi.fn()` replacing the dependency under test -- use typed DI interfaces
- Vitest as default runner; `playwright` runner token when needed

**Step 5: Run deterministic verification gates**

```bash
# Resolve from repo docs or scripts; fallback: npx vitest run
<product-test-command> $node_path/tests/

# Resolve from repo docs or scripts; fallback: npx tsc --noEmit
<product-typecheck-command>

# Resolve from repo docs or scripts; fallback: npx eslint src/ test/
<product-lint-command> $node_path/tests/
```

If the canonical wrapper rejects a path suffix, run the closest supported focused command and record the exact command used. For example, use a wrapper-provided filter flag, a package script that accepts `--`, or the full product test command when no focused form exists.

The focused test gate passes in WRITE mode only when tests fail for the expected missing implementation or assertion mismatch. Collection, syntax, harness, or configuration failures fail the gate. The typecheck and lint gates pass only with zero exit status. Stop before Step 6 unless all three gates pass.

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

Reread `/typescript-test-standards`, then read the most recent merged `test-evidence-auditor` JSON and the TypeScript findings appended to its gate rows. Treat `overall: REJECTED` or a `FAIL` row as proof that the prior authoring pass applied the shared standards incompletely.

Rebuild the assertion-to-evidence matrix across every affected assertion before editing. Include:

- assertion type and linked evidence file
- required TypeScript evidence form and type-specific obligations
- coupling path through every harness, generator, fixture path, and source contract
- one falsifying mutation for every clause
- every assertion-relevant source branch reached by the evidence

Sweep every same-class instance across the complete matrix. Do not treat findings as independent line-local patch requests.

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

Tests run and fail for expected reasons (RED phase complete).
```

</fix_mode_workflow>

<test_writing_checklist>

Before declaring tests complete:

- [ ] Each spec assertion has at least one test
- [ ] Assertion type and level match `/test` Stage 2
- [ ] The complete assertion-to-evidence matrix records each assertion's linked lane, required TypeScript form, coupling path, clause mutations, and relevant-path coverage
- [ ] Mapping evidence uses `it.each`, `describe.each`, or `test.each` over at least two cases
- [ ] `[test]` compliance evidence exercises a deliberate violating fixture
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
- **Exception implementations** - The 7 exception cases in TypeScript
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

Tests fail for the expected RED reason; typecheck and lint pass. Ready for test-evidence audit.
```

**FIX mode output:**

```markdown
**Tests Fixed**

**Issues Addressed**

| Issue   | Location    | Fix Applied |
| ------- | ----------- | ----------- |
| {issue} | {file:line} | {fix}       |

**Verification**

Tests pass the deterministic checklist. Ready for audit redispatch.
```

</output_format>

<failure_modes>

**Failure 1: Copied surrounding test structure instead of applying the shared standard**

What happened: Claude placed reusable setup, local reading factories, parameterized case bindings, and direct `fc.assert` calls in executed test files because nearby tests used that shape.

Why it failed: Existing tests have no authority over `/typescript-test-standards`. Executed test files own assertion flow only; harnesses own reusable setup and property execution through the seed-reporting wrapper.

How to avoid: Complete the assertion-to-evidence matrix from the shared standard before reading surrounding tests as implementation examples. Reject any planned local declaration, fixture parameter, property parameter, or direct property execution before writing.

**Failure 2: Repaired successive findings instead of rebuilding the complete matrix**

What happened: Claude moved setup into a harness after one rejection, added uncovered cases after another, corrected assertion classification after a third, and still compared only selected reading fields although the assertion required every other field to remain unchanged.

Why it failed: Each repair targeted the cited line while leaving another clause, path, or oracle outside the design. The auditor and authoring workflow shared the same standards; repeated rejection proved incomplete application of those standards.

How to avoid: On every rejection, discard the prior matrix, reread `/typescript-test-standards`, and rebuild every affected assertion row with its complete observable, linked lane, coupling path, falsifying mutations, and relevant-path coverage before editing.

**Failure 3: Put valid evidence in the wrong linked lane**

What happened: A registry-derivation proof lived in mapping evidence although the compliance assertion linked the compliance file, while a dprint-argument proof lived in compliance evidence although the scenario assertion linked the scenario file.

Why it failed: The checks were behaviorally useful but could not prove assertions that linked different evidence files. Alignment requires the assertion type, evidence method, and linked file to agree.

How to avoid: Record one linked evidence lane per assertion in the matrix and move each proof to that file before auditing. Rescore every clause after moving evidence so no source path becomes uncovered.

**Failure 4: Used generic loops and passing cases where the shared standard requires stronger forms**

What happened: Mapping evidence iterated with ordinary loops, and compliance evidence asserted valid behavior without deliberate violating fixtures.

Why it failed: `/typescript-test-standards` requires `it.each`, `describe.each`, or `test.each` over at least two cases for mappings, and a violating fixture for `[test]` compliance.

How to avoid: Fill the matrix's required-evidence-form field directly from `/typescript-test-standards`; block writing when a mapping lacks the required table form or compliance lacks a deterministic violation that the product rejects.

</failure_modes>

<success_criteria>

Test evidence is ready for audit when:

- [ ] Every created or changed test file lives in the governed node's `tests/` directory and is linked from the corresponding spec assertion
- [ ] Every affected assertion has a complete assertion-to-evidence matrix whose language form and linked file match `/typescript-test-standards`
- [ ] The test filenames and assertion mapping follow `/typescript-test-standards` and any `spx/local/typescript-tests.md` overlay loaded for the repository
- [ ] The product's resolved TypeScript test command demonstrates the required RED or GREEN phase result for the governed node or changeset
- [ ] The product's resolved TypeScript typecheck and lint commands exit zero for the changed scope
- [ ] FIX mode addresses every supplied audit finding with a test change or a stated evidence-based rejection before redispatch

</success_criteria>
