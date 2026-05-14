# Test Data Ownership

PROVIDES ownership rules for TypeScript test values, generators, harnesses, and fixtures
SO THAT TypeScript tests
CAN distinguish source contracts from generated input domains and avoid hiding literals in test-infrastructure modules

## Assertions

### Compliance

- ALWAYS: values that the source imports or should import come from the runtime, framework, protocol package, or production module that owns them — tests do not define local stand-ins for source vocabulary ([review])
- ALWAYS: values that the code under test owns are exposed by source-owned registries, tuples, constructors, typed factories, schemas, or structured metadata — tests consume source contracts instead of duplicating them ([review])
- ALWAYS: values that only the test needs are generated when they represent a variable input domain such as paths, names, identifiers, option sets, file contents, encodings, counts, or product shapes — generated values expand the exercised space ([review])
- ALWAYS: expected outputs for generated inputs are derived from the input, an independent oracle, or a source outside the module under test — tests do not copy expected data from the same implementation they verify ([review])
- ALWAYS: generators vary, compose, shrink, or explore meaningful alternatives — the generator abstraction carries evidence value beyond naming a constant ([review])
- ALWAYS: harnesses manage setup, teardown, cleanup, dependency checks, and access to external resources such as filesystems, browsers, APIs, Docker, product binaries, or local services — harnesses do not own arbitrary test data or replace the behavior an assertion claims to verify ([review])
- ALWAYS: fixture files contain real-world payloads whose complete shape matters to the behavior under test — fixtures are inert data samples, not a hiding place for isolated strings or numbers ([review])
- ALWAYS: executed tests access fixtures only by reading files, copying files into temp projects, or passing fixture paths to the code or program under test — fixture contents remain inputs rather than executable test dependencies ([review])
- NEVER: import fixture modules, require fixture files, or consume fixture exports from executed TypeScript tests — even a valid `*.ts` fixture for a linter, parser, pre-commit hook, or scanner is input source text, not a module dependency ([review])
- NEVER: create shared test-owned constants such as `TEST_FIXTURES`, `SAMPLE_PATHS`, `TYPICAL`, or `EDGES` to satisfy literal-reuse checks — named example bags preserve hand-picked values ([eval](evals/shared-constant-bag/eval.toml))
- NEVER: create a generator whose only behavior is `fc.constant(...)` for a source-owned singleton shape — the owning source module provides the constructor or registry ([review])
