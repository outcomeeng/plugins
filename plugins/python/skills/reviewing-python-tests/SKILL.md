---
name: reviewing-python-tests
description: >-
  ALWAYS invoke this skill when reviewing Python tests for evidentiary value and spec compliance.
  NEVER review tests without this skill.
---

<objective>
Python-specific test review. Extends `/reviewing-tests` with Python testing patterns, property-based testing requirements, and Python code quality checks.

</objective>

<quick_start>
**PREREQUISITE**: Read these skills first — they are the law:

- `/reviewing-tests` — Foundational review protocol (Phases 1–4: spec structure, evidentiary integrity, lower-level assumptions, ADR/PDR compliance)
- `/testing` — Methodology (5 stages, 5 factors, 7 exceptions)
- `/standardizing-python-testing` — Python testing standards

Execute the 4 foundational phases from `/reviewing-tests` first, then continue with the Python-specific phases below.

**Python-specific grep patterns** for foundational Phase 2 (evidentiary integrity):

```bash
# Find silent skips (REJECT if on required deps)
grep -rn "pytest.mark.skipif" {test_dir}
grep -rn "pytest.skip" {test_dir}

# Find mocking (any = REJECT)
grep -rn "@patch\|Mock()\|MagicMock\|mocker\." {test_dir}
```

**Python filename conventions** for foundational Phase 1.2 (test file linkage):

| Level | Filename suffix   | Example                       |
| ----- | ----------------- | ----------------------------- |
| 1     | `_unit.py`        | `test_uart_tx_unit.py`        |
| 2     | `_integration.py` | `test_uart_tx_integration.py` |
| 3     | `_e2e.py`         | `test_uart_tx_e2e.py`         |

When reporting findings, cite source skills:

- "Per /reviewing-tests Phase 1.1, assertion type must match test strategy"
- "Per /standardizing-python-testing, parsers MUST have property-based tests"

</quick_start>

<python_phases>
Execute these AFTER completing the 4 foundational phases from `/reviewing-tests`.

<phase name="property_based_testing">
Per `/testing` and `/standardizing-python-testing`, property-based testing is **MANDATORY** for:

| Code Type               | Required Property        | Hypothesis Pattern        |
| ----------------------- | ------------------------ | ------------------------- |
| Parsers                 | `parse(format(x)) == x`  | `@given(st.text())`       |
| Serialization           | `decode(encode(x)) == x` | `@given(valid_objects())` |
| Mathematical operations | Algebraic properties     | `@given(st.integers())`   |
| Complex algorithms      | Invariant preservation   | `@given(valid_inputs())`  |

**5.1 Identify Applicable Code Types**

```bash
# Find parsers and serializers
grep -rn "def parse\|def encode\|def decode\|def serialize\|def deserialize" {src_dir}

# Check if tests have property-based coverage
grep -rn "@given\|from hypothesis" {test_dir}
```

**5.2 Evaluate Coverage**

For each identified parser/serializer/math operation:

| Found                                      | Verdict    |
| ------------------------------------------ | ---------- |
| `@given` decorator with roundtrip property | PASS       |
| Only example-based tests                   | **REJECT** |
| No tests at all                            | **REJECT** |

**Example rejection:**

```python
# ❌ REJECT: Parser with only example-based tests
def test_parse_json_simple() -> None:
    result = parse('{"key": "value"}')
    assert result == {"key": "value"}


# Missing: @given(st.text()) + roundtrip property
```

**5.3 Verify Property Quality**

Property tests must test meaningful properties, not just "doesn't crash":

```python
# ❌ REJECT: Trivial property (only tests "doesn't crash")
@given(st.text())
def test_parse_doesnt_crash(text: str) -> None:
    try:
        parse(text)
    except ParseError:
        pass  # Expected for invalid input


# ✅ ACCEPT: Meaningful roundtrip property
@given(valid_json_values())
def test_roundtrip(value: JsonValue) -> None:
    assert parse(format(value)) == value
```

**GATE 5**: Before proceeding to Phase 6, verify:

- [ ] Identified all parsers, serializers, math operations, complex algorithms in code under test
- [ ] Ran grep for `@given` patterns in test files
- [ ] Each applicable code type has property-based tests with meaningful properties

If any check fails, STOP and REJECT with detailed findings citing `/standardizing-python-testing`.

</phase>

<phase name="python_test_quality">
Verify tests follow Python testing patterns per `/standardizing-python-testing`.

**6.1 Type Annotations**

```bash
# Find test functions missing return type
grep -rn "def test_" {test_dir} | grep -v "-> None"
```

**All test functions MUST have `-> None` return type annotation.**

**6.2 No Mocking**

```bash
# Find mocking patterns
grep -rn "@patch\|Mock()\|MagicMock\|mocker\." {test_dir}
```

**Any mocking = REJECT.** Use dependency injection instead.

**6.3 Magic Values**

```bash
# Find assertions with magic numbers (PLR2004)
grep -rn "assert.*==" {test_dir} | grep -E "[0-9]+"
```

**Magic values in assertions should use named constants.**

**6.4 Test Organization**

