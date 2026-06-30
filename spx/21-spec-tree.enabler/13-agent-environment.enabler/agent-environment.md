# Agent Environment

PROVIDES a stable per-agent session identity and a per-runtime session directory keyed on it
SO THAT session management nodes (sessions, pickup, handoff)
CAN scope work to the current agent without file-system heuristics or race conditions

The spec-tree plugin's only runtime hook is a `SessionStart` hook that delegates to the `spx` CLI hook runner — `spx hook run <hook-name-kebab-case>`, here `spx hook run session-start` — through a hook-safety-compliant inline guard. On the normal path the `spx` hook runner delivers the session environment: it writes the agent session identity and project directories into the harness-provided `$CLAUDE_ENV_FILE` and records the worktree-occupancy claim. On the disabled-or-absent path the guard exits with a valid empty result and writes nothing. The plugin owns only the hook's wiring and its fail-open guard; it embeds no `.spx/`, git, transcript, or session logic of its own, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` and `spx/15-hook-safety.pdr.md`. The identity's distinctness and the per-session directory the `spx` CLI realizes are its own contract, verified by its suite; this node verifies the plugin's integration with it. This node holds the hook-wide constraint that spans its children.

## Assertions

### Scenarios

- Given a `SessionStart` payload and `spx` resolvable on `PATH`, when the shipped hook command runs, then the `spx` hook runner delivers the session environment — `CLAUDE_SESSION_ID` and `SPX_WORKTREE_CLAIM_PATH` reach `$CLAUDE_ENV_FILE` and a worktree-occupancy claim is recorded under the project's `.spx/worktrees/` ([test](tests/test_agent_environment.scenario.l1.py))
- Given the kill switch `SPECTREE_SESSION_HOOK_DISABLED=1`, when the shipped hook command runs, then it exits with a valid empty result and writes nothing — no identity, no claim, no `.spx/` state ([test](tests/test_agent_environment.scenario.l1.py))
- Given `spx` is unresolvable on `PATH`, when the shipped hook command runs, then it exits with a valid empty result and writes nothing — the fail-open safety net for a consumer without `spx` installed ([test](tests/test_agent_environment.scenario.l1.py))
- Given the shipped hook runs end-to-end against the real `spx` CLI in a git worktree with the session's controlling process alive, when it completes, then `$CLAUDE_ENV_FILE` carries the correct values — `CLAUDE_SESSION_ID` for the payload, the resolved `CLAUDE_PROJECT_DIR` and `PROJECT_DIR`, and `SPX_WORKTREE_CLAIM_PATH` for the recorded claim — and `spx worktree status` reports the worktree `running`, so spx itself recognizes the claim the hook recorded ([test](tests/test_agent_environment.scenario.l3.py))

### Conformance

- The spec-tree plugin's `hooks.json` declares exactly one hook event — `SessionStart` — whose command delegates to `spx hook run session-start` and names no plugin-shipped script path ([test](tests/test_agent_environment.conformance.l1.py))

### Audit

- ALWAYS: the `SessionStart` hook delegates session-identity, project-dir, and worktree-occupancy work to the `spx` CLI hook runner and embeds no `.spx/`, git, transcript, or session logic of its own; on the disabled-or-absent path it exits with a valid empty result, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` ([audit])
