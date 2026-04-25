---
name: coding-python
description: >-
  ALWAYS invoke this skill when writing or fixing implementation code for Python.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-python/SKILL.md"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-python-tests/SKILL.md"`

<objective>
Write or fix implementation code that makes tests pass. This skill handles both:
1. **Writing new implementation** - Given failing tests, produce code that passes them
2. **Fixing rejected implementation** - Given reviewer feedback, fix existing code

**This skill WRITES implementation. Tests should already exist.**
</objective>

<mode_detection>
**Determine which mode you're in:**

1. **WRITE mode** - Implementation doesn't exist or tests are failing
   - Check: Tests fail with ImportError or AssertionError
   - Action: Write implementation to make tests pass

2. **FIX mode** - Implementation exists but was rejected by reviewer
   - Check: Recent `/auditing-python` output shows REJECT with specific issues
   - Action: Read the rejection, fix the specific issues, re-run verification

**Always check which mode before proceeding.**
</mode_detection>

<prerequisites>

Before invoking this skill:

1. **Tests must exist** - Written by `/testing-python`
2. **Tests must be reviewed** - Approved by `/auditing-python-tests`
3. **Spec must be loaded** - Context from `/spec-tree:contextualizing`
4. **Standards must be loaded** - Read `/standardizing-python` and `/standardizing-python-tests`

If tests don't exist or aren't approved, go back to earlier steps.
</prerequisites>

<write_mode_workflow>

## WRITE Mode: Creating Implementation

### Step 1: Understand Tests

Read the existing tests to understand:

```bash
# Read test files
cat {node_path}/tests/*.py

# Run tests to see failures
just run test {node_path}/tests/ -v
```

Understand:

- What behaviors the tests verify
- What interfaces are expected (function signatures, classes)
- What the tests import (where implementation should live)

### Step 2: Write Implementation (GREEN)

Write minimal code that makes tests pass.

**Code standards (per `/standardizing-python`):**

```python
# ✅ Type annotations on ALL functions
def process_order(order: Order, config: Config) -> OrderResult: ...


# ✅ Named constants for all literals
MIN_ORDER_VALUE = 10
MAX_ITEMS = 100


# ✅ Dependency injection for external dependencies
@dataclass
class Deps:
    run_command: CommandRunner
```

### Step 3: Run Tests (Verify GREEN)

```bash
just run test {node_path}/tests/ -v
```

All tests should pass. If any fail, fix implementation and re-run.

### Step 4: Refactor (Keep GREEN)

Clean up while keeping tests green:

1. Extract constants
2. Simplify
3. DRY

### Step 5: Self-Verify

```bash
# Type checking
just run mypy product/

# Linting
just run ruff check product/

# Tests one more time
just run test {node_path}/tests/ -v
```

All must pass before declaring complete.

</write_mode_workflow>

<fix_mode_workflow>

## FIX Mode: Fixing Rejected Implementation

### Step 1: Read Rejection Feedback

Find the most recent `/auditing-python` output. Look for:

- Specific file:line locations
- Issue categories (magic values, missing DI, etc.)
- Required fixes

### Step 2: Apply Fixes

For each rejection reason:

| Rejection Category       | Fix Action                             |
| ------------------------ | -------------------------------------- |
| Magic values             | Extract to named constants             |
| Missing type annotations | Add types to all functions             |
| Direct external imports  | Refactor to dependency injection       |
| Deep relative imports    | Change to absolute imports             |
| Missing `-> None`        | Add return type                        |
| Security issues          | Fix the vulnerability (don't suppress) |

### Step 3: Verify Fixes

```bash
# Run tests
just run test {node_path}/tests/ -v

# Type checking
just run mypy product/

# Linting
just run ruff check product/
```

### Step 4: Report What Was Fixed

```markdown
## Implementation Fixed

### Issues Addressed

| Issue       | Location        | Fix Applied                       |
| ----------- | --------------- | --------------------------------- |
| Magic value | handler.py:45   | Extracted to MAX_RETRIES constant |
| Missing DI  | processor.py:12 | Added ProcessorDeps dataclass     |

### Verification

All tests pass. Types and lint clean. Ready for re-review.
```

</fix_mode_workflow>

<code_patterns>

## Mandatory Patterns

### Named Constants

```python
# ❌ REJECTED
def validate_score(score: int) -> bool:
    return 0 <= score <= 100


# ✅ REQUIRED
MIN_SCORE = 0
MAX_SCORE = 100


def validate_score(score: int) -> bool:
    return MIN_SCORE <= score <= MAX_SCORE
```

### Dependency Injection

```python
# ❌ REJECTED
import subprocess


def sync_files(src: str, dest: str) -> bool:
    result = subprocess.run(["rsync", src, dest])
    return result.returncode == 0


# ✅ REQUIRED
@dataclass
class SyncDeps:
    run_command: CommandRunner


def sync_files(src: str, dest: str, deps: SyncDeps) -> bool:
    returncode, _, _ = deps.run_command.run(["rsync", src, dest])
    return returncode == 0
```

### Type Annotations

```python
# ✅ All functions have full type annotations
def get_user(user_id: int) -> User | None:
    users: list[User] = fetch_users()
    return next((u for u in users if u.id == user_id), None)
```

</code_patterns>

<output_format>

**WRITE mode output:**

```markdown
## Implementation Complete

### Node: {node_path}

### Files Created/Modified

| File                 | Action  | Description   |
| -------------------- | ------- | ------------- |
| `product/handler.py` | Created | Order handler |

### Verification

- Tests: ✓ Pass
- Types: ✓ Pass
- Lint: ✓ Pass

Ready for review.
```

**FIX mode output:**

```markdown
## Implementation Fixed

### Issues Addressed

| Issue   | Location    | Fix Applied |
| ------- | ----------- | ----------- |
| {issue} | {file:line} | {fix}       |

### Verification

All checks pass. Ready for re-review.
```

</output_format>

<success_criteria>

Task is complete when:

- [ ] All tests in `{node}/tests/` pass
- [ ] Type checking passes (`mypy`)
- [ ] Linting passes (`ruff check`)
- [ ] Code uses named constants (no magic values)
- [ ] Code uses dependency injection (no direct external imports)
- [ ] All functions have type annotations
- [ ] All reviewer feedback addressed (if FIX mode)

</success_criteria>
