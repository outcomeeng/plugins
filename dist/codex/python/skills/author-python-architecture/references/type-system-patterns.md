# Type System Patterns

Type annotations are architectural constraints. The ADR states which of the rules below govern the product it decides for.

## Contents

- [Annotation Rules](#annotation-rules)
- [The `Any` Rule](#the-any-rule)
- [Protocols for Interfaces](#protocols-for-interfaces)
- [Pydantic Versus Dataclass](#pydantic-versus-dataclass)
- [Strict Mypy](#strict-mypy)

## Annotation Rules

- Every public function, class attribute, and module-level variable is typed.
- Modern syntax only: `X | None`, `list[str]`, `dict[str, int]`; never `Optional[X]`, `List[str]`, or `Dict[str, int]`.
- Aliases use the `type` statement: `type UserId = int`.

## The `Any` Rule

Every use of `Any` is justified in an ADR that the code's docstring links by markdown link. The sanctioned case is an untyped third-party library with no stubs; lazy typing and avoiding a complex type are forbidden.

## Protocols for Interfaces

Dependency-injected interfaces are `Protocol` classes, not base classes. Protocols avoid inheritance coupling and admit real, controlled, and recording implementations alike.

## Pydantic Versus Dataclass

| Use case                       | Choice                  |
| ------------------------------ | ----------------------- |
| System boundary (input/output) | Pydantic                |
| Needs validation               | Pydantic                |
| Needs serialization            | Pydantic                |
| Internal domain object         | dataclass               |
| Simple value object            | dataclass (frozen=True) |

Pydantic validates untrusted input at the boundary so domain logic carries no validation code.

## Strict Mypy

Strict mode is mandatory, configured in `pyproject.toml`:

```toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
```

Every `# type: ignore` names its error code and carries an explanation, for example `# type: ignore[no-untyped-call] - legacy_lib lacks stubs`.
