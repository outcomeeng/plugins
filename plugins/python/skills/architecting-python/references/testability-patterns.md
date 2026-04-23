# Testability Patterns

Testability is an architectural concern. Design code so that testing is natural, not an afterthought.

## Core Principle

> **Ask first: "When would we need a test?" Then: "What kind of test?"**

Testing is not about coverage metrics. It's about answering specific questions at specific times.

---

## When Would We Need a Test?

Different situations call for different tests. Start by understanding the situation.

### Situation 1: Debugging During Development

**When**: You're implementing a function and need to verify it works.

**What you need**: A test with a KNOWN input and EXPECTED output that you can step through in a debugger.

**Example**:

```python
def test_parse_user_basic() -> None:
    """Debugging: Can I step through parse_user with a known input?"""
    # Known input - I can set a breakpoint and inspect every step
    input_data = {"name": "John Doe", "email": "john@example.com"}

    result = parse_user(input_data)

    assert result.name == "John Doe"
    assert result.email == "john@example.com"
```

**Key property**: You can set a breakpoint, see the exact input, step through, and understand what's happening.

---

### Situation 2: Preventing Known Bugs

**When**: You fixed a bug and want to ensure it never comes back.

**What you need**: A regression test that captures the exact scenario that caused the bug.

**Example**:

```python
def test_parse_user_handles_unicode_name() -> None:
    """Regression: Bug #42 - Unicode names were truncated."""
    # The exact input that caused the bug
    input_data = {"name": "José García", "email": "jose@example.com"}

    result = parse_user(input_data)

    # The assertion that would have caught the bug
    assert result.name == "José García"  # Not "Jos"
```

**Key property**: Documents WHY this test exists. Future developers understand the bug it prevents.

---

### Situation 3: Documenting Expected Behavior

**When**: You want to document what the system SHOULD do (golden/known-good tests).

**What you need**: Tests that serve as executable documentation of correct behavior.

**Example**:

```python
class TestUserValidation:
    """Documents: What inputs are valid/invalid for user creation?"""

    def test_valid_email_accepted(self) -> None:
        """Valid: Standard email format."""
        assert is_valid_email("user@example.com") is True

    def test_invalid_email_missing_at_rejected(self) -> None:
        """Invalid: Email must contain @."""
        assert is_valid_email("userexample.com") is False

    def test_invalid_email_missing_domain_rejected(self) -> None:
        """Invalid: Email must have domain."""
        assert is_valid_email("user@") is False
```

**Key property**: Reading these tests tells you exactly what's valid and invalid.

---

### Situation 4: Exploring Edge Cases

**When**: You've covered the obvious cases but want confidence about weird inputs.

**What you need**: Property-based tests that explore the input space automatically.

**Example**:

```python
from hypothesis import given, strategies as st


@given(st.text())
def test_parse_user_never_crashes_on_any_name(name: str) -> None:
    """Confidence: Does parse_user handle ANY string as a name?"""
    try:
        result = parse_user({"name": name, "email": "test@test.com"})
        assert isinstance(result.name, str)
    except ValidationError:
        pass  # Rejecting invalid input is fine
```

**Key property**: Explores inputs you didn't think of. Finds edge cases automatically.

---

### Situation 5: Proving `l2` or `l3` Behavior

**When**: You need real local dependencies (`l2`) or remote/credentialed dependencies (`l3`) to prove the assertion.

**What you need**: Scenario or conformance tests that exercise real interactions.

**Example**:

```python
def test_user_service_creates_and_retrieves_user(
    db_connection: Connection,
) -> None:
    """Scenario: Does the full flow work with a real database?"""
    repo = PostgresUserRepository(db_connection)
    service = UserService(repo)

    # Create
    user = service.create_user("John Doe", "john@example.com")

    # Retrieve
    retrieved = service.get_user(user.id)

    assert retrieved is not None
    assert retrieved.name == "John Doe"
```

**Key property**: Uses real components through a harness instead of replacing the dependency under test.

---

## Test Type Selection Guide

Given a situation, select the appropriate test type.

| Situation                    | Evidence mode               | Level cue                             |
| ---------------------------- | --------------------------- | ------------------------------------- |
| Debugging during development | `mapping` or `scenario`     | Usually `l1`                          |
| Preventing known bugs        | `scenario` or `compliance`  | Lowest level that proves the failure  |
| Documenting behavior         | `scenario`                  | Lowest level that proves the workflow |
| Exploring edge cases         | `property`                  | Usually `l1`                          |
| Real local dependency proof  | `scenario` or `conformance` | `l2`                                  |
| Remote service proof         | `scenario` or `conformance` | `l3`                                  |

---

## Development Progression

Tests evolve as code matures. Follow this progression:

### Phase 1: Debuggable Named Cases (Development)

Start with 1-2 simple tests you can step through:

```python
def test_calculate_total_single_item() -> None:
    """Development: Basic case I can debug."""
    items = [OrderLine(product_id=1, quantity=1, price=Money(1000, "USD"))]

    total = calculate_total(items)

    assert total == Money(1000, "USD")
```

**Purpose**: Get immediate feedback. See if basic logic works.

---

### Phase 2: Edge Cases (Hardening)

Add tests for boundaries and special cases:

```python
def test_calculate_total_empty_list() -> None:
    """Edge: What happens with no items?"""
    items: list[OrderLine] = []

    total = calculate_total(items)

    assert total == Money(0, "USD")


def test_calculate_total_large_quantities() -> None:
    """Edge: Large quantities shouldn't overflow."""
    items = [OrderLine(product_id=1, quantity=1_000_000, price=Money(100, "USD"))]

    total = calculate_total(items)

    assert total == Money(100_000_000, "USD")
```

