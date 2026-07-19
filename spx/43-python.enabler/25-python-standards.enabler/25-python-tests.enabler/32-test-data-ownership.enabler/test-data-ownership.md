# Test Data Ownership

PROVIDES ownership rules for Python test values, generators, harnesses, pytest fixture callables, and inert fixture files
SO THAT Python tests
CAN distinguish source contracts from generated input domains and avoid hiding literals in test-infrastructure modules

## Assertions

### Compliance

- ALWAYS: every test case — input and expected output — derives from a source independent of the test author's invention: the spec assertion text (scenarios), a finite source-owned enumeration (mappings), a generator over a domain (properties), an external oracle (conformance), the decision record being enforced (compliance), or an inert fixture file. The provenance of every case is auditable to a source outside the author's head ([review])
- ALWAYS: values that the source imports or should import come from the runtime, framework, protocol package, or production module that owns them — tests do not define local stand-ins for source vocabulary ([review])
- ALWAYS: values that the code under test owns are exposed by source-owned registries, enums, constructors, typed factories, schemas, dataclasses, or structured metadata — tests consume source contracts instead of duplicating them ([review])
- ALWAYS: executed test files may bind convenience aliases derived solely from imported source contracts, generators, harnesses, or fixture-path providers when the binding introduces no literal, number, vocabulary, case data, expected result, configuration, or independent policy ([review])
- ALWAYS: executed test functions and callbacks own every behavioral predicate and assertion API call; imported harnesses and recording collaborators expose observations rather than verdicts ([eval](../../../../21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership/eval.toml))
- ALWAYS: values that only the test needs are generated when they represent a variable input domain such as paths, names, identifiers, option sets, file contents, encodings, counts, product shapes, or environment names — generated values expand the exercised space ([review])
- ALWAYS: expected outputs for generated inputs are derived from the input, an independent oracle, or a source outside the module under test — tests do not copy expected data from the same implementation they verify ([review])
- ALWAYS: generators vary, compose, shrink, or explore meaningful alternatives through Hypothesis strategies or deterministic generator functions with more than one meaningful outcome — the generator abstraction carries evidence value beyond naming a constant ([review])
- ALWAYS: harnesses manage setup, teardown, cleanup, dependency checks, and access to external resources such as filesystems, subprocesses, browsers, APIs, Docker, product binaries, local services, or pytest discovery entrypoints — harnesses do not own arbitrary test data or replace the behavior an assertion claims to verify ([review])
- ALWAYS: pytest fixture callables that manage resources, dependencies, setup, teardown, or cleanup are harness entrypoints under `product_testing/harnesses/`; they may be imported by `conftest.py` for discovery without moving fixture body code into `tests/` ([review])
- ALWAYS: fixture files under `product_testing/fixtures/` contain real-world payloads whose complete shape matters to the behavior under test — fixtures are inert data samples, not a hiding place for isolated strings or numbers ([review])
- ALWAYS: executed tests access inert fixtures only by reading files, copying files into temp products, or passing fixture paths to the code or program under test — fixture contents remain inputs rather than executable test dependencies ([review])
- NEVER: import fixture files as Python modules, import from fixture-data directories, or consume fixture exports from executed Python tests — fixtures are inert file inputs ([review])
- NEVER: use a hand-picked test case based on the author's understanding of what would exercise the code — the author wrote or read the implementation, so the invention encodes the same model the code embodies, and every future run confirms that shared model rather than the spec. Concrete forms include hand-named TEST_FIXTURES / SAMPLE_PATHS / TYPICAL / EDGES bags, single-value module-scope constants, hand-written JSON keys, hand-copied artifact field names, and hand-extended parametrize case rows — the defect is shared, the form varies ([review])
- NEVER: create a generator whose only behavior is `st.just(...)`, a singleton `st.sampled_from(...)`, or a constant-returning function for a source-owned singleton shape — the owning source module provides the constructor, registry, enum, or schema ([review])
- NEVER: derive an expected output through the implementation table, algorithm, parser, or branch logic that produces the actual output — the expected output comes from an independent oracle ([eval](../../../../21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/evals/full-chain-ownership/eval.toml))
