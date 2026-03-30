---
name: auditing-python-tests
description: >-
  ALWAYS invoke this skill when auditing Python tests for evidentiary value and spec compliance.
  NEVER audit tests without this skill.
---

<objective>

Python-specific test audit. Extends `/auditing-tests` with Python supplements for each evidence property: coupling, falsifiability, alignment, coverage.

Read `/auditing-tests` first — it defines the 4-property evidence model and ordered workflow. This skill adds only what is Python-specific.

</objective>

<quick_start>

**PREREQUISITE**: Read `/auditing-tests` and its evidence model before auditing.

1. Run the `/auditing-tests` workflow: load context → map assertions → audit coupling → falsifiability → alignment → coverage → verdict
2. At each property step, apply the Python supplement below
3. First property failure = REJECT (skip remaining properties for that assertion)

**Python filename conventions** for assertion-to-test mapping:

| Level | Filename suffix   | Example                       |
| ----- | ----------------- | ----------------------------- |
| 1     | `_unit.py`        | `test_uart_tx_unit.py`        |
| 2     | `_integration.py` | `test_uart_tx_integration.py` |
| 3     | `_e2e.py`         | `test_uart_tx_e2e.py`         |

</quick_start>

<essential_principles>

Follow the four principles from `/auditing-tests`: **COUPLING FIRST**, **RUN COVERAGE DON'T GUESS**, **NO MECHANICAL DETECTION**, **BINARY VERDICT**.

**NO CODE QUALITY CHECKS.**

Type annotations (`-> None`), magic values, test organization, naming conventions — these are linting concerns enforced by `/standardizing-python-testing`, mypy, and ruff. The auditor evaluates evidence quality only. A test with perfect Python style and zero evidentiary value must be REJECTED. A test with missing type hints but genuine evidence of spec fulfillment is not rejected by this audit.

</essential_principles>

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

| Exception                | Python pattern                                 | Why coupling maintained                    |
| ------------------------ | ---------------------------------------------- | ------------------------------------------ |
| 1. Failure modes         | Class implementing Protocol, raises error      | Tests error handling of real integration   |
| 2. Interaction protocols | Class with call-recording list                 | Tests call sequence against real interface |
| 3. Time/concurrency      | `patch("time.time")`, `patch("random.random")` | Tests timing logic with real code          |
| 4. Safety                | Class that records but doesn't execute         | Tests intent without destructive effects   |
| 5. Combinatorial cost    | Configurable class mirroring real behavior     | Tests breadth with real-shaped data        |
| 6. Observability         | Class capturing request details                | Tests details real system hides            |
| 7. Contract testing      | Stub validated against schema                  | Tests serialization against real contract  |

For each test double found:

1. Identify which exception applies (must be one of the 7)
2. Verify the double is a class implementing a Protocol — not `@patch`/`Mock()`/`MagicMock`
3. Exception 3 (time/concurrency) may legitimately use `patch("time.time")` — this is the one case where `patch` is acceptable
4. All other `@patch`/`Mock()`/`MagicMock`/`mocker.patch` usage → coupling is severed → REJECT

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

<concrete_examples>

**Example 1: APPROVED**

Auditing `spx/21-uart.enabler/43-transmitter.outcome/`

Assertion mapping:

```text
Assertion: MUST: Given a UartTx configured for 8N1 at 115200 baud,
           when byte 0x55 is written, then TX line outputs start bit,
           8 data bits (LSB first), and stop bit
Type: Scenario
Test: tests/test_uart_tx_unit.py ✓ exists
```

Coupling:

```text
Import: from product.uart_tx import UartTx
Classification: Direct — codebase import of module under test
```

Falsifiability:

```text
Module: product/uart_tx.py
Mutation: UartTx.write() outputs bits in MSB order instead of LSB
Impact: assert bits == [0, 1, 0, 1, ...] fails — genuine falsifiability
No @patch or Mock() found.
```

