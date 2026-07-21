# Source Testability

PROVIDES the source-design stance for TypeScript test writing
SO THAT TypeScript test authors and auditors
CAN require architecture changes before accepting weak, literal-bound, or mock-bound evidence

## Assertions

### Compliance

- ALWAYS: test writing for TypeScript code under test treats source shape as improvable when its structure prevents maintainable evidence — the source contract changes before the test accepts a workaround ([audit])
- ALWAYS: source modules expose observable contracts through pure functions, typed dependency parameters, exported registries, or source-owned constructors when tests need those contracts — behavior becomes testable through the production API ([audit])
- ALWAYS: command and script entrypoints remain thin boundaries around imported orchestrators or domain modules — tests verify parsing and dispatch at the boundary while deeper behavior is tested in reusable code ([audit])
- ALWAYS: side effects are represented by typed interfaces or injected collaborators when the assertion concerns behavior across process, filesystem, clock, network, or service boundaries — evidence stays coupled without framework replacement mocks ([audit])
- ALWAYS: a controlled implementation or recording collaborator substituted for a production dependency conforms to that dependency's typed interface boundary and preserves behavior-relevant state, so the test exercises real behavior through the production contract rather than a stubbed replacement ([audit])
- NEVER: accept a test whose only path to passing is copying source literals, pinning arbitrary example objects, mocking the behavior under test, or storing isolated strings in fixture files — those patterns expose missing source contracts ([audit])
- NEVER: preserve hard-to-test source shape as a constraint on test design — the spec governs source design, and the implementation complies ([audit])
