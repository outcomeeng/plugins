# Python Architecture

PROVIDES Python architecture standards for boundaries, dependencies, source-owned vocabulary, and testable module structure
SO THAT Python testing, implementation, and audit skills
CAN derive consistent guidance from source contracts rather than from incidental code shape

## Assertions

### Compliance

- ALWAYS: production modules expose semantically named source-owned vocabulary for domain tokens, statuses, command names, rule identifiers, message identifiers, schemas, and registry entries — tests and consumers import the owning source contract instead of copying literals ([audit])
- ALWAYS: side-effect boundaries use typed dependencies such as protocols, dataclasses, context managers, or explicit collaborator objects for process execution, filesystem work, clocks, network clients, and external services — tests observe behavior through stable interfaces rather than framework mocks ([audit])
- ALWAYS: controlled implementations and recording collaborators preserve the production Protocol boundary and expose observations only; linked tests own every predicate and assertion call, including interaction checks ([audit])
- ALWAYS: script and command entrypoints stay thin and delegate domain behavior to imported modules — argument parsing and process exit behavior remain separate from reusable Python logic ([audit])
- ALWAYS: closed vocabularies derive runtime values, type annotations, schemas, and filtered subsets from one source declaration — parallel constants and duplicated string unions drift ([audit])
- NEVER: create production modules only to aggregate values for tests — source ownership follows product semantics, not test convenience ([audit])
- NEVER: extract typed protocol members into named constants solely to silence magic-value warnings — the owning type, enum, schema, or registry documents the protocol ([audit])
- NEVER: architecture guidance recommends framework mocks, matcher-driven spies, `was_called_with`, `assert_called`, or collaborator methods that return a test verdict ([audit])
