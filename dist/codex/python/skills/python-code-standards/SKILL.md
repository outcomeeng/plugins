---
name: python-code-standards
user-invocable: false
description: >-
  Python code standards enforced across all skills. Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
The Python code standards every Python skill enforces.
</objective>

<success_criteria>
Code follows these standards when ruff and mypy pass and no type-annotation, source-ownership, constant-container, type-strictness, or import-hygiene rule in this reference remains violated.
</success_criteria>

<reference_note>
This is a reference skill: a set of standards, not a standalone workflow.

These standards apply to ALL Python code: production and test code alike.
</reference_note>

<repo_local_overlay>
Inside a repository, check for `spx/local/python.md` at the repository root. Read that file after this reference if it exists and apply it as repo-local routing to the product's governing specs and decisions. A local overlay supplements skill behavior; it does not declare product truth.
</repo_local_overlay>

<type_annotations>

ALL functions require complete type annotations, including test functions, fixtures, and `__init__`: every parameter is annotated, and every function declares a return type (`-> None` when it returns nothing).

```python
# ✅ REQUIRED
def test_creates_file(self, tmp_path: Path) -> None: ...


# ❌ REJECTED: missing return type (ANN201), parameter type (ANN001), `__init__` return type (ANN204)
def test_something(self): ...
def test_with_fixture(self, tmp_path) -> None: ...
def __init__(self, config: Config): ...
```

</type_annotations>

<source_owned_values>

Production modules own semantic literals through enums, schemas, registries, constructors, typed factories, or public constants that production consumers can import.

```python
# ✅ REQUIRED: production source owns the domain contract
MIN_SCORE = 0
MAX_SCORE = 100


def validate_score(score: int) -> bool:
    return MIN_SCORE <= score <= MAX_SCORE
```

Ruff's PLR2004 rule catches many obscure magic values, but it does not decide ownership. A local constant that duplicates production vocabulary is still wrong when lint passes. Idiomatic values (`0`, `1`, `"__main__"`) are exempt.

**Artifacts are downstream of Python.** A YAML, HCL, bash, JSON schema, IaC template, or any other rendered artifact file is not a legitimate source-of-truth for Python code. A Python module either renders the artifact (producing it from a typed schema or template) or consumes it (parsing it into a typed structure), and that module owns the artifact's vocabulary. Consumers that need to reason about the artifact's labels, paths, step names, or tokens import from the owning module. When no such module exists yet, the missing module is the architectural defect — the artifact is not an exemption from source ownership.

The test-side obligations — importing source-owned values, importing container keys — are stated in `python-test-standards`.

</source_owned_values>

<constant_objects>

When a module defines a set of related named values, choose the right container for the shape:

| Pattern                          | When to use                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `Final`-annotated dict           | String-to-string maps where keys and values are loosely related                                         |
| `StrEnum` (Python 3.11+)         | Closed set of string values with enumerable identity — prefer when call sites use `status is Status.OK` |
| Frozen `@dataclass(frozen=True)` | Richer shapes: structured config, typed records                                                         |

```python
# ✅ StrEnum: closed set with identity semantics
from enum import StrEnum


class GateStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"


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
```

</constant_objects>

<s101_policy>

`assert` is ACCEPTED in test files: pytest rewrites assertions for better error messages, and tests never run with `-O`.

**Required product configuration** in `pyproject.toml`:

```toml
[tool.ruff.lint.per-file-ignores]
"**/test_*.py" = ["S101"]
"**/tests/**/*.py" = ["S101"]
```

If the product hasn't configured this, tests will fail linting. Fix by adding the config, not by avoiding `assert`.

</s101_policy>

<type_strictness>

```python
# ❌ REJECTED: unqualified Any — hides real types (mypy strict)
def process(data: Any) -> Any: ...


# ✅ REQUIRED: concrete types
def process(data: dict[str, str]) -> ProcessResult: ...


# ❌ REJECTED: `type: ignore` without explanation (manual review)
result = cast(str, value)  # type: ignore

# ✅ REQUIRED: name the suppressed error and why
result = cast(str, value)  # type: ignore[no-untyped-call]  # third-party lib missing stubs
```

</type_strictness>

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
# ❌ REJECTED: sys.path manipulation — depend on an installed package instead
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

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
