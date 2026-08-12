# Source Testability

PROVIDES the source-design stance for Python test writing
SO THAT Python test authors and auditors
CAN require architecture changes before accepting weak, literal-bound, or mock-bound evidence

## Assertions

### Compliance

- ALWAYS: Python source-testability specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the source-design seam rules and declare only the Python delta: the observable contracts source modules expose are Python `Protocol` boundaries, typed dependency parameters, `@dataclass` and enum constructors, context managers, and exported registries; controlled implementations and injected collaborators conform to the same `Protocol` boundary as production ([audit])
- ALWAYS: the Python shapes that give a weak test a package path to import — a module-level example, a case sequence, a `@dataclass` of input-and-expected rows, an enum whose members name test scenarios, or a `for_testing` / `example` / `sample` / `build` classmethod — satisfy the source improvement the seam rules require only where a contract outside the test tree requires the symbol; `__all__` membership, a public name, and a type annotation establish none of that ([audit])
- ALWAYS: static importer analysis over Python source is a rebuttable signal, so an absent importer outside `spx/**/tests/` and `product_testing/` is rebutted by a packaging entry point, a plugin or `Protocol` implementation, an `importlib` or registry lookup, a framework-discovered attribute, a serialization schema, or the package's published surface ([audit])
