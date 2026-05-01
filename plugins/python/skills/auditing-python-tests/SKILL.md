---
name: auditing-python-tests
description: >-
  ALWAYS invoke this skill when auditing tests for Python or after writing tests.
  NEVER use auditing-python for test code.
---

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-python/SKILL.md" || echo "standardizing-python not found — invoke skill python:standardizing-python now"`

!`cat "${CLAUDE_SKILL_DIR}/../standardizing-python-tests/SKILL.md" || echo "standardizing-python-tests not found — invoke skill python:standardizing-python-tests now"`

!`cat "${CLAUDE_SKILL_DIR}/../../../spec-tree/skills/testing/SKILL.md" || echo "testing not found — invoke skill spec-tree:testing now"`

!`cat "${CLAUDE_SKILL_DIR}/../../../spec-tree/skills/auditing-tests/SKILL.md" || echo "auditing-tests not found — invoke skill spec-tree:auditing-tests now"`

<codex_fallback>
If you see `cat` commands above rather than skill content, shell injection did not run (Codex or similar environment). Invoke these skills now before proceeding:

1. Skill `python:standardizing-python`
2. Skill `python:standardizing-python-tests`
3. Skill `spec-tree:testing`
4. Skill `spec-tree:auditing-tests`

</codex_fallback>

<objective>

Python test audit. Three gates in strict sequence, fail-closed:

1. **Gate 0 — Deterministic**: filename policy, ruff, mypy, pytest collection, and coverage-tool availability check filenames, linting, types, collection, and coverage setup. Claude does not judge these rules — Gate 0 output is routed into the verdict verbatim.
2. **Gate 1 — Assertion audit**: per-assertion LLM audit using the `/auditing-tests` workflow — coupling, falsifiability, alignment, coverage — with Python supplements applied at each property step.
3. **Gate 2 — Architectural DRY**: LLM scan for repeated cross-file setup patterns that belong in shared fixtures or harnesses.

A gate failure skips every later gate.

</objective>

<quick_start>

Run Gate 0 tools, then apply the `/auditing-tests` Gate 1 workflow with Python supplements at each property step. First property failure = REJECT for that assertion.

</quick_start>

<essential_principles>

Follow the four principles from `/auditing-tests`: **COUPLING FIRST**, **RUN COVERAGE DON'T GUESS**, **NO MECHANICAL DETECTION**, **BINARY VERDICT**.

**NO CODE QUALITY CHECKS.**

Type annotations (`-> None`), magic values, test organization, naming conventions — these are linting concerns enforced by `/standardizing-python-tests`, mypy, and ruff. The auditor evaluates evidence quality only. A test with perfect Python style and zero evidentiary value must be REJECTED. A test with missing type hints but genuine evidence of spec fulfillment is not rejected by this audit.

</essential_principles>

<prerequisites>

1. Invoking 4 skills: Already done above.
2. Read local overlay files, they supersede any skills and are loaded below:

!`cat "spx/local/python.md" || echo "spx/local/python.md not found; apply skills only."`
!`cat "spx/local/python-tests.md" || echo "spx/local/python-tests.md not found; apply skills only."`

<codex_fallback>
If you see `cat` commands above, shell injection did not run (Codex or similar environment). Look for project-specific overlay files:

1. Read `spx/local/python.md` if it exists. It supersedes any skills.
2. Read `spx/local/python-tests.md` if it exists. It supersedes any skills.

</codex_fallback>

3. Invoke `/contextualizing` on the spec node under audit — `<SPEC_TREE_CONTEXT>` marker must be present before Gate 1

Gate 0 tool dependencies:

- `ruff` installed in the consumer project (F1, V1)
- `mypy` installed in the consumer project (V1)
- `pytest` installed in the consumer project (V1, C1)

If any tool is unavailable, Gate 0 records a terminal finding and the audit aborts.

Do not run `spx validation literal` for Python audits. The literal validator is TypeScript-only and reports `Skipping Literal (TypeScript not detected in project)` in Python projects.

</prerequisites>

<gate_0_deterministic>

Run the checks below and merge their findings.

<check id="F1" name="filename_policy">
List Python test files under the target node:

```bash
rg --files <spec-node-path>/tests/ --glob '*.py'
```

Each file must match `<subject>.<evidence>.<level>[.<variant>].py` where:

- `<evidence>` is one of: `scenario`, `mapping`, `conformance`, `property`, `compliance`
- `<level>` is one of: `l1`, `l2`, `l3`
- `<variant>` is optional (e.g., `async`, `hypothesis`)

