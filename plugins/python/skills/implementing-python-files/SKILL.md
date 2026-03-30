---
name: implementing-python-files
description: >-
  ALWAYS invoke this skill when given file paths to implement or applying TDD to specific files.
  NEVER implement specific files without this skill.
argument-hint: file_paths
---

<objective>
File-focused Python implementation skill. Implements code for one or more specific files using the 4-step TDD workflow: write tests → review tests → implement → review implementation.
</objective>

<quick_start>
**Input:** One or more file paths to implement

**Workflow per file:**

```text
File → Step 1 → Step 2 → Step 3 → Step 4 → Next File
         │         │         │         │
     /testing   /reviewing  /coding   /reviewing
      -python    -python     -python   -python
                 -tests
```

1. **Analyze file context** - Understand what the file should do
2. **Write tests** - Invoke `/testing-python` → tests written
3. **Review tests** - Invoke `/auditing-python-tests` → APPROVE/REJECT
4. **Implement** - Invoke `/coding-python` → code written
5. **Review code** - Invoke `/auditing-python` → APPROVE/REJECT
6. **Next file** - Repeat until all files complete

</quick_start>

<arguments>
**Input:** One or more file paths to implement

**Accepted formats:**

```bash
# Single file
/implementing-python-files src/mymodule/handler.py

# Multiple files (space-separated)
/implementing-python-files src/mymodule/handler.py src/mymodule/processor.py

# Glob pattern (expanded by shell)
/implementing-python-files src/mymodule/*.py
```

**File validation:**

- Files may or may not exist yet (new files are created)
- Paths should be relative to project root or absolute
- For existing files, tests may already exist (will be augmented)

</arguments>

<workflow>

## Step 0: Parse and Validate Input

Extract file paths from arguments. For each path:

1. **Normalize path** - Convert to absolute or project-relative
2. **Determine test location** - Co-located `tests/` or sibling `test_*.py`
3. **Check for existing tests** - Will augment, not replace

## For Each File (Sequential)

### Step 1: Analyze Context

Before writing tests, understand:

1. **Read the file** (if exists) - Understand current implementation
2. **Read related files** - Imports, dependencies, interfaces
3. **Identify behaviors** - What should this code do?

If file doesn't exist, determine expected behaviors from:

- User's request/description
- Interface contracts (if implementing an interface)
- Calling code (if being called by existing code)

### Step 2: Write Tests

Invoke `/testing-python`:

The skill will:

- Determine test levels per `/testing` methodology
- Write test files
- Run tests to confirm they fail (RED)

### Step 3: Review Tests

Invoke `/auditing-python-tests`:

**If REJECT:** Fix issues, re-invoke until APPROVE.
**If APPROVE:** Proceed to Step 4.

### Step 4: Implement

Invoke `/coding-python`:

The skill will:

- Read failing tests
- Write implementation code
- Run tests until GREEN
- Self-verify (types, lint)

### Step 5: Review Code

Invoke `/auditing-python`:

**If REJECT:** Fix issues, re-invoke until APPROVE.
**If APPROVE:** File is complete. Proceed to next file.

</workflow>

<skill_sequence>

| Step | Skill                    | Purpose               |
| ---- | ------------------------ | --------------------- |
| 2    | `/testing-python`        | Write tests           |
| 3    | `/auditing-python-tests` | Review tests          |
| 4    | `/coding-python`         | Write implementation  |
| 5    | `/auditing-python`       | Review implementation |

</skill_sequence>

<progress_tracking>

Track progress through file list:

```text
Files to implement:
├── src/mymodule/handler.py      [✓] Tests approved, code approved
├── src/mymodule/processor.py    [→] In Progress (Step 4: implementing)
├── src/mymodule/validator.py    [pending] Not started
└── src/mymodule/formatter.py    [pending] Not started
```

**Legend:**

- `[✓]` = Tests + code approved
- `[→]` = In progress (show current step)
- `[pending]` = Not started

</progress_tracking>

<success_criteria>

## File Complete

- [ ] Tests exist and verify correct behaviors
- [ ] Tests approved by `/auditing-python-tests`
- [ ] Implementation passes all tests
- [ ] Code approved by `/auditing-python`

## All Files Complete

- [ ] All files individually approved
- [ ] All tests pass: `uv run --extra dev pytest -v`
- [ ] Type checking passes: `uv run --extra dev mypy src/`
- [ ] Linting passes: `uv run --extra dev ruff check src/`

</success_criteria>

<error_handling>

**File doesn't exist and no context provided:**
→ Ask user for expected behaviors before proceeding

**Tests already exist with mocking:**
→ Flag to user, offer to refactor tests to use DI

**Review fails repeatedly (3+ attempts):**
→ Stop and report issues to user for guidance

</error_handling>
