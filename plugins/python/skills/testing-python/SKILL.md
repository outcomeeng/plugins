---
name: testing-python
description: >-
  ALWAYS invoke this skill when writing Python tests or fixing test failures.
  NEVER write tests without this skill.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

<objective>
Write or fix test files for a story specification. This skill handles both:
1. **Writing new tests** - Given a story spec, produce test files
2. **Fixing rejected tests** - Given reviewer feedback, fix existing tests

**This skill WRITES tests. It does not just design or plan.**
</objective>

<mode_detection>
**Determine which mode you're in:**

1. **WRITE mode** - Tests don't exist yet or you're starting fresh
   - Check: `ls {story_path}/tests/*.py` returns nothing or minimal files
   - Action: Follow full workflow below

2. **FIX mode** - Tests exist but were rejected by reviewer
   - Check: Recent `/reviewing-python-tests` output shows REJECT with specific issues
   - Action: Read the rejection, fix the specific issues, re-run tests

**Always check which mode before proceeding.**
</mode_detection>

<quick_start>
**Input:** Story spec path (e.g., `spx/01-capability/02-feature/21-story.story/`)

**Output:** Test files written to `{story}/tests/` directory

**Workflow:**

```
Check mode → WRITE or FIX → Execute → Verify → Report
```

</quick_start>

<write_mode_workflow>

## WRITE Mode: Creating New Tests

### Step 1: Load Context

Read the story spec and related files:

```bash
# Read story spec
cat {story_path}/{story_name}.story.md

# Read parent feature for context
cat {feature_path}/{feature_name}.feature.md

# Check for ADRs/PDRs that constrain testing approach
ls {capability_path}/*.adr.md {capability_path}/*.pdr.md {feature_path}/*.adr.md {feature_path}/*.pdr.md 2>/dev/null
```

Extract from the spec:

- **Outcomes** - Gherkin scenarios to verify
- **Test Strategy** - Which levels are specified
- **Harnesses** - Any referenced test harnesses

**Note on Analysis sections (stories only):** The Analysis section documents what the spec author examined. It provides context but is not binding — implementation may diverge as understanding deepens. Use it as a starting point, not a contract.

### Step 2: Determine Test Levels

For each assertion, apply the `/testing` methodology:

| Evidence Type                   | Minimum Level |
| ------------------------------- | ------------- |
| Pure computation/algorithm      | 1             |
| File I/O with temp dirs         | 1             |
| Standard dev tools (git, curl)  | 1             |
| Project-specific binary         | 2             |
| Database, Docker                | 2             |
| Real credentials, external APIs | 3             |

### Step 3: Write Test Files

Create test files following `/standardizing-python-testing`:

**Mandatory elements:**

- `-> None` return type on every test function
- Type annotations on all parameters
- Named constants for all test values
- Property-based tests for parsers/serializers/math (`@given`)
- No mocking - use dependency injection
- File naming indicates level (`.unit.py`, `.integration.py`, `.e2e.py`)

### Step 4: Verify Tests Fail (RED)

```bash
uv run --extra dev pytest {story_path}/tests/ -v
```

Tests should FAIL with ImportError or AssertionError (implementation doesn't exist yet).

### Step 5: Handle Potential Nodes

If the implementation module doesn't exist yet, tests fail on import — breaking the quality gate. Add the node to `spx/POTENTIAL` and run the project's sync command:

```bash
# Add node path to spx/POTENTIAL (paths relative to spx/)
echo "76-risc-v.outcome" >> spx/POTENTIAL

# Sync to pyproject.toml
just sync-potential
```

This excludes the node's tests from pytest, mypy, and pyright until the implementation exists. Ruff still checks style. See the spec-tree `/understanding` skill's `references/potential-nodes.md` for the full convention.

Remove the entry from `spx/POTENTIAL` when implementation begins.

</write_mode_workflow>

<fix_mode_workflow>

## FIX Mode: Fixing Rejected Tests

### Step 1: Read Rejection Feedback

Find the most recent `/reviewing-python-tests` output. Look for:

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
| Wrong filename suffix  | Use `.unit.py`, `.integration.py`, or `.e2e.py`      |

### Step 3: Verify Fixes

```bash
# Run tests again
uv run --extra dev pytest {story_path}/tests/ -v

# Check types
uv run --extra dev mypy {story_path}/tests/

# Check linting
uv run --extra dev ruff check {story_path}/tests/
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
- [ ] Test level matches the evidence type (per `/testing` Stage 2)
- [ ] File names include level suffix (`.unit.py`, `.integration.py`, `.e2e.py`)
- [ ] All test functions have `-> None` return type
- [ ] All parameters have type annotations
- [ ] Named constants used (no magic values)
- [ ] Parsers/serializers have property-based tests (`@given`)
- [ ] No mocking - dependency injection where doubles needed
- [ ] Tests run and fail for expected reasons (RED phase)

</test_writing_checklist>

<patterns_reference>

See `/standardizing-python-testing` for:

- **Level patterns** - How to write Level 1, 2, 3 tests
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

### Story: {story_path}

### Test Files Created

| File                     | Level | Outcomes Covered |
| ------------------------ | ----- | ---------------- |
| `tests/test_foo.unit.py` | 1     | Outcome 1, 2     |

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

- [ ] Test files exist in `{story}/tests/` directory
- [ ] Each assertion from spec has corresponding test(s)
- [ ] Tests follow `/standardizing-python-testing` standards
- [ ] Tests run and fail for expected reasons
- [ ] All reviewer feedback addressed (if FIX mode)

</success_criteria>