**Purpose**: Ensure robustness at boundaries.

---

### Phase 3: Regression Tests (Bug Fixes)

When bugs are found, add tests that would have caught them:

```python
def test_calculate_total_mixed_currencies_raises() -> None:
    """Regression: Bug #17 - Mixed currencies were silently summed."""
    items = [
        OrderLine(product_id=1, quantity=1, price=Money(100, "USD")),
        OrderLine(product_id=2, quantity=1, price=Money(100, "EUR")),
    ]

    with pytest.raises(CurrencyMismatchError):
        calculate_total(items)
```

**Purpose**: Prevent bugs from recurring.

---

### Phase 4: Property-Based Tests (Confidence)

Add property tests to explore the input space:

```python
from hypothesis import given, strategies as st


@given(
    st.lists(
        st.builds(
            OrderLine,
            product_id=st.integers(min_value=1),
            quantity=st.integers(min_value=0, max_value=1000),
            price=st.builds(
                Money, amount=st.integers(min_value=0), currency=st.just("USD")
            ),
        )
    )
)
def test_calculate_total_always_non_negative(items: list[OrderLine]) -> None:
    """Property: Total is always non-negative for valid inputs."""
    total = calculate_total(items)

    assert total.amount >= 0
```

**Purpose**: Find edge cases you didn't think of.

---

## Designing for Testability

Architecture decisions affect testability. Make these decisions in ADRs.

### 1. Dependency Injection Enables Mocking

```python
# TESTABLE - Dependencies injected
class UserService:
    def __init__(self, repo: UserRepository, notifier: Notifier) -> None:
        self._repo = repo
        self._notifier = notifier


# In tests:
def test_user_service_sends_notification() -> None:
    mock_repo = MockUserRepository()
    mock_notifier = MockNotifier()
    service = UserService(mock_repo, mock_notifier)

    service.create_user("John", "john@example.com")

    assert mock_notifier.was_called_with("john@example.com")
```

```python
# NOT TESTABLE - Hidden dependencies
class UserService:
    def __init__(self) -> None:
        self._repo = PostgresUserRepository()  # Can't mock!
        self._notifier = SmtpNotifier()  # Can't mock!
```

---

### 2. Pure Functions Are Easiest to Test

```python
# EASY TO TEST - Pure function
def calculate_discount(price: Money, discount_percent: int) -> Money:
    """Pure: Same input always gives same output."""
    discount_amount = price.amount * discount_percent // 100
    return Money(price.amount - discount_amount, price.currency)


# Test: No setup needed
def test_calculate_discount() -> None:
    result = calculate_discount(Money(1000, "USD"), 10)
    assert result == Money(900, "USD")
```

```python
# HARD TO TEST - Impure function
def calculate_discount_and_log(price: Money, discount_percent: int) -> Money:
    """Impure: Has side effects (logging, time)."""
    logger.info(f"Calculating discount at {datetime.now()}")  # Side effect!
    discount_amount = price.amount * discount_percent // 100
    return Money(price.amount - discount_amount, price.currency)
```

---

### 3. Boundaries Separated from Logic

```python
# TESTABLE - Boundaries separated
def parse_config_file(path: Path) -> dict:
    """Boundary: Reads file (impure)."""
    return json.loads(path.read_text())


def validate_config(data: dict) -> AppConfig:
    """Logic: Validates config (pure)."""
    return AppConfig(**data)


def load_config(path: Path) -> AppConfig:
    """Composition: Combines boundary and logic."""
    data = parse_config_file(path)
    return validate_config(data)


# Test the logic without files:
def test_validate_config() -> None:
    data = {"api_key": "test", "debug": True}
    config = validate_config(data)
    assert config.debug is True
```

---

### 4. Protocols Enable Test Doubles

```python
class Clock(Protocol):
    """Protocol: Anything with a now() method."""

    def now(self) -> datetime: ...


class RealClock:
    """Production: Uses system time."""

    def now(self) -> datetime:
        return datetime.now()


class FakeClock:
    """Testing: Returns controlled time."""

    def __init__(self, fixed_time: datetime) -> None:
        self._time = fixed_time

    def now(self) -> datetime:
        return self._time


# Function accepts any Clock:
def create_timestamp(clock: Clock) -> str:
    return clock.now().isoformat()


# Test with controlled time:
def test_create_timestamp() -> None:
    fake_clock = FakeClock(datetime(2024, 1, 1, 12, 0, 0))
    result = create_timestamp(fake_clock)
    assert result == "2024-01-01T12:00:00"
```

---

## ADR Compliance Rules for Testability

ADRs express testability through Compliance rules, not a separate Testing Strategy section:

```markdown
## Compliance

### MUST

- Pure pricing rules live in functions that accept typed values and return typed results -- enables `l1` `mapping` and `property` evidence ([review])
- Order persistence accepts a repository Protocol -- enables `l2` scenario evidence with the real database harness ([review])
- Time-dependent behavior accepts a Clock Protocol -- enables deterministic `l1` evidence without patching globals ([review])

### NEVER

- `unittest.mock.patch` replaces repository, payment, or clock dependencies ([review])
- Invariant: total is always sum of line prices
```

---

## Key Principles

1. **Situation first**: Ask "when would we need this test?" before "what kind of test?"

2. **Debuggability matters**: Named cases with known inputs are debuggable

3. **Progression is natural**: Simple → edge cases → regression → property-based

4. **Design enables testing**: DI, pure functions, protocols, separated boundaries

5. **ADRs specify strategy**: Testability is an architectural concern
