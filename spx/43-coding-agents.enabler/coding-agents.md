# Coding Agents

PROVIDES shared identity, authority, and coordination contracts for coding-agent runtimes
SO THAT agent-facing workflows operating across panes, sessions, and worktrees
CAN exchange facts and restore conditions for autonomous work without centralizing workflow ownership

## Assertions

### Compliance

- ALWAYS: coordination identifies every participating agent, pane, worktree, branch, run, and repository with the complete identity value supplied by its authoritative source ([audit])
- ALWAYS: explicit SPX facts, public runtime projections, direct command results, and operator-confirmed external changes are authoritative coordination evidence; prose inference remains advisory ([audit])
- ALWAYS: Prowl is the sole authority for durable pane topology, while native runtime and session selection belongs to SPX through the exact `spx agent resume --latest` command ([audit])
- ALWAYS: the operating agent owns successful work, run identities, retry selection, checkpoints, and continuation state for its workflow ([audit])
- NEVER: coding-agent recovery persists or reconstructs Prowl pane topology, native runtime identity, or native session identity ([audit])
- NEVER: one coding-agent workflow takes ownership of another workflow's internal state, successful results, or continuation decisions ([audit])
- NEVER: a coding-agent workflow edits, stages, stashes, checks out, resets, or commits in a sibling worktree; delegated mutation authority binds to an exact pane, worktree, branch, and repository identity ([audit])
- NEVER: a plugin skill scans harness transcript files or transcript directories; transcript discovery, parsing, normalization, and correlation belong to SPX ([audit])
