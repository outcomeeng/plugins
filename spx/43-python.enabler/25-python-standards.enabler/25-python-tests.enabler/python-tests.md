# Python Tests

PROVIDES Python test standards for evidence type, execution level, testability, test data ownership, test-infrastructure auditing, and generator use
SO THAT Python testing and audit skills
CAN produce evidence that is coupled to source behavior, maintainable under source changes, and free of literal laundering

## Assertions

### Compliance

- ALWAYS: Python test guidance starts from the spec assertion and selected evidence type before choosing file names, runners, harnesses, generators, pytest fixtures, or examples — evidence shape follows the claim being proved ([review])
- ALWAYS: tests for Python code under test treat source architecture as changeable when the code is not testable through its production contract — acceptable evidence often requires improving source contracts, extracting pure logic, or injecting side-effect dependencies before writing the test ([review])
- ALWAYS: source-owned protocol values and singleton shapes come from production modules through exported registries, constructors, enums, schemas, typed factories, or dataclasses — tests import ownership rather than recreating it ([review])
- ALWAYS: variable test input domains come from generators that vary, compose, shrink, or explore more than one meaningful value — generator APIs exist to expand evidence, not to hide constants ([review])
- ALWAYS: property-based Python tests run through spec-governed harnesses that own seed selection, run count, replay input, and failure diagnostics, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([review])
- ALWAYS: Python test infrastructure follows `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`: harnesses manage resource lifecycle and access to behavior, generators produce variable input domains, fixtures stay inert, and source-owned domain truth comes from source modules ([review])
- ALWAYS: fixture files are inert input artifacts read from disk, copied into temp products, or passed by path to code or programs under test — executed tests never import them as Python modules or consume their exports ([review])
- ALWAYS: pytest fixture callables that perform setup, teardown, cleanup, or dependency access are harness entrypoints and live under `<package>_testing/harnesses/`; `conftest.py` imports them explicitly only for pytest discovery ([review])
- ALWAYS: Python test audit opens imported test-infrastructure modules — generators, harnesses, inert fixture references, and `conftest.py` shims — before approving an assertion; laundering and severed coupling can live outside the test file ([review])
- NEVER: executed Python test files declare variables or constants; every value or configuration choice those declarations would bind lives in spec-governed harnesses, generators, inert whole-payload fixtures, source contracts, or justified eval case data ([review])
- NEVER: use shared test-owned constant bags as a fix for duplicated test literals — moving a hand-picked value behind a name does not increase evidence ([review])
- NEVER: treat `st.just(...)`, `st.sampled_from(...)` with a single source-owned singleton, or a constant-returning factory as a generator domain — source-owned singleton construction belongs in the owning source module ([review])
- NEVER: use fixture files to store plain strings or numbers that represent test data — fixtures are for real-world payloads whose shape matters as a whole ([review])
