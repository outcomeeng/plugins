# Test Data Ownership

PROVIDES ownership rules for TypeScript test values, generators, harnesses, and fixtures
SO THAT TypeScript tests
CAN distinguish source contracts from generated input domains and avoid hiding literals in test-infrastructure modules

## Assertions

### Compliance

- ALWAYS: values that the source imports or should import come from the runtime, framework, protocol package, or production module that owns them — tests do not define local stand-ins for source vocabulary ([audit])
- ALWAYS: values that the code under test owns are exposed by source-owned registries, tuples, constructors, typed factories, schemas, or structured metadata — tests consume source contracts instead of duplicating them ([audit])
- ALWAYS: values that only the test needs are generated when they represent a variable input domain such as paths, names, identifiers, option sets, file contents, encodings, counts, or product shapes — generated values expand the exercised space ([audit])
- ALWAYS: expected outputs for generated inputs are derived from the input, an independent oracle, or a source outside the module under test — tests do not copy expected data from the same implementation they verify ([audit])
- ALWAYS: generators vary, compose, shrink, or explore meaningful alternatives — the generator abstraction carries evidence value beyond naming a constant ([audit])
- ALWAYS: property-based test configuration — run counts, seed selection, replay output, and failure diagnostics — lives in a spec-governed harness so every property failure reports the seed and replay path ([audit])
- ALWAYS: harnesses manage setup, teardown, cleanup, dependency checks, and access to external resources such as filesystems, browsers, APIs, Docker, product binaries, or local services — harnesses do not own arbitrary test data or replace the behavior an assertion claims to verify ([audit])
- ALWAYS: fixture files contain real-world payloads whose complete shape matters to the behavior under test — fixtures are inert data samples, not a hiding place for isolated strings or numbers ([audit])
- ALWAYS: executed tests access fixtures only by reading files, copying files into temp projects, or passing fixture paths to the code or program under test — fixture contents remain inputs rather than executable test dependencies ([audit])
- NEVER: import fixture modules, require fixture files, or consume fixture exports from executed TypeScript tests — even a valid `*.ts` fixture for a linter, parser, pre-commit hook, or scanner is input source text, not a module dependency ([audit])
- ALWAYS: a `const`, `let`, `var`, framework fixture parameter, or property-generated parameter in an executed TypeScript test is valid when it only receives or renames an observation, source-owned contract, generated value, harness handle, or fixture path, and belongs to its semantic owner when it chooses a case, expected result, runner or seed configuration, setup policy, generator domain, fixture content, or verdict rule, per `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` ([audit])
- NEVER: create shared test-owned constants such as `TEST_FIXTURES`, `SAMPLE_PATHS`, `TYPICAL`, or `EDGES` to satisfy literal-reuse checks — named example bags preserve hand-picked values ([eval](evals/shared-constant-bag/eval.toml))
- NEVER: create a generator whose only behavior is `fc.constant(...)` for a source-owned singleton shape — the owning source module provides the constructor or registry ([audit])
