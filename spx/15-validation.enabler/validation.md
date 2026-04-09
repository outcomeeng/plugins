# Validation

PROVIDES pre-commit validation that catches invalid plugin artifacts before they enter the repository
SO THAT all plugin and skill authors
CAN trust that committed artifacts conform to Claude Code and Agent Skills standards

Two scripts:

1. **SKILL.md frontmatter validation** (`validate-skill-frontmatter.py`) — Ensures skill files conform to the fields the Claude Code CLI accepts.
2. **Plugin manifest validation** (`validate-plugins.py`) — Discovers and validates all marketplace and plugin manifests via `claude plugin validate`.

## Field Source

The set of valid SKILL.md frontmatter fields is extracted from the installed Claude Code CLI binary. The binary embeds JavaScript source that parses frontmatter via property access patterns (`var["field-name"]`, `var.field`). Extracting these from the binary ensures the validation stays current as Claude Code evolves — no hardcoded list to maintain.

The Agent Skills open standard fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`) serve as a minimum floor. The binary-extracted fields serve as the maximum ceiling. Any frontmatter key outside this union is invalid.

## Assertions

### Scenarios

- Given a SKILL.md with only standard Agent Skills fields, when validated, then no errors are reported ([test](tests/test_validation.unit.py))
- Given a SKILL.md with an unknown field (`foo-bar`), when validated, then an error is reported naming the invalid field ([test](tests/test_validation.unit.py))
- Given a SKILL.md with no frontmatter, when validated, then no errors are reported ([test](tests/test_validation.unit.py))
- Given a file that is not named SKILL.md, when passed to the validator, then it is skipped ([test](tests/test_validation.unit.py))
- Given the Claude binary is unavailable, when valid fields are requested, then the standard fields are returned as fallback ([test](tests/test_validation.unit.py))
- Given binary extraction fails, when valid fields are requested, then the standard fields are returned as fallback ([test](tests/test_validation.unit.py))

### Compliance

- NEVER: hardcode Claude Code-specific fields — they are derived from the binary at runtime ([review])

## Plugin Manifest Validation

A single script that discovers and validates all marketplaces and plugins under a given root directory.

### Scenarios

- Given a directory containing `.claude-plugin/marketplace.json`, when validated, then `claude plugin validate` runs against it ([test](tests/test_validate_plugins.unit.py))
- Given a directory containing `plugins/*/` with `.claude-plugin/plugin.json`, when validated, then `claude plugin validate` runs against each plugin ([test](tests/test_validate_plugins.unit.py))
- Given a plugin that fails validation, when validated, then the script exits non-zero and reports which plugin failed ([test](tests/test_validate_plugins.unit.py))
- Given no marketplace or plugins found, when validated, then the script exits non-zero with an error ([test](tests/test_validate_plugins.unit.py))
