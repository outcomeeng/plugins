# Source Testability

PROVIDES the source-design stance for Python test writing
SO THAT Python test authors and auditors
CAN require architecture changes before accepting weak, literal-bound, or mock-bound evidence

## Assertions

### Compliance

- ALWAYS: Python source-testability specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the source-design seam rules and declare only the Python delta: the observable contracts source modules expose are Python `Protocol` boundaries, typed dependency parameters, `@dataclass` and enum constructors, context managers, and exported registries; controlled implementations and injected collaborators conform to the same `Protocol` boundary as production ([audit])
- ALWAYS: the source improvement a weak Python test demands is a contract a production caller uses, so a module-level example, a case sequence, a `@dataclass` of input-and-expected rows, an enum whose members name test scenarios, or a `for_testing` / `example` / `sample` / `build` classmethod added to give a test a package path to import satisfies nothing — the Python discriminator for source laundering is that the symbol has no importer outside `spx/**/tests/` and `product_testing/`, and `__all__` membership, a public name, and a type annotation are all consistent with having none
