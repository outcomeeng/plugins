<python_test_audit_examples>

<contents>

- Example 1: Approved
- Example 2: Rejected, Coupling Severed By @patch
- Example 3: Rejected, TYPE_CHECKING Import Disguised As Coupling

</contents>

<example number="1" verdict="approved">

Auditing `spx/55-example.enabler/21-transmitter.outcome/`

Assertion mapping:

```text
Assertion: MUST: Given a UartTx configured for 8N1 at 115200 baud,
           when byte 0x55 is written, then TX line outputs start bit,
           8 data bits (LSB first), and stop bit
Type: Scenario
Test: tests/test_uart_tx.scenario.l1.py exists
```

Coupling:

```text
Import: from product.uart_tx import UartTx
Classification: Direct - codebase import of module under test
```

Falsifiability:

```text
Module: product/uart_tx.py
Mutation: UartTx.write() outputs bits in MSB order instead of LSB
Impact: assert bits == [0, 1, 0, 1, ...] fails
No @patch or Mock() found.
```

Alignment:

```text
Assertion says: "8N1 at 115200 -> start bit, 8 data bits LSB first, stop bit"
Test does: UartTx(config="8N1", baud=115200).write(0x55) -> asserts exact bit sequence
Match: exact behavior tested
Assertion type: Scenario -> example-based test strategy
```

Coverage trace:

```text
Source path: product/uart_tx.py
Test path: tests/test_uart_tx.scenario.l1.py -> UartTx.write
Judgment: reaches the assertion-relevant write path
```

```text
Audit: spx/55-example.enabler/21-transmitter.outcome/
Verdict: APPROVED

| # | Assertion      | Coupling | Falsifiability           | Alignment | Coverage trace | Verdict |
|---|----------------|----------|--------------------------|-----------|----------------|---------|
| 1 | 8N1 TX bit seq | Direct   | MSB/LSB swap breaks test | PASS      | Reaches write path | PASS |
```

</example>

<example number="2" verdict="rejected" reason="coupling-severed-by-patch">

Auditing `spx/55-example.enabler/21-auth.outcome/`

```text
Assertion: MUST: Given valid credentials, when authenticating,
           then a session token is returned from the database
Test: tests/test_auth.scenario.l2.py exists
```

Coupling:

```text
Import: from product.database import query
Classification: Direct, but line 8 uses @patch("product.database.query")
Result: Coupling severed. Real database.query never runs.
```

```text
Audit: spx/55-example.enabler/21-auth.outcome/
Verdict: REJECTED

| # | Assertion     | Property Failed | Finding          | Detail                         |
|---|---------------|-----------------|------------------|--------------------------------|
| 1 | Session token | Falsifiability  | coupling severed | @patch replaces database.query |

How tests could pass while assertions fail:
Database query is entirely replaced with a Mock returning hardcoded results.
Any schema change, connection failure, or constraint violation in the real
database is invisible. The test verifies behavior against a fake that always
returns [{"id": 1}].
```

</example>

<example number="3" verdict="rejected" reason="type-checking-import-disguised-as-coupling">

Auditing `spx/55-example.enabler/21-contrast.outcome/`

```text
Assertion: MUST: All theme colors meet WCAG AA contrast ratio (4.5:1)
Test: tests/test_contrast.compliance.l1.py exists
```

Coupling:

```text
Imports:
  import pytest                            -> Framework
  from typing import TYPE_CHECKING         -> Stdlib
  if TYPE_CHECKING:
      from product.theme import ThemeColor -> Type-only, erased at runtime

Zero runtime codebase imports -> no coupling.
```

```text
Audit: spx/55-example.enabler/21-contrast.outcome/
Verdict: REJECTED

| # | Assertion        | Property Failed | Finding     | Detail                                      |
|---|------------------|-----------------|-------------|---------------------------------------------|
| 1 | WCAG AA contrast | Coupling        | no coupling | Only pytest plus TYPE_CHECKING runtime path |

How tests could pass while assertions fail:
Test declares its own color tuples and checks contrast math against them.
The actual theme colors in product/theme.py are never imported at runtime. If
all theme colors are changed to pure white, this test still passes.
```

</example>

</python_test_audit_examples>