Fail Gate 0 for files that do not match this pattern, unless a repo-local overlay defines a different Python test filename convention.
</check>

<check id="V1" name="python_validation">
Run the validation sequence:

```bash
ruff check <spec-node-path>/tests/
mypy <spec-node-path>/tests/
pytest --collect-only -q <spec-node-path>/tests/
```

Fail Gate 0 if any command fails. A non-compiling or uncollectable test file has no auditable evidence surface.
</check>

<check id="C1" name="coverage_tool">
Verify coverage tooling is available:

```bash
pytest --co -q --collect-only --tb=no <spec-node-path>/tests/ | head -1
python -m pytest --co -q 2>/dev/null | grep -c 'test session starts' || true
coverage --version 2>/dev/null || python -m pytest --co -q --no-header 2>&1 | head -1
```

Fail Gate 0 when project instructions require measured coverage and neither `coverage` nor `pytest-cov` is available.
</check>

Gate 0 status:

| Condition      | Status | Action                                                        |
| -------------- | ------ | ------------------------------------------------------------- |
| F1 or V1 fails | FAIL   | Record findings, skip Gates 1 and 2                           |
| C1 only        | PASS   | Record coverage note; continue with other evidence properties |
| all pass       | PASS   | Proceed to Gate 1                                             |

Gate 0 check IDs:

| check_id | Source                          |
| -------- | ------------------------------- |
| F1       | Filename policy                 |
| V1       | ruff / mypy / pytest collection |
| C1       | Coverage tool availability      |

</gate_0_deterministic>

<python_supplements>

Apply these at the corresponding step of the `/auditing-tests` workflow.

<supplement property="coupling">

**Python import classification:**

| Import pattern                                            | Classification                          |
| --------------------------------------------------------- | --------------------------------------- |
| `import pytest`                                           | Framework — does not count              |
| `from hypothesis import given`                            | Framework — does not count              |
| `import json`                                             | Stdlib — does not count                 |
| `from typing import TYPE_CHECKING`                        | Type-only — does not count              |
| `from product.config import parse_config`                 | Codebase (production) — counts          |
| `from ..config import parse_config`                       | Codebase (production relative) — counts |
| `from product_testing.harnesses import ConfigTestHarness` | Codebase (test infra) — counts          |

**Production code vs test harnesses — both are codebase imports:**

| Import target          | Correct pattern                             | Classification    |
| ---------------------- | ------------------------------------------- | ----------------- |
| Production module      | `from product.config import parse_config`   | Direct coupling   |
| Test harness (package) | `from product_testing.harnesses import ...` | Indirect coupling |
| Co-located test helper | `from .helpers import ConfigTestHarness`    | Indirect coupling |
| Shared fixtures        | `from tests.conftest import db_harness`     | Indirect coupling |

Test harnesses wrap production modules, so they provide **indirect coupling**. When a test imports a harness, follow the chain: verify the harness itself has direct coupling to the module the assertion is about. If the harness is also a tautology, the coupling chain is broken.

**Deep relative imports to test infrastructure are a red flag:**

```python
# ❌ Red flag — deep relative to test infra
from ....tests.harnesses import ConfigTestHarness
# Likely correct but fragile — verify the harness has real coupling

# ✅ Correct — package import to test infra
from product_testing.harnesses import ConfigTestHarness

# ✅ Also correct — co-located helper via relative import
from .helpers import ConfigTestHarness
```

Deep relative imports (`from ....`) are not themselves a coupling failure — the audit cares whether the import ultimately reaches the module under test, not the path style. But deep relative imports to test infrastructure signal the test may be importing a shared harness that wraps a different module than the assertion targets. Always trace the chain.

**`TYPE_CHECKING` imports are not coupling.** Imports inside `if TYPE_CHECKING:` blocks are erased at runtime — the test has zero runtime dependency on the module. If all codebase imports are under `TYPE_CHECKING`, the test is a tautology.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from product.theme import ThemeColor  # Erased at runtime — no coupling

# Zero runtime codebase imports → tautology
```

**`__init__.py` re-exports can mask false coupling.** If the test imports from a package `__init__.py`, verify the specific name used is the one the assertion is about — not a sibling re-export from the same package.

```python
# Assertion is about parse_config, but test uses validate_config from same package
from product.config import validate_config
# parse_config is also exported from product.config but never called → false coupling
```

</supplement>

<supplement property="falsifiability">

**Python mocking patterns that sever coupling:**

```python
# Coupling severed — real module replaced
from unittest.mock import patch, Mock


