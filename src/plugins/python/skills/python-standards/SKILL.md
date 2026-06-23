---
name: python-standards
user-invocable: false
description: >-
  Python code standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The Python code standards every Python skill enforces.
</objective>

<success_criteria>
Code follows these standards when all ruff rules and mypy checks pass. See `${CLAUDE_SKILL_DIR}/references/rejection-criteria.md` for the complete rejection-criteria lookup with rule codes.
</success_criteria>

<reference_note>
This is a reference skill. Other Python skills load these standards. Do not invoke it directly — invoke `/code-python`, `/test-python`, or `/audit-python` instead.

These standards apply to ALL Python code: production and test code alike.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, it must also check for `spx/local/python.md` at the repository root. Read that file after this reference if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

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

<source_owned_values>

Production modules must own semantic literals through enums, schemas, registries, constructors, typed factories, or public constants that production consumers can import. Tests import those source-owned values instead of defining test-local constants.

```python
# ✅ REQUIRED: production source owns the domain contract
MIN_SCORE = 0
MAX_SCORE = 100


def validate_score(score: int) -> bool:
    return MIN_SCORE <= score <= MAX_SCORE


# ✅ REQUIRED IN TESTS: import the source-owned contract
from product.scoring import MAX_SCORE, validate_score


def test_rejects_above_maximum() -> None:
    assert validate_score(MAX_SCORE + 1) is False
```

```python
# ❌ REJECTED IN TESTS: local copy of source-owned domain values
MAX_SCORE = 100


def test_rejects_above_maximum() -> None:
    assert validate_score(MAX_SCORE + 1) is False
```

Ruff's PLR2004 rule catches many obscure magic values, but it does not decide ownership. A local test constant that duplicates production vocabulary is still wrong when lint passes.

```python
# ✅ OK: Idiomatic values are exempt
assert len(results) == 0
assert count == 1
if __name__ == "__main__":
    main()
```

**Artifacts are downstream of Python.** A YAML, HCL, bash, JSON schema, IaC template, or any other rendered artifact file is not a legitimate source-of-truth for Python code. A Python module either renders the artifact (producing it from a typed schema or template) or consumes it (parsing it into a typed structure), and that module owns the artifact's vocabulary. Consumers that need to reason about the artifact's labels, paths, step names, or tokens import from the owning module. When no such module exists yet, the missing module is the architectural defect — the artifact is not an exemption from source ownership.

**Container keys are vocabulary.** In dict literals, JSON-encoded strings, set or tuple members, and f-string templates, the *keys* and *members* are vocabulary and follow source ownership; only *values* may be synthetic at the call site. Construct containers via `{LABEL: synthetic_value, ...}` with `LABEL` imported from the owning production module, then serialize with `json.dumps` if a string is needed. A hand-written key is a hand-picked case for the parser or consumer that reads the container.

</source_owned_values>

---

<constant_objects>

When a module defines a set of related named values, choose the right container for the shape:

| Pattern                          | When to use                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `Final`-annotated dict           | String-to-string maps where keys and values are loosely related                                         |
| `StrEnum` (Python 3.11+)         | Closed set of string values with enumerable identity — prefer when call sites use `status is Status.OK` |
| Frozen `@dataclass(frozen=True)` | Richer shapes: structured config, typed records                                                         |

```python
# ✅ Final dict: loosely related string map
from typing import Final

HEADERS: Final = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# ✅ StrEnum: closed set with identity semantics (Python 3.11+)
from enum import StrEnum


class GateStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"


# ✅ Frozen dataclass: structured config record
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int
    backoff_seconds: float
    timeout_seconds: float


# ❌ REJECTED: plain class with uppercase fields — not immutable, no type narrowing
class Status:
    PASS = "pass"
    FAIL = "fail"
```

**No re-export of library constants.** When production code and tests both need an HTTP status code, both import from the same canonical source (`http.HTTPStatus`, `fastapi.status`, etc.). Never create a product-local re-export.

