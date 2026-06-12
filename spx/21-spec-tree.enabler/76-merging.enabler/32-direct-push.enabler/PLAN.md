# Plan: Direct-push Transport

## Scope

Declared transport. Two variants:

1. **Direct to `origin/<trunk>`** (active scope) — push the verified changeset to the remote default branch. Used by coordination-note-only changesets and by any project that selects this transport in `spx/local/merging.md`.
2. **Direct to a local trunk checkout** (deferred) — merge into a local default-branch worktree, then push. Depends on the local trunk being available. Implementation deferred until a consumer needs it.

## Pending

- Author the `/merge` direct-push execution path (skill materialization step).
- Add `[eval]` coverage mirroring the GitHub-PR transport gate evals once the execution path exists; the current `[audit]` assertions are the Declared-state evidence.
- Decide the local-trunk-checkout (variant 2) execution and worktree-safety model when a consumer requires it.
