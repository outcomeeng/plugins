---
name: standardizing-python
disable-model-invocation: true
description: >-
  Python code standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Python code standards enforced by linters (ruff, mypy) and manual review. Defines what `/coding-python` must follow and `/auditing-python` enforces.
</objective>

<quick_start>
Reference this skill when coding or reviewing Python. Standards grouped by category with ruff rule codes. All examples show correct (✅) and incorrect (❌) patterns.
</quick_start>

<success_criteria>
Code follows these standards when all ruff rules and mypy checks pass. See summary table at the end for the complete rejection criteria with rule codes.
</success_criteria>

<reference_note>
This is a reference skill. Other Python skills reference these standards. You typically don't invoke this directly—invoke `/coding-python`, `/testing-python`, or `/auditing-python` instead.

These standards apply to ALL Python code: production and test code alike.
</reference_note>

---

<type_annotations>

ALL functions require complete type annotations. No exceptions.

```python
# ✅ REQUIRED: Return types on ALL functions
def process_items(
    items: list[str],
    config: Config,
    logger: logging.Logger,
) -> ProcessResult:
    """Process items according to config."""


# ✅ REQUIRED: -> None on functions that return nothing
def test_validates_input(self) -> None:
    result = validate("test")
    assert result.valid


# ✅ REQUIRED: -> None on __init__
def __init__(self, config: Config) -> None:
    self.config = config


# ✅ REQUIRED: Type annotations on ALL parameters
def test_creates_file(self, tmp_path: Path) -> None:
    file = tmp_path / "test.txt"
    assert not file.exists()


# ✅ REQUIRED: Return types on fixtures
@pytest.fixture
def config(tmp_path: Path) -> Config:
    return Config(path=tmp_path)


# ❌ REJECTED: Missing return type (ANN201)
def test_something(self):
    pass


# ❌ REJECTED: Missing parameter type (ANN001)
def test_with_fixture(self, tmp_path) -> None:
    pass


# ❌ REJECTED: Missing __init__ return type (ANN204)
def __init__(self, config: Config):
    self.config = config
```

**Ruff rules enforced:**

| Rule   | What it catches                        |
| ------ | -------------------------------------- |
| ANN001 | Missing type annotation on parameter   |
| ANN201 | Missing return type on public function |
| ANN204 | Missing return type on `__init__`      |

</type_annotations>

---

<named_constants>

Test values and configuration must use named constants, not inline literals.

```python
# ✅ REQUIRED: Named constants at module level
VALID_SCORE = 85
MIN_SCORE = 0
MAX_SCORE = 100
VALID_INPUT = "simple"
EXPECTED_RESULT = 42


class TestScoreValidation:
    def test_accepts_valid_score(self) -> None:
        assert validate_score(VALID_SCORE) is True

    def test_rejects_above_maximum(self) -> None:
        assert validate_score(MAX_SCORE + 1) is False


# ❌ REJECTED: Magic values (PLR2004)
class TestScoreValidationBad:
    def test_accepts_valid_score(self) -> None:
        assert validate_score(85) is True  # What is 85?

    def test_rejects_above_maximum(self) -> None:
        assert validate_score(101) is False  # Magic number
```

**Why named constants matter:**

- Sharing between tests and production code
- Clear documentation of what values mean
- Easy updates when requirements change
- Self-documenting test intent

**PLR2004 exemptions:** Ruff's magic value rule already exempts common idiomatic values: `0`, `1`, `""`, and `"__main__"`. You don't need constants for these.

```python
# ✅ OK: Idiomatic values are exempt
assert len(results) == 0
assert count == 1
if __name__ == "__main__":
    main()
```

</named_constants>

---

<naming_conventions>

**Lowercase Argument Names (N803)**

```python
# ❌ REJECTED: Uppercase argument names
def __init__(self, domain: ClockDomain, WIDTH: int = 8) -> None:
    pass


# ✅ REQUIRED: Lowercase argument names
def __init__(self, domain: ClockDomain, width: int = 8) -> None:
    pass
```

**Avoid Shadowing Builtins**

```python
# ❌ BAD: Shadows builtin `input`
@pytest.mark.parametrize("input,expected", TEST_CASES)
def test_processing(self, input: str, expected: int) -> None:
    pass


# ✅ GOOD: Descriptive name, no shadowing
@pytest.mark.parametrize(("input_val", "expected"), TEST_CASES)
def test_processing(self, input_val: str, expected: int) -> None:
    pass
```

**Why avoid `input` as a parameter name:**

