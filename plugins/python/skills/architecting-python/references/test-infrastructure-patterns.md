# Test Infrastructure Patterns

Test infrastructure is an architectural concern. Design it once in ADRs, not ad-hoc during implementation.

## Core Principle

> **Test utilities are production code. Package them properly. Verify the environment before running tests.**

---

## The Test Environment Problem

### Symptom: "Module not found" When Running Tests

```bash
$ just run test spx/.../tests/test_foo.scenario.l1.py
ModuleNotFoundError: No module named 'click'  # But click IS installed!
```

### Root Cause: Wrong pytest

```bash
$ uv run which pytest
/opt/homebrew/bin/pytest  # ❌ WRONG - System pytest, not project venv
```

The system pytest uses a different Python that doesn't have your project's dependencies.

### Fix: Install Dev Dependencies in Project Venv

```bash
# This installs pytest AND all dev deps in the project venv
uv pip install -e ".[dev]"

# Verify
uv run which pytest
# /path/to/project/.venv/bin/pytest  # ✅ CORRECT
```

---

## Test Utility Packaging

### The Problem: Tests Can't Import Shared Code

```python
# spx/.../tests/test_foo.scenario.l1.py
from tests.fixtures import create_user  # ❌ ModuleNotFoundError
```

### ❌ Wrong: Path Hacks

```python
# conftest.py - DON'T DO THIS
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # Brittle, breaks easily
```

### ✅ Right: Make Test Utilities an Installable Package

**Step 1: Structure**

```
project/
├── pyproject.toml
├── mypackage/              # Main package
│   └── ...
├── mypackage_testing/      # Test utilities package (NOT tests/)
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── __init__.py
│   │   └── users.py        # create_user(), etc.
│   └── harnesses/
│       ├── __init__.py
│       └── cli.py          # CLIHarness, etc.
└── spx/                    # Co-located tests (per Outcome Engineering framework)
    └── .../tests/
        └── test_foo.scenario.l1.py # from mypackage_testing.fixtures import create_user
```

**Step 2: pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["mypackage", "mypackage_testing"] # Both are installable
```

**Step 3: Install**

```bash
uv pip install -e ".[dev]"  # Installs both packages in editable mode
```

**Step 4: Import**

```python
# spx/.../tests/test_foo.scenario.l1.py
from mypackage_testing.fixtures import create_user  # ✅ Works everywhere
```

---

## pytest Configuration for Complex Layouts

### The Problem: Multiple test directories collide

```
project/
├── spx/.../21-foo.outcome/tests/test_generics.scenario.l1.py  # Co-located tests
└── spx/.../54-bar.outcome/tests/test_generics.mapping.l1.py   # Different evidence file
```

pytest gets confused: "imported module 'test_generics' has this **file** attribute..."

### Fix: Use importlib Import Mode

```toml
# pyproject.toml
[tool.pytest.ini_options]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short --import-mode=importlib" # KEY: importlib mode
pythonpath = ["."]
```

### Why importlib Mode Works

| Mode                | Behavior                                               | Problem                              |
| ------------------- | ------------------------------------------------------ | ------------------------------------ |
| `prepend` (default) | Adds test dir to sys.path, imports as top-level module | Multiple `test_foo.py` files collide |
| `importlib`         | Uses importlib to import each file independently       | Each file is isolated, no collisions |

---

## Excluding Out-of-Scope Code

### The Problem: Broken out-of-scope code fails `just check`

```bash
$ just check
ERROR archive/tests/test_emitter.py - ImportError: cannot import name 'HDLEmitterBase'
```

### Fix: Explicit Exclusions in Check Commands

```makefile
# justfile

# Run all checks - excludes archived work/
check: lint typecheck
    just run test mypackage_testing/ spx/ --ignore=archive/

# Coverage commands also need exclusion
test-cov:
    just run test --cov=mypackage --cov-report=term --ignore=archive/
```

---

## ADR Compliance: Test Infrastructure

Every Python project ADR governing test infrastructure should express rules in Compliance:

````markdown
## Compliance

### MUST

- Test utilities (fixtures, harnesses, helpers) are packaged as `{project}_testing/`
- `pyproject.toml` includes `{project}` and `{project}_testing` as installable packages
- pytest uses `--import-mode=importlib` when co-located test files can share module names

### NEVER

- Tests mutate `sys.path` to import shared fixtures or harnesses

```toml
[tool.pytest.ini_options]
addopts = "-v --tb=short --import-mode=importlib"
pythonpath = ["."]
```

### Test Locations

| Type             | Location         | Runs in `just check` |
| ---------------- | ---------------- | -------------------- |
| Co-located tests | `spx/.../tests/` | Yes                  |
| Regression tests | `tests/`         | Yes                  |

### Environment Verification

Before running tests, verify:

1. `uv run which pytest` → must be `.venv/bin/pytest`
2. Dev deps installed → `uv pip install -e ".[dev]"`
````

---

## Verification Checklist

Before running any tests, verify:

```bash
# 1. pytest is from project venv
uv run which pytest
# Expected: /path/to/project/.venv/bin/pytest
# If wrong: uv pip install -e ".[dev]"

# 2. Test utilities are importable
uv run python -c "from mypackage_testing.fixtures import ...; print('OK')"
# If fails: Check pyproject.toml packages list, re-run uv pip install -e ".[dev]"

# 3. pytest config has importlib mode
grep "import-mode" pyproject.toml
# Expected: --import-mode=importlib in addopts
```

---

## Key Principles

1. **Test utilities are packages** — Install them, don't path-hack them

2. **Verify environment first** — `uv run which pytest` before running tests

3. **Use importlib mode** — Required for projects with multiple test directories

4. **Exclude out-of-scope code** — Legacy/broken code gets quarantined, not blocking

5. **Document in ADRs** — Test infrastructure is an architectural decision
