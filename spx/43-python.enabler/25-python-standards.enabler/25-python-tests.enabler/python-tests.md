# Python Tests

PROVIDES Python test standards for evidence type, execution level, testability, test data ownership, test-infrastructure auditing, and generator use
SO THAT Python testing and audit skills
CAN produce evidence that is coupled to source behavior, maintainable under source changes, and free of literal laundering

## Assertions

### Compliance

- ALWAYS: Python test guidance starts from the spec assertion and selected evidence type before choosing file names, runners, harnesses, generators, pytest fixtures, or examples — evidence shape follows the claim being proved ([review])
- ALWAYS: Python test-standard specs cite `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` for the language-neutral seam rules and declare only the Python delta below rather than restating them ([review])
- ALWAYS: source-owned protocol values and singleton shapes come from production modules through exported registries, constructors, enums, schemas, typed factories, or dataclasses — the Python source contracts tests import instead of recreating ([review])
- ALWAYS: Python test infrastructure realizes the governing PDR's home as `product_testing/` — `product_testing/harnesses/`, `product_testing/generators/`, `product_testing/fixtures/` — with variable input domains produced by Hypothesis strategies or deterministic generator functions that explore more than one meaningful value ([review])
- ALWAYS: pytest fixture callables that perform setup, teardown, cleanup, or dependency access are harness entrypoints under `product_testing/harnesses/`; `conftest.py` imports them explicitly only for pytest discovery ([review])
- NEVER: executed Python test files declare variables or constants; every value or configuration choice those declarations would bind lives in spec-governed harnesses, generators, inert whole-payload fixtures, source contracts, or justified eval case data ([review])
- NEVER: treat `st.just(...)`, `st.sampled_from(...)` with a single source-owned singleton, or a constant-returning factory as a generator domain — source-owned singleton construction belongs in the owning source module ([review])
