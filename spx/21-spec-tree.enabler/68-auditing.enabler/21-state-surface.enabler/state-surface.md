# State Surface

PROVIDES a worktree-local on-disk surface — `.spx/audits/<lang>/<branch-slug>.md` — that persists open and resolved audit findings, plus a TTL-bounded run lock at `<state-file>.lock` that serialises concurrent runs on the same branch
SO THAT the local `audit-orchestrator` agent and any future caller of the `/audit` skill's stateful orchestration mode
CAN iterate auditably across commits — re-running the audit carries forward open finding IDs, resolves findings that no longer apply, and reopens regressions under their original IDs — without persisting any audit state into the product tree

## Assertions

### Scenarios

- Given an absent state file at `.spx/audits/<lang>/<branch-slug>.md`, when the audit runs against findings F1 and F2, then the file is created and F1, F2 receive monotonic IDs starting at `f-001` ([test](tests/test_state_surface.scenario.l1.py))
- Given a state file with open finding `f-001` at `(file_line, root_cause)`, when the next run reports the same `(file_line, root_cause)`, then `f-001` carries forward with refreshed `required_fix` and `next_finding_id` does not advance ([test](tests/test_state_surface.scenario.l1.py))
- Given a state file with open finding `f-001`, when the next run reports no findings, then `f-001` moves to the resolved table with `resolved_at` set to the current run's SHA ([test](tests/test_state_surface.scenario.l1.py))
- Given a state file with resolved finding `f-001` at `(file_line, root_cause)`, when a later run reports the same `(file_line, root_cause)`, then `f-001` is reopened with its original ID and `next_finding_id` does not advance ([test](tests/test_state_surface.scenario.l1.py))
- Given a lock file at `<state-file>.lock` whose mtime is within the TTL, when a second audit attempts to acquire the lock, then acquisition fails with `RunLockError` and the second run halts before reading or writing state ([test](tests/test_state_surface.scenario.l1.py))
- Given a lock file at `<state-file>.lock` whose mtime is older than the TTL, when an audit attempts to acquire the lock, then the stale lock is overwritten and the run proceeds ([test](tests/test_state_surface.scenario.l1.py))
- Given two branches whose slugs collide on the same `<lang>` subdirectory, when both runs persist state, then each state file's path differs because `branch_slug` appends a SHA-256 suffix to one of them ([test](tests/test_state_surface.scenario.l1.py))

### Compliance

- ALWAYS: state files live under `.spx/audits/<lang>/<branch-slug>.md` — the per-language subdirectory partitions state so a polyglot scope produces independent state files per partition; the branch-slug naming keeps state stable across runs on the same branch ([review])
- ALWAYS: the `.spx/` root is gitignored — audit state is worktree-local development scratch, not product truth, and never enters the repository's commit history ([review])
- ALWAYS: each state-transition writes the state file atomically — `save_state` writes to `<state-file>.tmp` and calls `os.replace`, so a crash mid-write leaves the prior state intact rather than corrupted ([test](tests/test_state_surface.scenario.l1.py))
- ALWAYS: the run lock at `<state-file>.lock` releases on every exit path — context-manager `__exit__` removes the lock whether the run exits cleanly or via exception, so a crashed run does not block the next run for a full TTL window ([test](tests/test_state_surface.scenario.l1.py))
- NEVER: a finding ID is reissued — `next_finding_id` strictly exceeds every ID ever assigned on the branch, including resolved IDs, so a regression always reopens its original ID instead of seeing a duplicate allocation ([test](tests/test_state_surface.scenario.l1.py))
- NEVER: audit state is written to a path inside `spx/` or any other tracked product directory — the only persisted surface is `.spx/audits/`; the audit verdict itself remains in-conversation per the `/audit` skill's stateless contract ([review])
