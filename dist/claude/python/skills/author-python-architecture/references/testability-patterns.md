# Testability Patterns

Testability is an architectural concern. ADRs establish constraints that make evidence possible; `/test` selects assertion type and execution level from the spec assertion, the operational environment, and those constraints.

## Contents

- [Constraint Guide](#constraint-guide)
- [Open-Domain Property Evidence](#open-domain-property-evidence)
- [Controlled Implementations](#controlled-implementations)
- [ADR Verification Rules](#adr-verification-rules)

## Constraint Guide

| Evidence need                   | ADR constraint                                                                                     |
| ------------------------------- | -------------------------------------------------------------------------------------------------- |
| Deterministic business rules    | Pure typed functions with source-owned inputs and observable outputs                               |
| Known failure prevention        | Explicit error contracts and dependency boundaries that can produce the real failure               |
| Open-domain invariants          | Pure or observable subjects plus generator and property-harness boundaries                         |
| Real local dependency behavior  | Protocol-typed dependency injection with a real local implementation and lifecycle-owning harness  |
| Remote or credentialed behavior | Safe, observable production boundary with credentials and mutation authorization outside test code |

## Open-Domain Property Evidence

When a spec asserts a falsifiable invariant over an open input space, the architecture exposes a pure or observable function, a `{product}_testing/generators/` strategy that varies and shrinks the valid domain, and a `{product}_testing/harnesses/` property harness that owns Hypothesis settings, seeds, replay, and diagnostics. The linked test owns the invariant predicate; the ADR never places generation policy in an assertion file.

```markdown
### Audit

- ALWAYS: total calculation is a pure typed function over source-owned money and order-line contracts ([audit])
- ALWAYS: the order-line generator varies and shrinks valid quantities, prices, currencies, and list shapes from source-owned constraints ([audit])
- ALWAYS: the property harness owns Hypothesis settings, seed selection, replay, and failure diagnostics ([audit])
```

## Controlled Implementations

Time and concurrency are the dependencies that admit a controlled implementation, and only after `/test` selects that exception. Every other collaborator is a real local implementation or a recording collaborator that preserves the behavior boundary.

```python
class Clock(Protocol):
    def now(self) -> datetime: ...


class ControlledClock:
    """Controlled implementation for the time exception."""

    def __init__(self, fixed_time: datetime) -> None:
        self._time = fixed_time

    def now(self) -> datetime:
        return self._time
```

## ADR Verification Rules

ADRs express testability as `### Audit` rules under `## Verification`, never as a separate Testing Strategy section:

```markdown
## Verification

### Audit

- ALWAYS: pure pricing rules live in functions that accept typed values and return typed results -- enables deterministic mapping or property evidence ([audit])
- ALWAYS: order persistence accepts a repository Protocol -- enables scenario evidence with the real database harness ([audit])
- ALWAYS: time-dependent behavior accepts a Clock Protocol -- enables deterministic evidence through a controlled clock when `/test` selects the time exception ([audit])
- NEVER: `unittest.mock.patch` replaces repository, payment, or clock dependencies ([audit])
```
