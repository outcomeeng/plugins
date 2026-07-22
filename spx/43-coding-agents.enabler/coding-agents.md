# Coding Agents

PROVIDES shared environment, identity, authority, communication, and coordination contracts for coding agents
SO THAT agent-facing workflows operating across panes, sessions, worktrees, native supervisors, and remote-managed tasks
CAN use environment capabilities without centralizing workflow ownership or reconstructing environment state

## Assertions

### Compliance

- ALWAYS: coordination identifies every participating environment, agent, pane or task, worktree, branch, run, and repository with the complete identity value supplied by its authoritative source ([audit])
- ALWAYS: explicit SPX facts, public environment projections, checked command results, and operator-confirmed external changes are authoritative coordination evidence; prose inference remains advisory ([audit])
- ALWAYS: a supported coding environment exposes source-owned operations and explicit unavailable results rather than requiring workflows to discover command syntax or infer unsupported behavior ([audit])
- ALWAYS: the operating agent owns successful work, run identities, retry selection, checkpoints, results, and continuation state for its workflow ([audit])
- NEVER: one coding-agent workflow takes ownership of another workflow's internal state, successful results, or continuation decisions ([audit])
- NEVER: a coding-agent workflow edits, stages, stashes, checks out, resets, or commits in a sibling worktree; delegated mutation authority binds to exact environment and repository identities ([audit])
- NEVER: a plugin skill scans harness transcript files or transcript directories; transcript discovery, parsing, normalization, and correlation belong to SPX ([audit])
- NEVER: an agent-facing workflow constructs raw environment commands, invokes environment command help, or depends on a separate environment-control skill when a source-owned environment capability exists ([audit])
