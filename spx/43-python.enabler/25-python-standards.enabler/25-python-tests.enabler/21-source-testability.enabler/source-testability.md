# Source Testability

PROVIDES the source-design stance for Python test writing
SO THAT Python test authors and auditors
CAN require architecture changes before accepting weak, literal-bound, or mock-bound evidence

## Assertions

### Compliance

- ALWAYS: test writing for Python code under test treats source shape as improvable when its structure prevents maintainable evidence — the source contract changes before the test accepts a workaround ([review])
- ALWAYS: source modules expose observable contracts through pure functions, typed dependency parameters, protocols, enums, schemas, dataclasses, source-owned constructors, or exported registries when tests need those contracts — behavior becomes testable through the production API ([review])
- ALWAYS: command and script entrypoints remain thin boundaries around imported orchestrators or domain modules — tests verify parsing and dispatch at the boundary while deeper behavior is tested in reusable code ([review])
- ALWAYS: side effects are represented by typed protocols, context managers, or injected collaborators when the assertion concerns behavior across process, filesystem, clock, network, database, or service boundaries — evidence stays coupled without framework replacement mocks ([review])
- NEVER: accept a test whose only path to passing is copying source literals, pinning arbitrary example objects, mocking the behavior under test, or storing isolated strings in fixture files — those patterns expose missing source contracts ([review])
- NEVER: preserve hard-to-test source shape as a constraint on test design — the spec governs source design, and the implementation complies ([review])