```python
# ❌ REJECTED: re-export in product code
from http import HTTPStatus

HTTP_OK = HTTPStatus.OK  # product-local alias

# ✅ REQUIRED: both production and test code import from the canonical source
from http import HTTPStatus

response_code = HTTPStatus.OK
```

</constant_objects>

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
- Makes code confusing when the actual `input()` function is needed
- The tuple form `("input_val", "expected")` is also preferred by pytest for clarity

</naming_conventions>

---

<s101_policy>

Ruff's S101 rule flags `assert` statements because they can be disabled with Python's `-O` flag.

**Policy:** `assert` is ACCEPTED in test files because:

1. pytest rewrites assertions for better error messages
2. Tests are never run with `-O` optimization
3. The alternative (`if not x: raise AssertionError`) adds noise

**Required product configuration** in `pyproject.toml`:

```toml
[tool.ruff.lint.per-file-ignores]
"**/test_*.py" = ["S101"]
"**/tests/**/*.py" = ["S101"]
```

If the product hasn't configured this, tests will fail linting. Fix by adding the config, not by avoiding `assert`.

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

Use modern syntax: `X | None` (not `Optional[X]`), `X | Y` (not `Union[X, Y]`), and lowercase generics `list[str]` / `dict[str, V]` (not `List` / `Dict`).

**Ruff rules enforced:**

| Rule  | What it catches                                               |
| ----- | ------------------------------------------------------------- |
| UP006 | `List`, `Dict`, `Tuple` instead of `list`, `dict`, `tuple`    |
| UP007 | `Optional[X]`, `Union[X, Y]` instead of `X \| None`, `X \| Y` |

</modern_syntax>

---

<error_handling>

Catch specific exceptions and handle or re-raise them; never a bare `except:` or a broad `except Exception: pass` that swallows errors.

```python
# ✅ REQUIRED: catch specific exceptions, then handle or re-raise
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

Context matters for security rules — a CLI tool invoked by the user has different trust boundaries than a web service. See `/audit-python` for false positive handling.

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

Acquire files and other resources with a context manager (`with open(...) as f:`), never a manual `open()` / `.close()` pair.

**Ruff rules enforced:**

| Rule   | What it catches                   |
| ------ | --------------------------------- |
| SIM115 | Open file without context manager |

</resource_management>

---

<code_hygiene>

Remove commented-out code and unused imports; never manipulate `sys.path` to reach modules — depend on an installed package instead (see `<import_hygiene>`).

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

**Infrastructure** is stable code that doesn't move when the feature moves. Absolute imports are required:

```python
# ❌ REJECTED: Deep relative to infrastructure
from .......tests.helpers import with_temp_product

# ✅ REQUIRED: Absolute import
from myproject_testing.harnesses import with_temp_product
```

**Anti-Patterns**

```python
# ❌ REJECTED: sys.path manipulation
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# ❌ REJECTED: Deep relative imports
from .....lib.utils import helper

# ❌ REJECTED: Assuming working directory
from lib.utils import helper  # Only works if CWD is product root
```

**Required Product Setup**

**1. Use explicit product package layout:**

```text
product/
├── product/
│   ├── __init__.py
│   └── ...
├── product_testing/
│   ├── __init__.py
│   ├── generators/
│   ├── harnesses/
│   └── fixtures/
└── pyproject.toml
```

**2. Configure `pyproject.toml`:**

```toml
[project]
name = "product"

[tool.setuptools.packages.find]
where = ["src"]
```

**3. Install in editable mode** (portable fallback; prefer the product's own wrapper):

```bash
python3 -m pip install -e .
```

</import_hygiene>

---

<rejection_criteria_summary>
The complete rejection-criteria lookup — every issue the sections above state, indexed by its ruff rule code (or `manual` / `review` / `mypy`) — lives in `${CLAUDE_SKILL_DIR}/references/rejection-criteria.md`.
</rejection_criteria_summary>
