# Type System Patterns

Python's type system, when used strictly, provides compile-time safety comparable to statically typed languages. These patterns are MANDATORY for high-assurance Python.

## Core Principle

> **Type annotations are not optional. They are architectural constraints.**

Every public function, every class attribute, every module-level variable must be typed. Mypy in strict mode is the verification tool.

---

## Modern Python Syntax (3.10+)

Use modern syntax. Old syntax is rejected.

### Union Types

```python
# GOOD - Modern syntax
def get_user(user_id: int) -> User | None: ...


# BAD - Old syntax
from typing import Optional


def get_user(user_id: int) -> Optional[User]: ...
```

### Generic Collections

```python
# GOOD - Lowercase builtins
def process_items(items: list[str]) -> dict[str, int]: ...


# BAD - typing module imports
from typing import List, Dict


def process_items(items: List[str]) -> Dict[str, int]: ...
```

### Type Aliases

```python
# GOOD - Type alias with explicit annotation
type UserId = int
type UserMap = dict[UserId, User]

# ACCEPTABLE - For Python 3.10-3.11
UserId = int
UserMap = dict[int, User]
```

---

## The `Any` Problem

`Any` is a type system escape hatch. It defeats the purpose of typing.

### When `Any` is Forbidden

```python
# FORBIDDEN - Lazy typing
def process(data: Any) -> Any: ...


# FORBIDDEN - Avoiding complex types
results: list[Any] = []
```

### When `Any` is Allowed (with ADR justification)

```python
# ALLOWED - Interfacing with untyped library (document in ADR)
def parse_legacy_config(config: Any) -> AppConfig:
    """Parse config from untyped legacy library.

    Note: 'config' is Any because legacy_lib has no type stubs.
    See [Type Safety Justification](54-type-safety-justification.adr.md) for details.
    """
    ...
```

**Rule**: Every use of `Any` must be justified in an ADR.

---

## Protocols for Structural Typing

Use Protocols to define interfaces without inheritance.

### Defining a Protocol

```python
from typing import Protocol


class Logger(Protocol):
    """Interface for logging implementations."""

    def info(self, message: str) -> None: ...
    def error(self, message: str, exc: Exception | None = None) -> None: ...
    def debug(self, message: str) -> None: ...
```

### Using Protocols

```python
def sync_files(
    source: Path,
    dest: Path,
    logger: Logger,  # Any object with info/error/debug methods
) -> SyncResult:
    logger.info(f"Syncing {source} to {dest}")
    ...
```

### Why Protocols?

- No inheritance coupling
- Works with any compatible object
- Enables easy mocking in tests
- Documents the interface explicitly

---

## TypeVar and Generics

Use generics for reusable, type-safe abstractions.

### Basic TypeVar

```python
from typing import TypeVar

T = TypeVar("T")


def first(items: list[T]) -> T | None:
    return items[0] if items else None
```

### Bounded TypeVar

```python
from typing import TypeVar


class Comparable(Protocol):
    def __lt__(self, other: Self) -> bool: ...


T = TypeVar("T", bound=Comparable)


def min_value(a: T, b: T) -> T:
    return a if a < b else b
```

### Generic Classes

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(Generic[T]):
    def get(self, id: int) -> T | None: ...
    def save(self, entity: T) -> None: ...
    def delete(self, entity: T) -> None: ...


class UserRepository(Repository[User]): ...
```

---

## TYPE_CHECKING for Import Cycles

Break import cycles without runtime overhead.

### The Pattern

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import User  # Only imported for type checking


class UserService:
    def get_user(self, user_id: int) -> "User":  # String annotation
        ...
```

### When to Use

- Breaking circular imports between modules
- Importing large modules only needed for type hints
- Importing from packages with heavy initialization

---

## Pydantic at Boundaries

Use Pydantic for data validation at system boundaries.

### System Boundaries

```
External Input  ──►  Pydantic Model  ──►  Domain Logic  ──►  Pydantic Model  ──►  External Output
     │                    │                    │                    │                   │
     │                    ▼                    │                    ▼                   │
     │              VALIDATION                 │              SERIALIZATION             │
     │                                         │                                        │
     └── API requests, CLI args, files ────────┴── Pure Python types ──────────────────┘
```

### Input Validation

```python
from pydantic import BaseModel, Field, field_validator


class SyncRequest(BaseModel):
    """Request to sync a dataset."""

    source: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    dry_run: bool = False

    @field_validator("source", "destination")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v.startswith("/") and ":" not in v:
            raise ValueError("Path must be absolute or remote (host:path)")
        return v
```

### Output Serialization

```python
class SyncResult(BaseModel):
    """Result of a sync operation."""

    files_copied: int
    bytes_transferred: int
    errors: list[str]

    model_config = {"frozen": True}  # Immutable
```

### Why Pydantic at Boundaries?

- Validates untrusted input automatically
- Generates clear error messages
- Serializes to JSON/dict for output
- Self-documenting schemas
- Keeps domain logic pure (no validation code)

---

## Type Narrowing

Use type guards and assertions to narrow types.

### isinstance Narrowing

```python
def process(value: str | int) -> str:
    if isinstance(value, str):
        return value.upper()  # Type narrowed to str
    return str(value)  # Type narrowed to int
```

### TypeGuard for Custom Checks

```python
from typing import TypeGuard


def is_valid_user(obj: object) -> TypeGuard[User]:
    return isinstance(obj, dict) and "id" in obj and "name" in obj


def process(obj: object) -> None:
    if is_valid_user(obj):
        print(obj["name"])  # Type narrowed to User
```

### assert_never for Exhaustiveness

```python
from typing import assert_never


def handle_status(status: Literal["pending", "active", "closed"]) -> str:
    match status:
        case "pending":
            return "Waiting"
        case "active":
            return "In progress"
        case "closed":
            return "Done"
        case _:
            assert_never(status)  # Compile error if case missed
```

---

## Dataclasses for Domain Objects

Use dataclasses for simple domain objects.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Snapshot:
    """A ZFS snapshot."""

    dataset: str
    name: str
    timestamp: datetime

    @property
    def full_name(self) -> str:
        return f"{self.dataset}@{self.name}"
```

### When to Use Dataclasses vs Pydantic

| Use Case                       | Choice                  |
| ------------------------------ | ----------------------- |
| System boundary (input/output) | Pydantic                |
| Internal domain object         | dataclass               |
| Needs validation               | Pydantic                |
| Needs serialization            | Pydantic                |
| Simple value object            | dataclass (frozen=True) |

---

## Mypy Configuration

Strict mode is mandatory. Configure in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
```

### Handling `# type: ignore`

Every `# type: ignore` must have an explanation:

```python
# GOOD - Explains why
result = legacy_function()  # type: ignore[no-untyped-call] - legacy_lib lacks stubs

# BAD - No explanation
result = legacy_function()  # type: ignore
```

**Rule**: `# type: ignore` without explanation is rejected by the Reviewer.

---

## Key Principles

1. **Modern syntax only**: `X | None`, `list[str]`, not `Optional[X]`, `List[str]`

2. **No `Any` without ADR**: Every use of `Any` must be justified

3. **Protocols for interfaces**: No inheritance for dependency injection

4. **Pydantic at boundaries**: Validate input, serialize output

5. **Strict Mypy**: All flags enabled, zero errors allowed
