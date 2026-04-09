# Committing

WE BELIEVE THAT a commit workflow enforcing Conventional Commits with selective staging
WILL produce atomic, well-described commits that map cleanly to spec tree changes
CONTRIBUTING TO traceable git history and easier change review

The `/committing-changes` skill guides commit message structure, scope selection, and staged file review. The `/commit` command invokes it with auto-detected context.

## Assertions

### Scenarios

- Given staged changes spanning multiple plugins, when the commit skill runs, then it recommends splitting into separate commits per plugin ([test](tests/test_committing.unit.py))
- Given a commit message, when validated, then it conforms to Conventional Commits format (type, optional scope, description) ([test](tests/test_committing.unit.py))
- Given spec tree changes and version bumps, when committed, then both are included in the same commit ([test](tests/test_committing.unit.py))

### Compliance

- ALWAYS: include version bumps in the same commit as the changes that warrant them — separate version bump commits create misleading history ([review])
- NEVER: commit files that likely contain secrets (.env, credentials) — warn the user if they request it ([review])
