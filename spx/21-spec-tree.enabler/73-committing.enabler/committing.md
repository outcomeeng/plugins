# Committing

PROVIDES a commit workflow enforcing Conventional Commits with selective staging for local verification checkpoints and publication-ready changes
SO THAT all developers
CAN produce atomic, well-described commits that map cleanly to spec tree changes

## Assertions

### Scenarios

- Given staged changes spanning multiple plugins, when the commit skill runs, then it recommends splitting into separate commits per plugin ([test](tests/test_committing.scenario.l1.py))
- Given a commit message, when validated, then it conforms to Conventional Commits format (type, optional scope, description) ([test](tests/test_committing.scenario.l1.py))
- Given spec tree changes and version bumps, when committed, then both are included in the same commit ([test](tests/test_committing.scenario.l1.py))

### Compliance

- ALWAYS: `/commit-changes` presents payload-bearing `git commit` message input by supported harness environment — quoted heredoc to `git commit -F -` for interactive Claude Code and Codex sessions, and one physical `printf '%s\n' ... | git commit -F -` line for programmatic runners that require single-line commands — per `spx/15-agent-tools.pdr.md` ([audit])
- ALWAYS: `/commit-changes` can seal stabilized work as a local verification checkpoint when deterministic verification is `passing`, `failing`, or `not-run`, and reports that state with the checkpoint; passing verification and approval govern agentic-gate dispatch and publication readiness rather than local commit eligibility, and a repaired subject receives a new checkpoint commit before re-verification ([audit])
- ALWAYS: include version bumps in the same commit as the changes that warrant them — separate version bump commits create misleading history ([audit])
- NEVER: commit files that likely contain secrets (.env, credentials) — warn the user if they request it ([audit])
