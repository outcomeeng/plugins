# Source Testability

PROVIDES the source-design stance for Python test writing
SO THAT Python test authors and auditors
CAN require architecture changes before accepting weak, literal-bound, or mock-bound evidence

## Assertions

### Compliance

- ALWAYS: Python source-testability specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the source-design seam rules and declare only the Python delta: the observable contracts source modules expose are Python `Protocol` boundaries, typed dependency parameters, `@dataclass` and enum constructors, context managers, and exported registries; controlled implementations and injected collaborators conform to the same `Protocol` boundary as production ([audit])