- [ ] Test class/function names describe the scenario
- [ ] Assertions verify outcomes, not implementation
- [ ] Fixtures clean up after themselves
- [ ] No hardcoded paths or environment-specific values

**GATE 6 (FINAL)**: Before issuing verdict, verify:

- [ ] All test functions have `-> None` return type
- [ ] No mocking patterns found
- [ ] Magic values use named constants (or are self-documenting)
- [ ] Test organization checklist passes

If all gates passed (foundational 1–4 + Python 5–6), issue APPROVED. Otherwise, REJECT with detailed findings.

</phase>

</python_phases>

<concrete_examples>
**Example 1: APPROVED verdict**

Reviewing `spx/01-uart/03-transmitter.story/`

Phase 1 checks (from /reviewing-tests):

```bash
$ grep -A 5 "^### Scenarios" transmitter.story.md
### Scenarios

- Given a UartTx configured for 8N1 at 115200 baud, when byte 0x55 is written, then TX line outputs start bit, 8 data bits (LSB first), and stop bit ([test](tests/test_uart_tx_unit.py))

$ ls -la tests/test_uart_tx_unit.py
-rw-r--r-- 1 user group 2847 Jan 15 10:23 tests/test_uart_tx_unit.py
✓ File exists, Level 1 matches _unit.py suffix
```

Phase 2 checks (from /reviewing-tests, using Python grep patterns):

```bash
$ grep -rn "pytest.mark.skipif" tests/
(no results)
✓ No silent skips

$ grep -rn "@patch\|Mock()\|MagicMock" tests/
(no results)
✓ No mocking
```

Phase 6 checks (Python-specific):

```bash
$ grep -rn "def test_" tests/ | grep -v "-> None"
(no results)
✓ All test functions have -> None
```

**Verdict: APPROVED** - All assertions have genuine evidentiary coverage at appropriate levels.

---

**Example 2: REJECT verdict**

Reviewing `spx/02-hdl/08-verilog-gen.story/`

Phase 2.2 finds silent skip:

```bash
$ grep -rn "pytest.mark.skipif" tests/
tests/test_verilog_gen.unit.py:15:@pytest.mark.skipif(not verilator_available(), reason="Verilator not available")
```

**Verdict: REJECT**

| # | Category    | Location                    | Issue                         | Required Fix                                     |
| - | ----------- | --------------------------- | ----------------------------- | ------------------------------------------------ |
| 1 | Silent Skip | test_verilog_gen.unit.py:15 | skipif on required dependency | Change to pytest.fail() if verilator unavailable |

**How Tests Could Pass While Assertion Fails:**

CI environment doesn't have Verilator installed. Test is silently skipped. CI goes green. The assertion "generates lint-clean Verilog" has zero verification. Users deploy code that produces invalid Verilog.

</concrete_examples>

<rejection_triggers>
Quick reference — includes both foundational triggers (from `/reviewing-tests`) and Python-specific triggers:

| Category            | Trigger                                                                      | Verdict | Source           |
| ------------------- | ---------------------------------------------------------------------------- | ------- | ---------------- |
| **Spec Structure**  | Code examples in spec                                                        | REJECT  | /reviewing-tests |
| **Spec Structure**  | Assertion type doesn't match test strategy (Property without `@given`, etc.) | REJECT  | /reviewing-tests |
| **Spec Structure**  | Missing or broken test file links (inline or table)                          | REJECT  | /reviewing-tests |
| **Spec Structure**  | Language about "pending" specs                                               | REJECT  | /reviewing-tests |
| **Spec Structure**  | Temporal language ("currently", "the existing", file references)             | REJECT  | /reviewing-tests |
| **Level**           | Assertion tested at wrong level                                              | REJECT  | /reviewing-tests |
| **Dependencies**    | `skipif` on required dependency                                              | REJECT  | /reviewing-tests |
| **Dependencies**    | Harness referenced but missing                                               | REJECT  | /reviewing-tests |
| **Decision Record** | Test violates ADR/PDR constraint                                             | REJECT  | /reviewing-tests |
| **Evidentiary**     | Test can pass with broken impl                                               | REJECT  | /reviewing-tests |
| **Property-Based**  | Parser without `@given` roundtrip test                                       | REJECT  | Python Phase 5   |
| **Property-Based**  | Serializer without `@given` roundtrip test                                   | REJECT  | Python Phase 5   |
| **Property-Based**  | Math operation without property tests                                        | REJECT  | Python Phase 5   |
| **Python**          | Missing `-> None` on test                                                    | REJECT  | Python Phase 6   |
| **Python**          | Mocking (`@patch`, `Mock()`)                                                 | REJECT  | Python Phase 6   |

</rejection_triggers>

<success_criteria>
Task is complete when:

- [ ] Verdict is APPROVED or REJECT (no middle ground)
- [ ] All 4 foundational phases from `/reviewing-tests` executed
- [ ] Both Python-specific phases (5–6) executed
- [ ] Property-based test coverage verified for parsers/serializers/math/algorithms
- [ ] Each rejection reason has file:line location
- [ ] Evidentiary gap explained (how tests could pass while assertion fails)
- [ ] Output follows format from `/reviewing-tests` (APPROVED or REJECT template)

</success_criteria>
