# Legacy

PROVIDES standalone commit workflow and foundational testing for projects without the spx CLI
SO THAT projects not using spec-tree
CAN still benefit from structured commit messages and test methodology

The legacy plugin contains `/committing-changes` (git commit guidance), `/testing` (foundational 5-stage, 5-factor methodology), `/reviewing-tests` (test review protocol), and session management (`/handoff`, `/pickup`). Spec-tree users use `spec-tree:committing-changes` and `spec-tree:testing` instead, which are supersets.

## Assertions

### Compliance

- ALWAYS: provide foundational testing methodology that language-specific skills reference — the legacy plugin is the testing methodology's source of truth for non-spec-tree projects ([review])
- NEVER: duplicate spec-tree-specific concerns (context loading, spec assertions) — legacy is the standalone subset ([review])
