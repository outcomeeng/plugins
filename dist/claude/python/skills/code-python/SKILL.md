---
name: code-python
description: >-
  ALWAYS invoke this skill when writing or fixing implementation code for Python.
  NEVER write or fix Python implementation without this skill.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
---

Invoke the `python:python-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `python:python-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<repo_local_overlay>
**Standards are pre-loaded above.** After loading, check for `spx/local/python.md` and `spx/local/python-tests.md` at the repository root. Read each file that exists and apply each as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<objective>
Write or fix implementation code that makes tests pass. Two modes:
1. **Writing new implementation** - Given failing tests, produce code that passes them
2. **Fixing rejected implementation** - Given reviewer feedback, fix existing code

**Write implementation only — tests MUST already exist.**
</objective>

<mode_detection>
**Determine the current mode:**

1. **WRITE mode** - Implementation doesn't exist or tests are failing
   - Check: Tests fail with ImportError or AssertionError
   - Action: Write implementation to make tests pass

2. **FIX mode** - Implementation exists but was rejected by reviewer
   - Check: Recent `/audit-python` output shows REJECT with specific issues
   - Action: Read the rejection, fix the specific issues, re-run verification

**Always check which mode before proceeding.**
</mode_detection>

<prerequisites>

Before invoking this skill:

1. **Tests must exist** - Written by `/test-python`
2. **Tests must be reviewed** - Approved by `/audit-python-tests`
3. **Spec must be loaded** - Context from `/spec-tree:contextualize`
4. **Standards are pre-loaded above**

If tests don't exist or aren't approved, go back to earlier steps.
</prerequisites>

<write_mode_workflow>

Run the product's own canonical commands when it documents them — a `CLAUDE.md` / `AGENTS.md` instruction, a Justfile or Makefile recipe, or a package script. The `python3 -m …` invocations below are the portable fallback for a product that ships no wrapper; report any tool the product lacks rather than skipping it.

**Step 1 — Understand the tests.** Read the existing tests to understand:

```bash
# Read test files
cat {node_path}/tests/*.py

# Run tests to see failures
python3 -m pytest {node_path}/tests/ -v
```

Understand:

- What behaviors the tests verify
- What interfaces are expected (function signatures, classes)
- What the tests import (where implementation should live)

**Step 2 — Write implementation (GREEN).** Write minimal code that makes tests pass.

**Code standards (per `/python-standards`):**

```python
# ✅ Type annotations on ALL functions
def process_order(order: Order, config: Config) -> OrderResult: ...


# ✅ Source-owned semantic values in production modules
MIN_ORDER_VALUE = 10
MAX_ITEMS = 100


# ✅ Dependency injection for external dependencies
@dataclass
class Deps:
    run_command: CommandRunner
```

**Step 3 — Run tests (verify GREEN).**

```bash
python3 -m pytest {node_path}/tests/ -v
```

All tests MUST pass. If any fail, fix implementation and re-run.

**Step 4 — Refactor (keep GREEN).** Clean up while keeping tests green:

1. Move semantic values to the owning source module
2. Simplify
3. DRY

**Step 5 — Self-verify.**

```bash
# Type checking
python3 -m mypy product/

# Linting
python3 -m ruff check product/

# Tests one more time
python3 -m pytest {node_path}/tests/ -v
```

All must pass before declaring complete.

</write_mode_workflow>

<fix_mode_workflow>

**Step 1 — Read rejection feedback.** Find the most recent `/audit-python` output. Look for:

- Specific file:line locations
- Issue categories (magic values, missing DI, etc.)
- Required fixes

**Step 2 — Apply fixes.** For each rejection reason:

| Rejection Category       | Fix Action                                       |
| ------------------------ | ------------------------------------------------ |
| Magic values             | Move semantic values to the owning source module |
| Missing type annotations | Add types to all functions                       |
| Direct external imports  | Refactor to dependency injection                 |
| Deep relative imports    | Change to absolute imports                       |
| Missing `-> None`        | Add return type                                  |
| Security issues          | Fix the vulnerability (don't suppress)           |

**Step 3 — Verify fixes.**

```bash
# Run tests
python3 -m pytest {node_path}/tests/ -v

# Type checking
python3 -m mypy product/

# Linting
python3 -m ruff check product/
```

**Step 4 — Report what was fixed.**

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

**Named constants**

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

**Dependency injection**

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

**Type annotations**

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
- [ ] Semantic values are source-owned (no duplicated test-owned constants)
- [ ] Code uses dependency injection (no direct external imports)
- [ ] All functions have type annotations
- [ ] All reviewer feedback addressed (if FIX mode)

</success_criteria>