Alignment:

```text
Assertion says: "8N1 at 115200 → start bit, 8 data bits LSB first, stop bit"
Test does: UartTx(config="8N1", baud=115200).write(0x55) → asserts exact bit sequence
Match: exact behavior tested ✓
Assertion type: Scenario → example-based test strategy ✓
```

Coverage:

```text
Baseline: product/uart_tx.py — 31.0%
With test: product/uart_tx.py — 72.4%
Delta: +41.4% ✓
```

```text
Audit: spx/21-uart.enabler/43-transmitter.outcome/
Verdict: APPROVED

| # | Assertion       | Coupling | Falsifiability          | Alignment | Coverage | Verdict |
|---|-----------------|----------|-------------------------|-----------|----------|---------|
| 1 | 8N1 TX bit seq  | Direct   | MSB/LSB swap breaks test | ✓        | +41.4%   | PASS    |
```

---

**Example 2: REJECT — coupling severed by @patch**

Auditing `spx/32-api.enabler/54-auth.outcome/`

```text
Assertion: MUST: Given valid credentials, when authenticating,
           then a session token is returned from the database
Test: tests/test_auth_integration.py ✓ exists
```

Coupling:

```text
Import: from product.database import query
Classification: Direct — but...
Line 8: @patch("product.database.query")
→ Coupling severed. Real database.query never runs.
```

```text
Audit: spx/32-api.enabler/54-auth.outcome/
Verdict: REJECT

| # | Assertion     | Property Failed | Finding          | Detail                            |
|---|---------------|-----------------|------------------|-----------------------------------|
| 1 | Session token | Falsifiability  | coupling severed | @patch replaces database.query    |

How tests could pass while assertions fail:
Database query is entirely replaced with a Mock returning hardcoded results.
Any schema change, connection failure, or constraint violation in the real
database is invisible. The test verifies behavior against a fake that always
returns [{"id": 1}].
```

---

**Example 3: REJECT — TYPE_CHECKING import disguised as coupling**

Auditing `spx/15-theme.enabler/22-contrast.outcome/`

```text
Assertion: MUST: All theme colors meet WCAG AA contrast ratio (4.5:1)
Test: tests/test_contrast_unit.py ✓ exists
```

Coupling:

```text
Imports:
  import pytest                                → Framework
  from typing import TYPE_CHECKING             → Stdlib
  if TYPE_CHECKING:
      from product.theme import ThemeColor         → Type-only (erased at runtime)

Zero runtime codebase imports → no coupling (tautology).
```

```text
Audit: spx/15-theme.enabler/22-contrast.outcome/
Verdict: REJECT

| # | Assertion        | Property Failed | Finding     | Detail                                            |
|---|------------------|-----------------|-------------|---------------------------------------------------|
| 1 | WCAG AA contrast | Coupling        | no coupling | Only pytest + TYPE_CHECKING import (erased at runtime) |

How tests could pass while assertions fail:
Test declares its own color tuples and checks contrast math against them.
The actual theme colors in product/theme.py are never imported at runtime. If
all theme colors are changed to pure white, this test still passes.
```

</concrete_examples>

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
| **Coverage**       | Zero delta on assertion-relevant source files               | Coverage       |

</rejection_triggers>

<success_criteria>

Audit is complete when:

- [ ] `/auditing-tests` workflow executed (load context → map assertions → 4 properties → verdict)
- [ ] Python supplements applied at each property step
- [ ] Coupling: imports classified (including `TYPE_CHECKING`, relative imports, `__init__.py` re-exports)
- [ ] Falsifiability: `@patch`/`Mock()`/`MagicMock` patterns checked, exceptions identified
- [ ] Alignment: property-based testing verified for parsers/serializers/math/algorithms
- [ ] Coverage: actual deltas from pytest-cov command
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has property, finding category, detail
- [ ] For REJECT: "how tests could pass while assertions fail" explained

</success_criteria>
