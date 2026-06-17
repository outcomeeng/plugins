# Base Currency

PROVIDES a session-start signal when the working directory's HEAD trails its resolved default branch
SO THAT an agent beginning work in a worktree
CAN start on a current base rather than building on stale state

`spx hooks session-start` performs the read-only base-staleness check and emits the result in the session-start JSON document per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`; the rendered directive instructs the agent to fetch and rebase onto the resolved default, never reset.

## Assertions

### Scenarios

- Given a `SessionStart` payload whose project directory is a git worktree behind its resolved default branch by N (N greater than zero), when `spx hooks session-start` runs, then it exits zero and its JSON document carries a `specTree.directives` entry of kind `base-currency` with `behind_count` equal to N and `default_branch` set to the resolved default branch ([test](tests/test_base_currency.scenario.l1.py))

### Mappings

- A worktree base state maps to the base-currency directive: behind the resolved default by N (N greater than zero) maps to a `base-currency` entry carrying `behind_count` N and the resolved `default_branch`; current with the default maps to no `base-currency` entry; a non-git directory or an unresolvable default maps to no `base-currency` entry and a zero exit ([test](tests/test_base_currency.mapping.l1.py))

### Compliance

- ALWAYS: `spx hooks session-start` resolves the default branch from git's configured default (`origin/HEAD`), never a literal `origin/main` ([test](tests/test_base_currency.compliance.l1.py))
- ALWAYS: the base-staleness check is read-only — `spx hooks session-start` runs no `git fetch` and no state-mutating git command, and HEAD and refs are unchanged after it runs ([test](tests/test_base_currency.compliance.l1.py))
