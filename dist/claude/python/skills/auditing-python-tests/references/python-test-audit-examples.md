# Python Test Audit Examples

## Contents

- Example 1: Approved
- Example 2: Rejected, Coupling Severed By @patch
- Example 3: Rejected, TYPE_CHECKING Import Disguised As Coupling

## Example 1: Approved

Auditing `spx/21-uart.enabler/43-transmitter.outcome/`

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

Coverage:

```text
Baseline: product/uart_tx.py - 31.0%
With test: product/uart_tx.py - 72.4%
Delta: +41.4%
```

```text
Audit: spx/21-uart.enabler/43-transmitter.outcome/
Verdict: APPROVED

| # | Assertion      | Coupling | Falsifiability           | Alignment | Coverage | Verdict |
|---|----------------|----------|--------------------------|-----------|----------|---------|
| 1 | 8N1 TX bit seq | Direct   | MSB/LSB swap breaks test | PASS      | +41.4%   | PASS    |
```

## Example 2: Rejected, Coupling Severed By @patch

Auditing `spx/32-api.enabler/54-auth.outcome/`

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
Audit: spx/32-api.enabler/54-auth.outcome/
Verdict: REJECT

| # | Assertion     | Property Failed | Finding          | Detail                         |
|---|---------------|-----------------|------------------|--------------------------------|
| 1 | Session token | Falsifiability  | coupling severed | @patch replaces database.query |

How tests could pass while assertions fail:
Database query is entirely replaced with a Mock returning hardcoded results.
Any schema change, connection failure, or constraint violation in the real
database is invisible. The test verifies behavior against a fake that always
returns [{"id": 1}].
```

## Example 3: Rejected, TYPE_CHECKING Import Disguised As Coupling

Auditing `spx/15-theme.enabler/22-contrast.outcome/`

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
Audit: spx/15-theme.enabler/22-contrast.outcome/
Verdict: REJECT

| # | Assertion        | Property Failed | Finding     | Detail                                      |
|---|------------------|-----------------|-------------|---------------------------------------------|
| 1 | WCAG AA contrast | Coupling        | no coupling | Only pytest plus TYPE_CHECKING runtime path |

How tests could pass while assertions fail:
Test declares its own color tuples and checks contrast math against them.
The actual theme colors in product/theme.py are never imported at runtime. If
all theme colors are changed to pure white, this test still passes.
```
