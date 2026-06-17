# Agent Environment

PROVIDES a stable per-agent session identity, a per-runtime session directory keyed on it, and a session-start signal when the working directory trails its default branch
SO THAT session management nodes (sessions, applying, committing)
CAN scope work to the current agent and begin on a current base, without file-system heuristics, race conditions, or stale-base rework

The spec-tree plugin delivers its session-start and pre-tool-use behaviors by wiring those runtime hook events to `spx hooks <event>`; for a converted event the plugin ships no hook script, and `spx hooks <event>` owns every behavior, all `.spx/` and transcript I/O, and the `$CLAUDE_ENV_FILE` write, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`. This node holds the hook-wiring constraint that spans its children. The compaction and post-tool-use events converge to the same contract as their nodes are decomposed (`PLAN.md`).

## Assertions

### Mappings

- The spec-tree plugin's hook-wiring file maps each converted hook event to its `spx hooks <event>` command — SessionStart to `spx hooks session-start` and PreToolUse to `spx hooks pre-tool-use` — and the plugin's `scripts/` directory carries no `session-start` or `load-gate` script alongside the wiring file ([test](tests/test_agent_environment.mapping.l1.py))

### Compliance

- ALWAYS: for a converted hook event the spec-tree plugin's only contribution is the wiring entry; no behavior, `.spx/` access, git inspection, or `$CLAUDE_ENV_FILE` write for that event is performed by plugin-shipped code — every such behavior is owned by `spx hooks <event>`, per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` ([audit])
