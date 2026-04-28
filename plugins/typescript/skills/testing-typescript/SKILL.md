---
name: testing-typescript
description: >-
  ALWAYS invoke this skill when writing or fixing tests for TypeScript.
allowed-tools: Read, Bash, Glob, Grep, Write, Edit
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript/SKILL.md" || echo "standardizing-typescript not found -- invoke typescript:standardizing-typescript manually"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-typescript-tests/SKILL.md" || echo "standardizing-typescript-tests not found -- invoke typescript:standardizing-typescript-tests manually"`

!`cat "${CLAUDE_SKILL_DIR}/../../../spec-tree/skills/testing/SKILL.md" || echo "testing not found -- invoke spec-tree:testing manually"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. `typescript:standardizing-typescript`
2. `typescript:standardizing-typescript-tests`
3. `spec-tree:testing`

</codex_fallback>

<objective>
Write or fix test files for a node specification. This skill handles both:
1. **Writing new tests** - Given a node spec, produce test files
2. **Fixing rejected tests** - Given reviewer feedback, fix existing tests

**This skill WRITES tests. It does not just design or plan.**
</objective>

<mode_detection>
**Determine which mode you're in:**

1. **WRITE mode** - Tests do not exist yet or you are starting fresh
   - Check: `ls {node_path}/tests/*.ts` returns nothing or minimal files
   - Action: Follow full workflow below

2. **FIX mode** - Tests exist but were rejected by reviewer
   - Check: Recent `/auditing-typescript-tests` output shows REJECT with specific issues
   - Action: Read the rejection, fix the specific issues, re-run tests

**Always check which mode before proceeding.**
</mode_detection>

<quick_start>
**Input:** Node spec path (e.g., `spx/21-infra.enabler/43-parser.outcome/`)

**Output:** Test files written to `{node}/tests/` directory

**Prerequisites:** Standards and the `/testing` router are pre-loaded above. The router chooses evidence and level; this skill implements those decisions in TypeScript.

**Workflow:**

```
Check mode -> WRITE or FIX -> Execute -> Verify -> Report
```

</quick_start>

<write_mode_workflow>

## WRITE Mode: Creating New Tests

### Step 1: Load Context

Read the node spec and related files:

```bash
# Read node spec
cat {node_path}/{slug}.outcome.md

# Read parent node for context (if nested)
cat {parent_path}/{slug}.enabler.md

# Check for ADRs/PDRs that constrain testing approach
ls {node_path}/../*.adr.md {node_path}/../*.pdr.md 2>/dev/null
```

Extract from the spec:

- **Assertions** - Typed assertions to verify
- **Test Strategy** - Which levels are specified
- **Harnesses** - Any referenced test harnesses

**Note on Analysis sections:** The Analysis section documents what the spec author examined. It provides context but is not binding -- implementation may diverge as understanding deepens. Use it as a starting point, not a contract.

### Step 2: Determine Evidence and Level

For each assertion, apply the `/testing` methodology:

| Evidence location               | Minimum level |
| ------------------------------- | ------------- |
| Pure computation/algorithm      | `l1`          |
| File I/O with temp dirs         | `l1`          |
| Standard dev tools (git, curl)  | `l1`          |
| Project-specific binary         | `l2`          |
| Database, Docker                | `l2`          |
| Real credentials, external APIs | `l3`          |

### Step 3: Write Test Files

Create test files following `/standardizing-typescript-tests`:

**Mandatory elements:**

- File naming: `<subject>.<evidence>.<level>[.<runner>].test.ts`
- Type annotations on all interfaces and function parameters
- Named constants for all test values -- import from production modules
- Property-based tests for parsers/serializers/math (`fc.assert`)
- No `vi.mock()` or `vi.fn()` replacing the dependency under test -- use typed DI interfaces
- Vitest as default runner; `playwright` runner token when needed

### Step 4: Verify Tests Fail (RED)

```bash
npx vitest run {node_path}/tests/
```

Tests should FAIL with import errors or assertion errors (implementation does not exist yet).

### Step 5: Handle Specified Nodes

If the implementation module does not exist yet, tests fail on import -- breaking the quality gate. Add the node to `spx/EXCLUDE`:

```bash
# Add node path to spx/EXCLUDE (paths relative to spx/)
echo "76-risc-v.outcome" >> spx/EXCLUDE
```

