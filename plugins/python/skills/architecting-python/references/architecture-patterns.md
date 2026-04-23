# Architecture Patterns

These patterns ensure Python code is maintainable, testable, and scalable.

## Core Principle

> **Separate what changes from what doesn't. Inject dependencies. Keep functions pure.**

---

## Domain-Driven Design (DDD)

Structure code around the business domain, not technical concerns.

### Building Blocks

| Concept          | Definition                    | Example                     |
| ---------------- | ----------------------------- | --------------------------- |
| **Entity**       | Has identity, mutable         | `User`, `Order`             |
| **Value Object** | No identity, immutable        | `Money`, `Address`          |
| **Aggregate**    | Cluster of entities with root | `Order` (with `OrderLines`) |
| **Repository**   | Persistence abstraction       | `UserRepository`            |
| **Service**      | Stateless domain logic        | `PaymentService`            |

### Entity

```python
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class User:
    """Entity: has identity (id), mutable state."""

    id: UUID = field(default_factory=uuid4)
    email: str = ""
    name: str = ""
    active: bool = True

    def deactivate(self) -> None:
        self.active = False
```

### Value Object

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """Value Object: no identity, immutable, equality by value."""

    amount: int  # Store as cents to avoid float issues
    currency: str

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
```

### Aggregate

```python
@dataclass
class Order:
    """Aggregate Root: controls access to OrderLines."""

    id: UUID
    customer_id: UUID
    lines: list[OrderLine] = field(default_factory=list)
    status: OrderStatus = OrderStatus.DRAFT

    def add_line(self, product_id: UUID, quantity: int, price: Money) -> None:
        if self.status != OrderStatus.DRAFT:
            raise InvalidOperationError("Cannot modify non-draft order")
        self.lines.append(OrderLine(product_id, quantity, price))

    def submit(self) -> None:
        if not self.lines:
            raise InvalidOperationError("Cannot submit empty order")
        self.status = OrderStatus.SUBMITTED
```

**Rule**: Only the Aggregate Root can modify its children. External code cannot directly modify `OrderLine`.

---

## Hexagonal Architecture (Ports & Adapters)

Isolate domain logic from external systems.

```
┌─────────────────────────────────────────────────────────────┐
│                        ADAPTERS                              │
│  CLI   │   REST API   │   Database   │   External APIs      │
└────────┼──────────────┼──────────────┼──────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                         PORTS                                │
│  UserInput   │   UserOutput   │   Repository   │   Gateway  │
└────────┬─────┴────────────────┴───────┬────────┴────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN CORE                             │
│  Entities   │   Value Objects   │   Services   │   Rules    │
└─────────────────────────────────────────────────────────────┘
```

### Ports (Interfaces)

```python
from typing import Protocol


class UserRepository(Protocol):
    """Port: defines what the domain needs from persistence."""

    def get(self, user_id: UUID) -> User | None: ...
    def save(self, user: User) -> None: ...
    def delete(self, user_id: UUID) -> None: ...


class NotificationGateway(Protocol):
    """Port: defines what the domain needs from notifications."""

    def send_email(self, to: str, subject: str, body: str) -> None: ...
```

### Adapters (Implementations)

```python
class PostgresUserRepository:
    """Adapter: implements UserRepository for Postgres."""

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get(self, user_id: UUID) -> User | None:
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = %s", (str(user_id),)
        ).fetchone()
        return User(**row) if row else None

    def save(self, user: User) -> None:
        self._conn.execute(
            "INSERT INTO users (id, email, name) VALUES (%s, %s, %s)",
            (str(user.id), user.email, user.name),
        )
```

### Domain Service

```python
class UserService:
    """Domain service: orchestrates domain logic."""

    def __init__(
        self,
        user_repo: UserRepository,
        notifications: NotificationGateway,
    ) -> None:
        self._users = user_repo
        self._notifications = notifications

    def register_user(self, email: str, name: str) -> User:
        user = User(email=email, name=name)
        self._users.save(user)
        self._notifications.send_email(email, "Welcome", f"Hello {name}!")
        return user
```

---

## Dependency Injection

Pass dependencies as parameters. Never import globals.

### The Pattern

```python
# GOOD - Dependencies as parameters
def sync_files(
    source: Path,
    dest: Path,
    logger: Logger,
    file_system: FileSystem,
    dry_run: bool = False,
) -> SyncResult:
    logger.info(f"Syncing {source} to {dest}")
    ...


# BAD - Hidden dependencies
def sync_files(source: Path, dest: Path) -> SyncResult:
    logger = logging.getLogger(__name__)  # Hidden
    config = load_config()  # Hidden
    ...
```

### Why DI Matters

1. **Testability**: Inject mocks for testing
2. **Flexibility**: Swap implementations without code changes
3. **Explicitness**: All dependencies visible in signature
4. **No globals**: No hidden state

### Composition Root

Wire dependencies at the application entry point:

```python
# main.py - Composition Root
def main() -> None:
    # Create adapters
    db = PostgresConnection(os.environ["DATABASE_URL"])
    user_repo = PostgresUserRepository(db)
    email_gateway = SmtpNotificationGateway(os.environ["SMTP_HOST"])
    logger = logging.getLogger("app")

    # Create service with injected dependencies
    user_service = UserService(user_repo, email_gateway)

    # Run application
    cli = UserCLI(user_service, logger)
    cli.run()