- Shadows Python's builtin `input()` function
- Causes A002 (argument shadows builtin) lint errors
- Makes code confusing if you need the actual `input()` function
- The tuple form `("input_val", "expected")` is also preferred by pytest for clarity

</naming_conventions>

---

<s101_policy>

Ruff's S101 rule flags `assert` statements because they can be disabled with Python's `-O` flag.

**Policy:** `assert` is ACCEPTED in test files because:

1. pytest rewrites assertions for better error messages
2. Tests are never run with `-O` optimization
3. The alternative (`if not x: raise AssertionError`) adds noise

**Required project configuration** in `pyproject.toml`:

```toml
[tool.ruff.lint.per-file-ignores]
"**/test_*.py" = ["S101"]
"**/tests/**/*.py" = ["S101"]
```

If the project hasn't configured this, tests will fail linting. Fix by adding the config, not by avoiding `assert`.

</s101_policy>

---

<type_strictness>

```python
# ❌ REJECTED: Unqualified Any — hides real types
def process(data: Any) -> Any: ...


# ✅ REQUIRED: Use concrete types or justify Any
def process(data: dict[str, str]) -> ProcessResult: ...


# ❌ REJECTED: type: ignore without explanation
result = cast(str, value)  # type: ignore

# ✅ REQUIRED: Explain what's being suppressed and why
result = cast(str, value)  # type: ignore[no-untyped-call]  # third-party lib missing stubs
```

**Rules:**

| Rule            | What it catches                        |
| --------------- | -------------------------------------- |
| mypy strict     | Unqualified `Any` usage                |
| (manual review) | `# type: ignore` without justification |

</type_strictness>

---

<modern_syntax>

```python
# ❌ REJECTED: Old-style type unions (UP007)
from typing import Optional, Union


def get_user(id: int) -> Optional[User]: ...
def process(value: Union[str, int]) -> None: ...


# ✅ REQUIRED: Modern union syntax
def get_user(id: int) -> User | None: ...
def process(value: str | int) -> None: ...


# ❌ REJECTED: Old-style generic types (UP006)
from typing import List, Dict, Tuple


def get_users() -> List[User]: ...
def get_config() -> Dict[str, Any]: ...


# ✅ REQUIRED: Lowercase generics
def get_users() -> list[User]: ...
def get_config() -> dict[str, Any]: ...
```

**Ruff rules enforced:**

| Rule  | What it catches                                               |
| ----- | ------------------------------------------------------------- |
| UP006 | `List`, `Dict`, `Tuple` instead of `list`, `dict`, `tuple`    |
| UP007 | `Optional[X]`, `Union[X, Y]` instead of `X \| None`, `X \| Y` |

</modern_syntax>

---

<error_handling>

```python
# ❌ REJECTED: Bare except (E722)
try:
    process()
except:
    pass

# ❌ REJECTED: Swallowing all errors (S110)
try:
    process()
except Exception:
    pass

# ✅ REQUIRED: Catch specific exceptions
try:
    process()
except ValueError as e:
    log.error("Invalid input: %s", e)
    raise
```

**Ruff rules enforced:**

| Rule | What it catches                          |
| ---- | ---------------------------------------- |
| E722 | Bare `except:` clause                    |
| S110 | `try`-`except`-`pass` on broad exception |

</error_handling>

---

<security>

```python
# ❌ REJECTED: Hardcoded secrets (S105/S106)
API_KEY = "sk-1234567890"
password = "hunter2"

# ❌ REJECTED: eval/exec (S307/S102)
result = eval(user_input)
exec(code_string)

# ❌ REJECTED: shell=True with untrusted input (S602)
subprocess.run(f"grep {user_input} file.txt", shell=True)

# ❌ REJECTED: Pickle with untrusted data (S301)
data = pickle.loads(untrusted_bytes)

# ❌ REJECTED: SSL verification disabled (S501)
requests.get(url, verify=False)
```

Context matters for security rules — a CLI tool invoked by the user has different trust boundaries than a web service. See `/auditing-python` for false positive handling.

**Ruff rules enforced:**

| Rule | What it catches                           |
| ---- | ----------------------------------------- |
| S105 | Hardcoded password in variable assignment |
| S106 | Hardcoded password in function argument   |
| S307 | Use of `eval()`                           |
| S102 | Use of `exec()`                           |
| S602 | `subprocess` call with `shell=True`       |
| S301 | Use of `pickle.loads`                     |
| S501 | SSL verification disabled                 |

</security>