The `spx` CLI reads this file and skips excluded nodes when running `spx test passing`. Remove the entry from `spx/EXCLUDE` when implementation begins.

</write_mode_workflow>

<fix_mode_workflow>

## FIX Mode: Fixing Rejected Tests

### Step 1: Read Rejection Feedback

Find the most recent `/auditing-typescript-tests` output. Look for:

- Specific file:line locations
- Issue categories (evidentiary gap, missing property tests, etc.)
- Required fixes

### Step 2: Apply Fixes

For each rejection reason:

| Rejection Category             | Fix Action                                                  |
| ------------------------------ | ----------------------------------------------------------- |
| Evidentiary gap                | Rewrite test to actually verify the assertion               |
| `vi.mock()` detected           | Replace with typed DI interface                             |
| `vi.fn()` testing call details | Replace with typed spy class or recording object            |
| Missing property tests         | Add `fc.assert(fc.property(...))` for parsers/serializers   |
| Source-owned value redefined   | Import from production module instead                       |
| Wrong filename axes            | Rename to `<subject>.<evidence>.<level>[.<runner>].test.ts` |

### Step 3: Verify Fixes

```bash
# Run tests
npx vitest run {node_path}/tests/

# Check types
npx tsc --noEmit

# Check linting
npx eslint {node_path}/tests/
```

### Step 4: Report What Was Fixed

```markdown
## Tests Fixed

### Issues Addressed

| Issue           | Location       | Fix Applied                       |
| --------------- | -------------- | --------------------------------- |
| vi.mock() usage | foo.test.ts:15 | Replaced with typed DI interface  |
| Magic value     | foo.test.ts:23 | Imported STATUS_CODES from module |

### Verification

Tests run and fail for expected reasons (RED phase complete).
```

</fix_mode_workflow>

<test_writing_checklist>

Before declaring tests complete:

- [ ] Each spec assertion has at least one test
- [ ] Evidence mode and level match `/testing` Stage 2
- [ ] File names use `<subject>.<evidence>.<level>[.<runner>].test.ts`
- [ ] No `vi.mock()` or `vi.fn()` replacing the dependency under test
- [ ] Doubles are typed interfaces passed through DI
- [ ] Property assertions use meaningful `fast-check` properties
- [ ] Source-owned values imported from production modules
- [ ] Tests run and fail for expected reasons (RED phase)

</test_writing_checklist>

<patterns_reference>

See `/standardizing-typescript-tests` for:

- **File naming** - Evidence, level, and runner axes
- **Level tooling** - Vitest vs Playwright, l1/l2/l3 infrastructure
- **Router mapping** - `/testing` Stage decisions to TypeScript patterns
- **l1 patterns** - Pure functions, typed factories, temp dirs
- **Exception implementations** - The 6 exception cases in TypeScript
- **l2 patterns** - Typed harness factory and usage
- **l3 patterns** - Credential management, fail-loudly policy
- **Dependency injection** - Typed interfaces and recording doubles
- **Property-based testing** - `fast-check` patterns
- **Test data policy** - Source-owned constants, generators, harnesses, fixtures
- **Anti-patterns** - What to reject or rewrite

Also check for `spx/local/typescript-tests.md` at the repository root -- project-specific overrides apply after this reference.

</patterns_reference>

<output_format>

**WRITE mode output:**

```markdown
## Tests Written

### Node: {node_path}

### Test Files Created

| File                            | Level | Assertions Covered |
| ------------------------------- | ----- | ------------------ |
| `tests/foo.scenario.l1.test.ts` | `l1`  | Assertion 1, 2     |

### Test Run (RED Phase)

Tests fail as expected. Ready for review.
```

**FIX mode output:**

```markdown
## Tests Fixed

### Issues Addressed

| Issue   | Location    | Fix Applied |
| ------- | ----------- | ----------- |
| {issue} | {file:line} | {fix}       |

### Verification

Tests pass checklist. Ready for re-review.
```

</output_format>

<success_criteria>

Task is complete when:

- [ ] Test files exist in `{node}/tests/` directory
- [ ] Each assertion from spec has corresponding test(s)
- [ ] Tests follow `/standardizing-typescript-tests` standards
- [ ] Tests run and fail for expected reasons
- [ ] All reviewer feedback addressed (if FIX mode)

</success_criteria>