@patch("product.database.query")
def test_auth(mock_query: Mock) -> None:
    mock_query.return_value = [{"id": 1}]
    # Real database.query never runs


# Coupling severed — MagicMock replaces behavior
from unittest.mock import MagicMock

database = MagicMock()
database.query.return_value = [{"id": 1}]


# Coupling severed — pytest-mock
def test_auth(mocker: MockerFixture) -> None:
    mocker.patch("product.database.query", return_value=[{"id": 1}])
```

**Legitimate alternatives mapped to `/testing` exceptions:**

| Exception                | Python pattern                             | Why coupling maintained                    |
| ------------------------ | ------------------------------------------ | ------------------------------------------ |
| 1. Failure modes         | Class implementing Protocol, raises error  | Tests error handling of real integration   |
| 2. Interaction protocols | Class with call-recording list             | Tests call sequence against real interface |
| 3. Time/concurrency      | Injected clock or controllable scheduler   | Tests timing logic with real code          |
| 4. Safety                | Class that records but doesn't execute     | Tests intent without destructive effects   |
| 5. Combinatorial cost    | Configurable class mirroring real behavior | Tests breadth with real-shaped data        |
| 6. Observability         | Class capturing request details            | Tests details real system hides            |
| 7. Contract testing      | Stub validated against schema              | Tests serialization against real contract  |

For each test double found:

1. Identify which exception applies (must be one of the 7)
2. Verify the double is a class implementing a Protocol — not `@patch`/`Mock()`/`MagicMock`
3. Any `@patch`/`Mock()`/`MagicMock`/`mocker.patch` usage replacing behavior under test → coupling is severed → REJECT

</supplement>

<supplement property="alignment">

**Property-based testing via Hypothesis is required for specific assertion types:**

| Code type               | Required property        | Hypothesis pattern        |
| ----------------------- | ------------------------ | ------------------------- |
| Parsers                 | `parse(format(x)) == x`  | `@given(st.text())`       |
| Serialization           | `decode(encode(x)) == x` | `@given(valid_objects())` |
| Mathematical operations | Algebraic properties     | `@given(st.integers())`   |
| Complex algorithms      | Invariant preservation   | `@given(valid_inputs())`  |

If the spec assertion describes a Property-type claim about a parser, serializer, or math operation, and the test uses only example-based assertions:

**REJECT — "misaligned: Property assertion requires property-based test strategy."**

```python
# ❌ REJECT: Parser assertion with only example-based test
def test_parse_json_simple() -> None:
    result = parse('{"key": "value"}')
    assert result == {"key": "value"}


# Missing: @given + roundtrip property


# ✅ PASS: Meaningful roundtrip property
@given(valid_json_values())
def test_roundtrip(value: JsonValue) -> None:
    assert parse(format(value)) == value
```

Verify property quality — `@given` that only checks "doesn't crash" is not a meaningful property:

```python
# ❌ REJECT: Trivial property (only tests "doesn't crash")
@given(st.text())
def test_parse_doesnt_crash(text: str) -> None:
    try:
        parse(text)
    except ParseError:
        pass  # No assertion about behavior
