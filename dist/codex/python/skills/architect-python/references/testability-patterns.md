# Testability Patterns

Testability is an architectural concern. Design code so that testing is natural, not an afterthought.

## Contents

- [Core Principle](#core-principle)
- [When Would We Need a Test?](#when-would-we-need-a-test)
- [Test Type Selection Guide](#test-type-selection-guide)
- [Development Progression](#development-progression)
- [Designing for Testability](#designing-for-testability)
- [ADR Verification Rules for Testability](#adr-verification-rules-for-testability)
- [Invariants](#invariants)
- [Verification](#verification)
- [Key Principles](#key-principles)

## Core Principle

> **Ask first: "When would we need a test?" Then: "What kind of test?"**

Testing is not about coverage metrics. It's about answering specific questions at specific times.

---

## When Would We Need a Test?

Different situations call for different tests. Start by understanding the situation.

### Situation 1: Debugging During Development

**When**: implementing a function and verifying it works.

**What's needed**: A test with a KNOWN input and EXPECTED output, steppable in a debugger.

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

**Key property**: A breakpoint can be set to see the exact input, step through, and understand what's happening.

---

### Situation 2: Preventing Known Bugs

**When**: a bug is fixed and must never come back.

**What's needed**: A regression test that captures the exact scenario that caused the bug.

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

**When**: documenting what the system SHOULD do (golden/known-good tests).

**What's needed**: Tests that serve as executable documentation of correct behavior.

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

**Key property**: Reading these tests shows exactly what's valid and invalid.

---

### Situation 4: Enabling Open-Domain Property Evidence

**When**: the spec asserts a falsifiable invariant over an open input space.

**What's needed**: Architecture that exposes a pure or observable function, a `product_testing/generators/` strategy that varies and shrinks the valid domain, and a `product_testing/harnesses/` property harness that owns Hypothesis settings, seeds, replay, and diagnostics. The linked test owns the invariant predicate.

**ADR constraint example**:

```markdown
### Audit

- ALWAYS: user payload normalization is a pure function whose output satisfies the source-owned canonical-form predicate for every valid generated payload ([audit])
- ALWAYS: property-run settings, seeds, replay, and failure diagnostics live in the property harness; executed assertion files own no Hypothesis policy ([audit])
```

**Key property**: The architecture makes a source-coupled invariant observable and leaves generation policy outside the assertion file.

---

### Situation 5: Enabling Real-Dependency Evidence

**When**: the assertion requires a real local, remote, shared, or credentialed dependency.

**What's needed**: Scenario or conformance tests that exercise real interactions.

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

## Architectural Testability Guide

ADRs establish constraints that make evidence possible. `/test` selects assertion type and execution level from the spec assertion, operational environment, and those constraints.

| Evidence need                   | ADR constraint                                                                                     |
| ------------------------------- | -------------------------------------------------------------------------------------------------- |
| Deterministic business rules    | Pure typed functions with source-owned inputs and observable outputs                               |
| Known failure prevention        | Explicit error contracts and dependency boundaries that can produce the real failure               |
| Open-domain invariants          | Pure or observable subjects plus generator and property-harness boundaries                         |
| Real local dependency behavior  | Protocol-typed dependency injection with a real local implementation and lifecycle-owning harness  |
| Remote or credentialed behavior | Safe, observable production boundary with credentials and mutation authorization outside test code |

---

## Development Progression

Tests evolve as code matures. Follow this progression:

### Phase 1: Debuggable Named Cases (Development)

Start with 1-2 simple tests that can be stepped through:

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

Prepare architecture for property evidence without placing generation policy in the ADR or assertion file:

```markdown
### Audit

- ALWAYS: total calculation is a pure typed function over source-owned money and order-line contracts ([audit])
- ALWAYS: the order-line generator varies and shrinks valid quantities, prices, currencies, and list shapes from source-owned constraints ([audit])
- ALWAYS: the property harness owns Hypothesis settings, seed selection, replay, and failure diagnostics ([audit])
```

`/test` selects property evidence from the assertion's open-domain quantifier and owns the linked invariant predicate.

---

## Designing for Testability

Architecture decisions affect testability. Make these decisions in ADRs.

### 1. Dependency Injection Enables Controlled Implementations

```python
# TESTABLE - Dependencies injected
class UserService:
    def __init__(self, repo: UserRepository, notifier: Notifier) -> None:
        self._repo = repo
        self._notifier = notifier


# In tests, use a real local repository and a recording collaborator for the
# notification safety boundary. The linked test owns every predicate.
def test_user_service_sends_notification() -> None:
    repo = SqliteUserRepository.open_memory()
    notifier = RecordingNotifier()
    service = UserService(repo, notifier)

    user = service.create_user("John", "john@example.com")

    assert repo.get(user.id) == user
    assert notifier.recipients == [user.email]
```

```python
# NOT TESTABLE - Hidden dependencies
class UserService:
    def __init__(self) -> None:
        self._repo = PostgresUserRepository()  # Hidden production dependency
        self._notifier = SmtpNotifier()  # Hidden production dependency
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

### 4. Protocols Enable Controlled Implementations

```python
class Clock(Protocol):
    """Protocol: Anything with a now() method."""

    def now(self) -> datetime: ...


class RealClock:
    """Production: Uses system time."""

    def now(self) -> datetime:
        return datetime.now()


class ControlledClock:
    """Controlled implementation for the time/concurrency exception."""

    def __init__(self, fixed_time: datetime) -> None:
        self._time = fixed_time

    def now(self) -> datetime:
        return self._time


# Function accepts any Clock:
def create_timestamp(clock: Clock) -> str:
    return clock.now().isoformat()


# Test with controlled time only after /test selects the time exception:
def test_create_timestamp() -> None:
    controlled_clock = ControlledClock(datetime(2024, 1, 1, 12, 0, 0))
    result = create_timestamp(controlled_clock)
    assert result == "2024-01-01T12:00:00"
```

---

## ADR Verification Rules for Testability

ADRs express testability through `### Audit` rules under `## Verification`, not a separate Testing Strategy section:

```markdown
## Invariants

- Total is always the sum of line prices

## Verification

### Audit

- ALWAYS: pure pricing rules live in functions that accept typed values and return typed results -- enables deterministic mapping or property evidence ([audit])
- ALWAYS: order persistence accepts a repository Protocol -- enables scenario evidence with the real database harness ([audit])
- ALWAYS: time-dependent behavior accepts a Clock Protocol -- enables deterministic evidence through a controlled clock when `/test` selects the time exception ([audit])
- NEVER: `unittest.mock.patch` replaces repository, payment, or clock dependencies ([audit])
```

---

## Key Principles

1. **Situation first**: Ask "when would we need this test?" before "what kind of test?"

2. **Debuggability matters**: Named cases with known inputs are debuggable

3. **Progression is natural**: Simple → edge cases → regression → property-based

4. **Design enables testing**: DI, pure functions, protocols, separated boundaries

5. **ADRs specify strategy**: Testability is an architectural concern
