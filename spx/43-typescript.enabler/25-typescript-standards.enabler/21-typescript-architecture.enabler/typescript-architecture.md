# TypeScript Architecture

PROVIDES TypeScript architecture standards for boundaries, dependencies, source-owned vocabulary, and testable module structure
SO THAT TypeScript testing, implementation, and audit skills
CAN derive consistent guidance from source contracts rather than from incidental code shape

## Assertions

### Compliance

- ALWAYS: production modules expose semantically named source-owned vocabulary for domain tokens, statuses, command names, rule identifiers, and message identifiers — tests and consumers import the owning source contract instead of copying literals ([review])
- ALWAYS: side-effect boundaries use typed dependencies for process execution, filesystem work, clocks, network clients, and external services — tests observe behavior through stable interfaces rather than framework mocks ([review])
- ALWAYS: command entrypoints stay thin and delegate domain behavior to imported modules — CLI parsing and process exit behavior remain separate from reusable TypeScript logic ([review])
- ALWAYS: closed vocabularies derive runtime values, TypeScript unions, schemas, and filtered subsets from one source declaration — parallel constants and duplicated string unions drift ([review])
- NEVER: create production modules only to aggregate values for tests — source ownership follows product semantics, not test convenience ([review])
- NEVER: extract typed literal union members into named constants solely to satisfy lint warnings — the type annotation already documents enum-like protocol values ([review])
