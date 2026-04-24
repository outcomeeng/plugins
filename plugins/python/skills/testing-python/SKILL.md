---
name: testing-python
description: >-
  ALWAYS invoke this skill when writing or fixing tests for Python.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Write or fix test files for a node specification. This skill handles both:
1. **Writing new tests** - Given a node spec, produce test files
2. **Fixing rejected tests** - Given reviewer feedback, fix existing tests

**This skill WRITES tests. It does not just design or plan.**
</objective>

<mode_detection>
**Determine which mode you're in:**

1. **WRITE mode** - Tests don't exist yet or you're starting fresh
   - Check: `ls {node_path}/tests/*.py` returns nothing or minimal files
   - Action: Follow full workflow below

2. **FIX mode** - Tests exist but were rejected by reviewer
   - Check: Recent `/auditing-python-tests` output shows REJECT with specific issues
   - Action: Read the rejection, fix the specific issues, re-run tests

**Always check which mode before proceeding.**
</mode_detection>

<quick_start>
**Input:** Node spec path (e.g., `spx/21-infra.enabler/43-parser.outcome/`)

**Output:** Test files written to `{node}/tests/` directory

**Prerequisites:** Run `/testing` first, then read `/standardizing-python` and `/standardizing-python-tests`. The foundational skill chooses evidence and level; this skill implements those decisions in Python.

**Workflow:**

```
Check mode → WRITE or FIX → Execute → Verify → Report
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

**Note on Analysis sections:** The Analysis section documents what the spec author examined. It provides context but is not binding — implementation may diverge as understanding deepens. Use it as a starting point, not a contract.

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

Create test files following `/standardizing-python-tests`:

**Mandatory elements:**

- `-> None` return type on every test function
- Type annotations on all parameters
- Named constants for all test values
- Property-based tests for parsers/serializers/math (`@given`)
- No mocking - use dependency injection
- File naming follows `test_<subject>.<evidence>.<level>[.<runner>].py`

### Step 4: Verify Tests Fail (RED)

```bash
just run test {node_path}/tests/ -v
```

Tests should FAIL with ImportError or AssertionError (implementation doesn't exist yet).

### Step 5: Handle Specified Nodes

If the implementation module doesn't exist yet, tests fail on import — breaking the quality gate. Add the node to `spx/EXCLUDE`:

```bash
# Add node path to spx/EXCLUDE (paths relative to spx/)
echo "76-risc-v.outcome" >> spx/EXCLUDE
```

The `spx` CLI reads this file and skips excluded nodes when running `spx test passing`. Ruff still checks style. See the spec-tree `/understanding` skill's `references/excluded-nodes.md` for the full convention.

Remove the entry from `spx/EXCLUDE` when implementation begins.

</write_mode_workflow>

<fix_mode_workflow>

## FIX Mode: Fixing Rejected Tests

### Step 1: Read Rejection Feedback

Find the most recent `/auditing-python-tests` output. Look for:

- Specific file:line locations
- Issue categories (evidentiary gap, missing property tests, etc.)
- Required fixes

### Step 2: Apply Fixes

For each rejection reason:

| Rejection Category     | Fix Action                                           |
| ---------------------- | ---------------------------------------------------- |
| Missing `-> None`      | Add return type to test functions                    |
| Evidentiary gap        | Rewrite test to actually verify the assertion        |
| Mocking detected       | Replace with dependency injection                    |
| Missing property tests | Add `@given` tests for parsers/serializers           |
| Silent skip            | Change `skipif` to `pytest.fail()` for required deps |
| Magic values           | Extract to named constants                           |
| Wrong filename axes    | Rename to the `/standardizing-python-tests` pattern  |

### Step 3: Verify Fixes

```bash
# Run tests again
just run test {node_path}/tests/ -v

# Check types
just run mypy {node_path}/tests/

# Check linting
just run ruff check {node_path}/tests/
```

### Step 4: Report What Was Fixed

```markdown
## Tests Fixed

### Issues Addressed

| Issue           | Location       | Fix Applied                          |
| --------------- | -------------- | ------------------------------------ |
| Missing -> None | test_foo.py:15 | Added return type                    |
| Magic value     | test_foo.py:23 | Extracted to EXPECTED_VALUE constant |

### Verification

Tests run and fail for expected reasons (RED phase complete).
```

</fix_mode_workflow>

<test_writing_checklist>

Before declaring tests complete:

- [ ] Each Gherkin assertion has at least one test
- [ ] Evidence mode and level match `/testing` Stage 2
- [ ] File names use `test_<subject>.<evidence>.<level>[.<runner>].py`
- [ ] All test functions have `-> None` return type
- [ ] All parameters have type annotations
- [ ] Named constants used (no magic values)
- [ ] Parsers/serializers have property-based tests (`@given`)
- [ ] No mocking - dependency injection where doubles needed
- [ ] Tests run and fail for expected reasons (RED phase)

</test_writing_checklist>

<patterns_reference>

See `/standardizing-python-tests` for:

- **Level patterns** - How to write `l1`, `l2`, and `l3` tests
- **Exception implementations** - The 7 exception cases in Python
- **Property-based testing** - Hypothesis patterns
- **Data factories** - Factory and builder patterns
- **DI patterns** - Protocol and dataclass dependencies
- **Harness patterns** - Docker, subprocess harnesses
- **Anti-patterns** - What to avoid

</patterns_reference>

<output_format>

**WRITE mode output:**

```markdown
## Tests Written

### Node: {node_path}

### Test Files Created

| File                            | Level | Outcomes Covered |
| ------------------------------- | ----- | ---------------- |
| `tests/test_foo.scenario.l1.py` | `l1`  | Outcome 1, 2     |

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
- [ ] Tests follow `/standardizing-python-tests` standards
- [ ] Tests run and fail for expected reasons
- [ ] All reviewer feedback addressed (if FIX mode)

</success_criteria>