---

<resource_management>

```python
# ❌ REJECTED: File not opened with context manager (SIM115)
f = open("file.txt")
data = f.read()
f.close()

# ✅ REQUIRED: Use context managers
with open("file.txt") as f:
    data = f.read()
```

**Ruff rules enforced:**

| Rule   | What it catches                   |
| ------ | --------------------------------- |
| SIM115 | Open file without context manager |

</resource_management>

---

<code_hygiene>

```python
# ❌ REJECTED: Commented-out code (ERA001)
# result = old_function(x)
# if condition:
#     do_something()

# ❌ REJECTED: Unused imports (F401)
import os  # never used

# ❌ REJECTED: sys.path manipulation
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
```

**Ruff rules enforced:**

| Rule   | What it catches    |
| ------ | ------------------ |
| ERA001 | Commented-out code |
| F401   | Unused imports     |

</code_hygiene>

---

<import_hygiene>

**Depth Rules**

| Depth     | Syntax              | Verdict | Rationale                                      |
| --------- | ------------------- | ------- | ---------------------------------------------- |
| Same dir  | `from . import x`   | OK      | Module-internal, same package                  |
| 1 level   | `from .. import x`  | REVIEW  | Is this truly module-internal?                 |
| 2+ levels | `from ... import x` | REJECT  | Use absolute import — crosses package boundary |

**Module-Internal vs. Infrastructure**

**Module-internal files** live in the same package and move together. Relative imports are acceptable:

```python
# ✅ ACCEPTABLE: Same package, files move together
from . import tokens
from .position import Position
```

**Infrastructure** is stable code that doesn't move when your feature moves. Must use absolute imports:

```python
# ❌ REJECTED: Deep relative to infrastructure
from .......tests.helpers import create_tree

# ✅ REQUIRED: Absolute import
from myproject_testing.helpers import create_tree
```

**Anti-Patterns**

```python
# ❌ REJECTED: sys.path manipulation
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# ❌ REJECTED: Deep relative imports
from .....lib.utils import helper

# ❌ REJECTED: Assuming working directory
from lib.utils import helper  # Only works if CWD is project root
```

**Required Project Setup**

**1. Use `src` layout:**

```text
myproject/
├── src/
│   └── myproject/
│       ├── __init__.py
│       └── ...
├── tests/
│   ├── __init__.py
│   └── ...
└── pyproject.toml
```

**2. Configure `pyproject.toml`:**

```toml
[project]
name = "myproject"

[tool.setuptools.packages.find]
where = ["src"]
```

**3. Install in editable mode:**

```bash
uv pip install -e .
```

</import_hygiene>

---

<rejection_criteria_summary>

| Issue                      | Example                           | Rule    |
| -------------------------- | --------------------------------- | ------- |
| Missing `-> None` on test  | `def test_foo(self):`             | ANN201  |
| Untyped fixture parameter  | `def test_foo(self, tmp_path):`   | ANN001  |
| Missing `-> None` on init  | `def __init__(self, x: int):`     | ANN204  |
| Magic values in assertions | `assert result == 42`             | PLR2004 |
| Uppercase argument names   | `def __init__(self, WIDTH=8):`    | N803    |
| Shadowing builtins         | `def foo(input: str):`            | A002    |
| Bare `except:`             | `except: pass`                    | E722    |
| Swallowing exceptions      | `except Exception: pass`          | S110    |
| Hardcoded secrets          | `API_KEY = "sk-..."`              | S105    |
| `eval()` / `exec()`        | `eval(user_input)`                | S307    |
| `shell=True`               | `subprocess.run(cmd, shell=True)` | S602    |
| Pickle with untrusted data | `pickle.loads(data)`              | S301    |
| SSL disabled               | `requests.get(url, verify=False)` | S501    |
| No context manager         | `f = open(...); f.close()`        | SIM115  |
| Old union syntax           | `Optional[X]`, `Union[X, Y]`      | UP007   |
| Old generic syntax         | `List[str]`, `Dict[str, int]`     | UP006   |
| Commented-out code         | `# old_function(x)`               | ERA001  |
| Unused imports             | `import os  # never used`         | F401    |
| Deep relative imports      | `from ... import x`               | manual  |
| `sys.path` manipulation    | `sys.path.insert(0, ...)`         | manual  |
| Unqualified `Any`          | `def f(x: Any) -> Any:`           | mypy    |
| `type: ignore` no reason   | `x = foo()  # type: ignore`       | manual  |

</rejection_criteria_summary>