```

---

## Single Responsibility Principle

Each module/class has one reason to change.

### Module Structure

```
product/
├── domain/              # Business logic (changes for business reasons)
│   ├── entities.py
│   ├── services.py
│   └── exceptions.py
├── adapters/            # External integrations (changes for infra reasons)
│   ├── postgres.py
│   ├── smtp.py
│   └── cli.py
├── ports/               # Interfaces (changes when contracts change)
│   ├── repositories.py
│   └── gateways.py
└── main.py              # Composition root
```

### Class Responsibilities

```python
# GOOD - Single responsibility
class UserValidator:
    """Validates user data."""

    def validate(self, data: dict) -> list[str]: ...


class UserRepository:
    """Persists users."""

    def save(self, user: User) -> None: ...


class UserNotifier:
    """Sends user notifications."""

    def notify(self, user: User, message: str) -> None: ...


# BAD - Multiple responsibilities
class UserManager:
    """Does everything user-related."""  # Too broad

    def validate(self, data: dict) -> list[str]: ...
    def save(self, user: User) -> None: ...
    def notify(self, user: User, message: str) -> None: ...
    def generate_report(self) -> str: ...
```

---

## No Circular Imports

Circular imports indicate architectural problems.

### Detecting Cycles

```python
# If this fails with ImportError, you have a cycle
python -c "from mypackage import main"
```

### Breaking Cycles

**Strategy 1: Extract shared types**

```python
# BEFORE (cycle: a imports b, b imports a)
# a.py
from b import B


class A:
    def use_b(self, b: B) -> None: ...


# b.py
from a import A


class B:
    def use_a(self, a: A) -> None: ...


# AFTER (no cycle: both import from types)
# types.py
from typing import Protocol


class AProtocol(Protocol):
    def use_b(self, b: "BProtocol") -> None: ...


class BProtocol(Protocol):
    def use_a(self, a: AProtocol) -> None: ...
```

**Strategy 2: TYPE_CHECKING**

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from other_module import OtherClass


def process(item: "OtherClass") -> None: ...
```

**Strategy 3: Reorganize modules**

Often, cycles indicate that code should be in a different module.

---

## Pure Functions

Prefer pure functions for business logic.

### What is Pure?

A pure function:

- Returns the same output for the same input
- Has no side effects (no I/O, no mutation)

```python
# PURE - Same input always gives same output
def calculate_total(items: list[OrderLine]) -> Money:
    return Money(
        sum(line.price.amount * line.quantity for line in items),
        items[0].price.currency if items else "USD",
    )


# IMPURE - Has side effects (I/O)
def calculate_and_save_total(order: Order) -> Money:
    total = calculate_total(order.lines)
    database.save(order.id, total)  # Side effect
    return total
```

### Why Pure Functions?

1. **Easy to test**: No mocking needed
2. **Easy to reason about**: No hidden state
3. **Parallelizable**: No shared mutable state
4. **Cacheable**: Same input = same output

### Isolate Impurity

Push side effects to the edges:

```python
# Pure core
def process_order(order: Order) -> ProcessedOrder:
    validated = validate_order(order)  # Pure
    priced = calculate_prices(validated)  # Pure
    return finalize(priced)  # Pure


# Impure shell
def handle_order_request(request: Request) -> Response:
    order = parse_request(request)  # Impure (I/O)
    processed = process_order(order)  # Pure
    save_to_database(processed)  # Impure (I/O)
    send_confirmation_email(processed)  # Impure (I/O)
    return create_response(processed)  # Impure (I/O)
```

---

## Directory Structure

Standard Python project layout:

```
project/
├── pyproject.toml          # Project config, dependencies
├── product/
│   ├── __init__.py
│   ├── domain/         # Business logic
│   ├── adapters/       # External integrations
│   ├── ports/          # Interfaces
│   └── main.py         # Entry point
├── mypackage_testing/      # Test utilities (fixtures, harnesses) - INSTALLABLE
│   ├── __init__.py
│   ├── fixtures/           # Test data factories
│   └── harnesses/          # Test infrastructure (CLI harness, etc.)
└── spx/                    # Specs as durable map (Outcome Engineering framework)
    ├── CLAUDE.md           # Navigation and work item management
    └── NN-{slug}.enabler/
        └── NN-{slug}.outcome/
            └── tests/      # Co-located tests with evidence/level naming
                ├── test_foo.mapping.l1.py
                ├── test_bar.scenario.l2.py
                └── test_baz.conformance.l3.py
```

**Key**: Test utilities in `mypackage_testing/` are installed via `uv pip install -e ".[dev]"`. Co-located tests in `spx/.../tests/` import from `mypackage_testing.fixtures`. See `test-infrastructure-patterns.md`.

---

## Key Principles

1. **DDD for complex domains**: Entities, Value Objects, Aggregates

2. **Hexagonal for isolation**: Ports and Adapters separate domain from infrastructure

3. **DI for testability**: All dependencies passed as parameters

4. **SRP for maintainability**: One reason to change per module/class

5. **Pure functions for logic**: Push side effects to the edges
