# Source Testability

PROVIDES the source-design stance for Python test writing
SO THAT Python test authors and auditors
CAN require architecture changes before accepting weak, literal-bound, or mock-bound evidence

## Assertions

### Compliance

- ALWAYS: Python source-testability specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the source-contracts-first and controlled-collaborator seam rules and declare only the Python source-design delta below ([review])
- ALWAYS: source modules expose observable contracts through pure functions, typed dependency parameters, protocols, enums, schemas, dataclasses, source-owned constructors, or exported registries when tests need those contracts — behavior becomes testable through the production API ([review])
- ALWAYS: command and script entrypoints remain thin boundaries around imported orchestrators or domain modules — tests verify parsing and dispatch at the boundary while deeper behavior is tested in reusable code ([review])
- ALWAYS: side effects are represented by typed protocols, context managers, or injected collaborators when the assertion concerns behavior across process, filesystem, clock, network, database, or service boundaries — evidence stays coupled without framework replacement mocks ([review])
- ALWAYS: controlled implementations and recording collaborators implement the same Protocol boundary as production, preserve behavior-relevant state, and expose observations while the linked test owns every predicate and assertion call ([review])
