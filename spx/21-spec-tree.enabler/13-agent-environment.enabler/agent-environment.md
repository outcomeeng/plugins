# Agent Environment

PROVIDES a stable per-agent session identity and a per-runtime session directory keyed on it
SO THAT session management nodes (sessions, pickup, handoff)
CAN scope work to the current agent without file-system heuristics or race conditions

The spec-tree plugin's only runtime hook is a `SessionStart` hook that writes the agent session identity into the harness-provided `$CLAUDE_ENV_FILE`; it performs no other behavior, holds no `.spx/` state, inspects no git state, and runs no subprocess, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`. This node holds the hook-wide constraint that spans its children.

## Assertions

### Scenarios

- Given a `SessionStart` payload, when the hook runs, then its only effect is writing `CLAUDE_SESSION_ID` to `$CLAUDE_ENV_FILE` — it emits no stdout directive and creates no `.spx/` state (no worktree claim, no session directory) ([test](tests/test_agent_environment.scenario.l1.py))

### Conformance

- The spec-tree plugin's `hooks.json` declares exactly one hook event — `SessionStart`, wired to `scripts/session-start.py` — and no other hook event ([test](tests/test_agent_environment.conformance.l1.py))

### Compliance

- ALWAYS: the `SessionStart` hook's only effect is writing the agent session identity to `$CLAUDE_ENV_FILE`; it reads or writes no `.spx/` state, inspects no git state, parses no transcript, and runs no subprocess, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` ([review])
