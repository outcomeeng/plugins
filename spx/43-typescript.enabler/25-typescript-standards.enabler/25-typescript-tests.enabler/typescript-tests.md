# TypeScript Tests

PROVIDES TypeScript test standards for evidence type, execution level, testability, test data ownership, test-infrastructure auditing, and generator use
SO THAT TypeScript testing and audit skills
CAN produce evidence that is coupled to source behavior, maintainable under source changes, and free of literal laundering

## Assertions

### Compliance

- ALWAYS: TypeScript test guidance starts from the spec assertion and selected evidence type before choosing file names, runners, harnesses, generators, or examples — evidence shape follows the claim being proved ([review])
- ALWAYS: tests for TypeScript code under test treat source architecture as changeable when the code is not testable through its production contract — acceptable evidence often requires improving source contracts, extracting pure logic, or injecting side-effect dependencies before writing the test ([review])
- ALWAYS: source-owned protocol values and singleton shapes come from production modules through exported registries, constructors, or typed factories — tests import ownership rather than recreating it ([review])
- ALWAYS: variable test input domains come from generators that vary, compose, shrink, or explore more than one meaningful value — generator APIs exist to expand evidence, not to hide constants ([review])
- ALWAYS: property-based TypeScript tests run through seed-reporting harnesses that own `numRuns`, seed selection, replay input, and failure diagnostics — reproducible failures are part of the evidence contract, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` and `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([review])
- ALWAYS: TypeScript test infrastructure follows `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`: harnesses manage resource lifecycle and access to behavior, generators produce variable input domains, fixtures stay inert, and source-owned domain truth comes from source modules ([review])
- ALWAYS: fixture files are inert input artifacts read from disk, copied into temp projects, or passed by path to code or programs under test — fixtures may be valid `*.ts` source files for linters, parsers, pre-commit hooks, or scanners, but executed tests never import them as modules or consume their exports ([review])
- ALWAYS: TypeScript test audit opens imported test-infrastructure modules — generators, harnesses, fixtures — before approving an assertion; laundering and severed coupling can live outside the test file, and the canonical home for these modules is the `@testing/` path mapping per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md` ([review])
- NEVER: executed TypeScript test files declare variables or constants; every value or configuration choice those declarations would bind lives in spec-governed harnesses, generators, inert whole-payload fixtures, source contracts, or justified eval case data ([review])
- NEVER: use shared test-owned constant bags as a fix for duplicated test literals — moving a hand-picked value behind a name does not increase evidence ([review])
- NEVER: treat `fc.constant(...)` around a source-owned singleton as a generator domain — source-owned singleton construction belongs in the owning source module ([review])
- NEVER: use fixture files to store plain strings or numbers that represent test data — fixtures are for real-world payloads whose shape matters as a whole ([review])
