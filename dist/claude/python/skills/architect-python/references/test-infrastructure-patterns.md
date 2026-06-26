# Test Infrastructure Patterns

Test infrastructure is an architectural concern. Design it once in ADRs, not ad-hoc during implementation.

## Core Principle

> **Test infrastructure is production code. Package it properly. Verify the environment before running tests.**

The governing category is **test infrastructure** — never "test utilities", "support", "helpers", or "tools". It has three kinds: `generators` (variable input domains), `harnesses` (resource lifecycle and access to real behavior), and `fixtures` (inert whole-payload input files consumed by path).

---

## Running Tests And The Environment

Run the product's canonical test command — the one its `CLAUDE.md`, Justfile, Makefile, or package scripts document. The direct `python3 -m pytest` invocations below are the portable fallback for a product that ships no wrapper.

### Symptom: "Module not found" When Running Tests

```bash
python3 -m pytest spx/.../tests/test_foo.scenario.l1.py
ModuleNotFoundError: No module named 'click'  # but click IS installed
```

### Root Cause: The Wrong Interpreter

The `pytest` resolved on `PATH` may run under a different interpreter than the one holding the product's dependencies. Confirm which interpreter resolves:

```bash
python3 -c "import sys; print(sys.executable)"
python3 -m pytest --version
```

### Fix: Install The Product For That Interpreter

```bash
python3 -m pip install -e ".[dev]"
```

Then invoke pytest through the same interpreter (`python3 -m pytest`) so it sees the installed packages.

---

## Test-Infrastructure Packaging

### The Problem: Tests Can't Import Shared Code

```python
# spx/.../tests/test_foo.scenario.l1.py
from tests.fixtures import (
    create_user,
)  # ❌ ModuleNotFoundError — tests/ is not a package
```

### ❌ Wrong: Path Hacks

```python
# conftest.py - DON'T DO THIS
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # brittle, breaks easily
```

### ✅ Right: Make Test Infrastructure An Installable Package

**Step 1: Structure** — the `{product}_testing/` package carries all three categories:

```
product/
├── pyproject.toml
├── mypackage/                 # main package
│   └── ...
├── mypackage_testing/         # test-infrastructure package (NOT tests/)
│   ├── __init__.py
│   ├── generators/            # variable input domains (e.g. Hypothesis strategies)
│   │   ├── __init__.py
│   │   └── users.py           # valid_users(), etc.
│   ├── harnesses/             # resource lifecycle, access to real behavior
│   │   ├── __init__.py
│   │   └── cli.py             # CLIHarness, etc.
│   └── fixtures/              # inert whole-payload input files (consumed by path)
│       └── sample_report.json
└── spx/                       # co-located tests (per Outcome Engineering framework)
    └── .../tests/
        └── test_foo.scenario.l1.py
```

Co-located tests import generators and harnesses from the package (`from mypackage_testing.generators import valid_users`) and consume fixtures as inert files by path — never by importing them as modules.

**Step 2: pyproject.toml** — both packages are installable:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["mypackage", "mypackage_testing"] # both are installable
```

**Step 3: Install** (portable fallback; prefer the product's own wrapper):

```bash
python3 -m pip install -e ".[dev]"  # installs both packages in editable mode
```

**Step 4: Import**

```python
# spx/.../tests/test_foo.scenario.l1.py
from mypackage_testing.generators import valid_users  # ✅ works everywhere
```

---

## pytest Configuration for Complex Layouts

### The Problem: Multiple test directories collide

```
product/
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

### The Problem: Broken out-of-scope code fails the check command

```bash
ERROR archive/tests/test_emitter.py - ImportError: cannot import name 'HDLEmitterBase'
```

### Fix: Explicit Exclusions in the Check Command

Add the exclusion to the product's own test or check recipe (Justfile, Makefile, or package script). With a direct invocation it is:

```bash
python3 -m pytest mypackage_testing/ spx/ --ignore=archive/
```

---

## ADR Verification: Test Infrastructure

Every Python product ADR governing test infrastructure should express rules under `## Verification`:

````markdown
## Verification

### Audit

- ALWAYS: test infrastructure is packaged as `{product}_testing/` with `generators/`, `harnesses/`, and inert fixture data under `fixtures/` ([audit])
- ALWAYS: `pyproject.toml` includes `{product}` and `{product}_testing` as installable packages ([audit])
- ALWAYS: pytest uses `--import-mode=importlib` when co-located test files can share module names ([audit])
- NEVER: tests mutate `sys.path` to import shared generators or harnesses ([audit])

```toml
[tool.pytest.ini_options]
addopts = "-v --tb=short --import-mode=importlib"
pythonpath = ["."]
```

### Test Locations

| Type             | Location         | In the product's check run |
| ---------------- | ---------------- | -------------------------- |
| Co-located tests | `spx/.../tests/` | Yes                        |
| Regression tests | `tests/`         | Yes                        |

### Environment Verification

Before running tests, verify the interpreter resolves the product venv and the test-infrastructure package imports:

1. `python3 -c "import sys; print(sys.executable)"` → the product venv's interpreter
2. Dev deps installed → `python3 -m pip install -e ".[dev]"`
````

---

## Verification Checklist

Before running any tests, verify:

```bash
# 1. the resolving interpreter is the product venv
python3 -c "import sys; print(sys.executable)"
# Expected: /path/to/product/.venv/bin/python

# 2. test infrastructure is importable
python3 -c "import mypackage_testing.generators, mypackage_testing.harnesses; print('OK')"
# If fails: check pyproject.toml packages list, re-run the editable install

# 3. pytest config has importlib mode
grep "import-mode" pyproject.toml
# Expected: --import-mode=importlib in addopts
```

---

## Key Principles

1. **Test infrastructure is a package** — install it, don't path-hack it

2. **Verify the interpreter first** — confirm `sys.executable` before running tests

3. **Use importlib mode** — required for projects with multiple test directories

4. **Exclude out-of-scope code** — legacy/broken code gets quarantined, not blocking

5. **Document in ADRs** — test infrastructure is an architectural decision
