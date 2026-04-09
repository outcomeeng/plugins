# Sync Exclude

PROVIDES a sync script that translates `spx/EXCLUDE` into Python tool configuration in `pyproject.toml`
SO THAT Python projects using spec-tree
CAN author specs and tests before implementation without breaking the quality gate

The script reads node paths from `spx/EXCLUDE` and updates `pyproject.toml` to exclude specified nodes from pytest, mypy, and pyright. Ruff is never excluded — style is checked regardless of implementation existence.

## Assertions

### Scenarios

- Given an `spx/EXCLUDE` file with one flat node path, when synced, then `pyproject.toml` contains a pytest `--ignore` flag, a mypy exclude regex, and a pyright exclude path for that node ([test](tests/test_sync_exclude.unit.py))
- Given an `spx/EXCLUDE` file with comments and blank lines, when parsed, then only non-comment, non-blank lines are returned as node paths ([test](tests/test_sync_exclude.unit.py))
- Given an `spx/EXCLUDE` file with a nested path (`57-subsystems.outcome/32-risc-v.outcome`), when synced, then all three tool configurations contain the full nested path with correct escaping ([test](tests/test_sync_exclude.unit.py))
- Given a `pyproject.toml` with previously-synced excluded entries, when synced with different nodes, then old entries are replaced with new entries ([test](tests/test_sync_exclude.unit.py))
- Given a `pyproject.toml` already in sync with `spx/EXCLUDE`, when synced again, then no changes are made ([test](tests/test_sync_exclude.unit.py))
- Given `spx/EXCLUDE` does not exist, when the script runs, then it exits with error code 1 ([test](tests/test_sync_exclude.unit.py))
- Given a `pyproject.toml` without `[tool.mypy]` or `[tool.pyright]` sections, when synced, then the missing sections are created and populated with exclude entries ([test](tests/test_sync_exclude.unit.py))

### Mappings

- Node path `{node}` maps to pytest `--ignore=spx/{node}/`, mypy `^spx/{escaped_node}/`, and pyright `spx/{node}/` ([test](tests/test_sync_exclude.unit.py))

### Properties

- Sync is idempotent: running twice with the same `spx/EXCLUDE` produces the same `pyproject.toml` content ([test](tests/test_sync_exclude.unit.py))

### Compliance

- NEVER: exclude specified nodes from ruff — style is checked regardless of implementation existence ([review])
- ALWAYS: use tomlkit for TOML round-tripping — preserves comments, formatting, and whitespace ([review])
- ALWAYS: detect previously-synced entries by value pattern, not marker comments ([review])
