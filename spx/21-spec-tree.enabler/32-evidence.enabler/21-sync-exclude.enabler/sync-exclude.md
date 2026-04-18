# Sync Exclude

PROVIDES EXCLUDE-aware invocation logic inside the `spx` CLI
SO THAT spec-tree projects in any language
CAN author specs and tests before implementation without breaking the quality gate

The `spx` CLI reads node paths from `spx/EXCLUDE` and passes exclusion flags to each tool at invocation time. It never writes to project configuration files (`pyproject.toml`, `package.json`, `tsconfig.json`). Test runners are auto-detected by walking `spx/**/tests/` and grouping files by extension.

## Assertions

### Scenarios

- Given an `spx/EXCLUDE` file with one flat node path, when `spx test passing` runs, then the node's tests are excluded from the test runner invocation ([review])
- Given an `spx/EXCLUDE` file with comments and blank lines, when parsed, then only non-comment, non-blank lines are returned as node paths ([review])
- Given an `spx/EXCLUDE` file with a nested path (`57-subsystems.outcome/32-risc-v.outcome`), when `spx test passing` runs, then the full nested path is excluded ([review])
- Given `spx/EXCLUDE` does not exist, when `spx test passing` runs, then all discovered tests run (no exclusions) ([review])
- Given `spx test` (without `passing`), when run, then all discovered tests run regardless of EXCLUDE entries ([review])

### Mappings

- File extension `test_*.py` maps to pytest runner ([review])
- File extension `*.test.ts` / `*.test.tsx` maps to vitest runner ([review])

### Properties

- Test discovery is deterministic: the same tree structure produces the same set of test files grouped by runner ([review])

### Compliance

- NEVER: exclude specified nodes from linting — style is checked regardless of implementation existence ([review])
- NEVER: write to project configuration files — `spx` passes flags at invocation time ([review])
- ALWAYS: auto-detect test runners from file extensions — no explicit language configuration required ([review])
