# Test Data Ownership

PROVIDES ownership rules for Python test values, generators, harnesses, pytest fixture callables, and inert fixture files
SO THAT Python tests
CAN distinguish source contracts from generated input domains and avoid hiding literals in test-infrastructure modules

## Assertions

### Compliance

- ALWAYS: Python test-data-ownership specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the case-provenance, predicate-ownership, oracle-independence, and semantic-binding seam rules and declare only the Python ownership delta below ([review])
- ALWAYS: values the source imports or owns come from the runtime, framework, protocol package, or production module through registries, enums, constructors, typed factories, schemas, dataclasses, or structured metadata — Python tests consume those source contracts instead of defining local stand-ins ([review])
- ALWAYS: variable Python input domains come from Hypothesis strategies or deterministic generator functions that vary, compose, shrink, or explore more than one meaningful outcome ([review])
- ALWAYS: pytest fixture callables that manage resources, dependencies, setup, teardown, or cleanup are harness entrypoints under `product_testing/harnesses/`; they may be imported by `conftest.py` for discovery without moving fixture body code into `tests/` ([review])
- ALWAYS: fixture files under `product_testing/fixtures/` contain real-world payloads whose complete shape matters to the behavior under test, read by path, copied into temp products, or passed to the code or program under test — never imported as Python modules or consumed as exports ([review])
- NEVER: executed Python test files declare variables or constants; every value or configuration choice those declarations would bind lives in spec-governed harnesses, generators, inert whole-payload fixtures, source contracts, or justified eval case data ([review])
- NEVER: use a hand-picked test case based on the author's understanding of what would exercise the code — the author wrote or read the implementation, so the invention encodes the same model the code embodies, and every future run confirms that shared model rather than the spec. Concrete Python forms include hand-named TEST_FIXTURES / SAMPLE_PATHS / TYPICAL / EDGES bags, single-value module-scope constants, hand-written JSON keys, hand-copied artifact field names, and hand-extended parametrize case rows ([review])
- NEVER: create a generator whose only behavior is `st.just(...)`, a singleton `st.sampled_from(...)`, or a constant-returning function for a source-owned singleton shape — the owning source module provides the constructor, registry, enum, or schema ([review])