```

For filename conventions, source-owned values, inline diagnostics, fixtures, and harness placement, defer to `/standardizing-python-tests`. Treat those as standards issues unless they break coupling, falsifiability, alignment, or coverage directly.

</supplement>

<supplement property="coverage">

**Python coverage commands (pytest-cov):**

Baseline (excluding test under audit):

```bash
just run test --cov=product --cov-report=term -- --ignore=path/to/test_under_audit.py
```

With test:

```bash
just run test --cov=product --cov-report=term path/to/test_under_audit.py
```

**Alternative tooling:** Projects may use `coverage.py` directly or different `--cov` targets. Check `pyproject.toml` for `[tool.pytest.ini_options]` and `[tool.coverage]` settings.

Report actual deltas:

```text
Baseline: product/config_parser.py — 43.2%
With test: product/config_parser.py — 67.8%
Delta: +24.6% — new coverage ✓
```

</supplement>

</python_supplements>

<gate_2_architectural>

Runs only if Gate 1 is PASS. Scan in-scope test files for repeated setup patterns that belong in shared fixtures or harnesses.

Trigger: two or more in-scope tests sharing any of these patterns:

- identical `@pytest.fixture` body (same dependencies, same setup logic)
- repeated `httpx.AsyncClient(app=...)` or `aiohttp.ClientSession` configuration
- repeated database seeding or transaction setup
- repeated `tempfile.TemporaryDirectory()` or `tmp_path` scaffolding with identical structure
- repeated mock patches (`@patch("same.module.path")`) across multiple test files
- repeated `conftest.py`-style setup appearing inline in multiple files instead of being shared

Each finding names the pattern, lists at least two occurrences with file and line, and proposes the nearest common location: a `product_testing/harnesses/<name>.py` module or an addition to `tests/conftest.py`.

Gate 2 status:

- PASS if no repeated setup pattern appears in two or more in-scope tests.
- FAIL if any repeated setup pattern appears in two or more in-scope tests.

</gate_2_architectural>

<verdict_format>

Follow `<verdict_format>` in `/auditing-tests`. Gate 0 check IDs for Python: F1, V1, C1 (see `<gate_0_deterministic>` for the check-to-command mapping). Gate 2 extraction target: `product_testing/harnesses/{name}.py` or `tests/conftest.py`.

</verdict_format>

<reference_guides>
Use `references/python-test-audit-examples.md` when concrete approved and rejected Python audit examples are needed.
</reference_guides>

<failure_modes>

**Failure 1: Accepted TYPE_CHECKING import as coupling**

Reviewer saw `from product.theme import ThemeColor` inside an `if TYPE_CHECKING:` block and classified it as direct coupling. But `TYPE_CHECKING` is `False` at runtime — the import never executes. The test declared its own color values and verified contrast math with zero connection to any theme module.

How to avoid: Coupling supplement — `TYPE_CHECKING` imports do not count as codebase imports.

**Failure 2: Missed coupling severed by @patch**

Reviewer saw `from product.database import query` and classified it as direct coupling. The test function was decorated with `@patch("product.database.query")`. The real module never ran.

How to avoid: Falsifiability supplement — check for `@patch`/`Mock()`/`MagicMock` after confirming coupling. Import + patch = coupling severed.

**Failure 3: Confused **init**.py re-export with direct coupling**

Test imported `validate_config` from `product.config`. The assertion was about `parse_config`. Both are exported from the same `__init__.py`, but the test never called `parse_config`.

How to avoid: Coupling supplement — `__init__.py` re-exports can mask false coupling. Verify the specific name used matches the assertion.

**Failure 4: Distracted by code quality while test was a tautology**

Reviewer spent the entire audit checking for `-> None` annotations, magic values, and naming conventions. The test had perfect Python style and zero evidentiary value — it imported only pytest and hypothesis.

How to avoid: Essential principles — no code quality checks. Check the four evidence properties only.

</failure_modes>

<rejection_triggers>

| Category           | Trigger                                                     | Property       |
| ------------------ | ----------------------------------------------------------- | -------------- |
| **Coupling**       | Zero codebase imports (only framework/stdlib)               | Coupling       |
| **Coupling**       | Only `TYPE_CHECKING` imports — erased at runtime            | Coupling       |
| **Coupling**       | `__init__.py` re-export of wrong name (false coupling)      | Coupling       |
| **Coupling**       | Import present but assertion-relevant function never called | Coupling       |
| **Falsifiability** | `@patch` replaces imported module                           | Falsifiability |
| **Falsifiability** | `Mock()` / `MagicMock` replaces real dependency             | Falsifiability |
| **Falsifiability** | `mocker.patch` (pytest-mock) replaces module                | Falsifiability |
| **Falsifiability** | Cannot name a concrete mutation that would fail the test    | Falsifiability |
| **Alignment**      | Parser/serializer without `@given` roundtrip                | Alignment      |
| **Alignment**      | Property assertion tested with only examples                | Alignment      |
| **Alignment**      | Test exercises different behavior than assertion describes  | Alignment      |
| **Coverage**       | Zero delta with baseline < 100% on assertion-relevant files | Coverage       |

</rejection_triggers>

<success_criteria>

Audit is complete when:

- [ ] Gate 0 run: ruff, mypy, and pytest collection all executed
- [ ] Gate 1 complete: every assertion evaluated — coupling (with Python supplements), falsifiability, alignment, coverage (if Gate 0 PASS)
- [ ] Gate 2 complete: in-scope tests scanned for repeated setup patterns (if Gate 1 PASS)
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has gate, step/property, and specific detail
- [ ] For REJECT: "how tests could pass while assertions fail" explained

</success_criteria>
