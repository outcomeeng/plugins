# Base Currency

PROVIDES a session-start signal when the working directory's HEAD trails its resolved default branch
SO THAT an agent beginning work in a worktree
CAN start on a current base rather than building on stale state

## Assertions

### Scenarios

- Given a `SessionStart` payload whose project directory is a git worktree behind its resolved default branch, when the hook runs, then stdout carries a `<SPEC-TREE_SESSION_START .../>` directive naming the behind-count and the resolved default branch and instructing the agent to fetch and rebase onto it, never reset ([test](tests/test_base_currency.scenario.l1.py))

### Mappings

- A worktree base state maps to the hook's staleness output: behind the resolved default by N (N greater than zero) maps to a `<SPEC-TREE_SESSION_START>` directive carrying N; current with the default maps to no directive; a non-git directory or an unresolvable default maps to no directive and a zero exit ([test](tests/test_base_currency.mapping.l1.py))

### Compliance

- ALWAYS: the `SessionStart` hook resolves the default branch from git's configured default (`origin/HEAD`), never a literal `origin/main` ([test](tests/test_base_currency.compliance.l1.py))
- ALWAYS: the base-staleness check is read-only — the hook runs no `git fetch` and no state-mutating git command, and HEAD and refs are unchanged after it runs ([test](tests/test_base_currency.compliance.l1.py))
