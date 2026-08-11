# Test Data Ownership

PROVIDES ownership rules for Python test values, generators, harnesses, pytest fixture callables, and inert fixture files
SO THAT Python tests
CAN distinguish source contracts from generated input domains and avoid hiding literals in test-infrastructure modules

## Assertions

### Compliance

- ALWAYS: Python test-data-ownership specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the case-provenance, predicate-ownership, oracle-independence, value-ownership, generator, fixture, and semantic-binding seam rules and declare only the Python delta below ([audit])
- ALWAYS: Python variable input domains come from Hypothesis strategies or deterministic generator functions; Python source-owned values come from registries, enums, constructors, typed factories, schemas, or dataclasses; pytest fixture callables that manage resources, dependencies, setup, teardown, or cleanup are harness entrypoints under `product_testing/harnesses/` imported by `conftest.py` for discovery, and inert fixtures live under `product_testing/fixtures/` ([audit])
- NEVER: a Python generator whose only behavior is `st.just(...)`, a singleton `st.sampled_from(...)`, or a constant-returning function for a source-owned singleton, or a Python constant bag named `TEST_FIXTURES` / `SAMPLE_PATHS` / `TYPICAL` / `EDGES` or a hand-extended `parametrize` case row standing in for source-owned values ([audit])
- ALWAYS: the case sources with no Python mechanism above — the spec scenario, the external conformance oracle, and the governing compliance rule — reach the test as literals in its body, so a Hypothesis strategy, a registry, or a fixture path never stands in for one, and a `parametrize` domain presents whichever source applies rather than being a source itself ([audit])
