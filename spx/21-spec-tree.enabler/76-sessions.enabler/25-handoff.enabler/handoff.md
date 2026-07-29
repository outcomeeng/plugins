# Handoff

PROVIDES the closing side of session continuity — deciding when a session may close, what continuation each closure thread carries, what the session document records, and what the operator is told
SO THAT an agent whose work has reached a stopping point
CAN leave the repository, the queue, and the operator in a state the next context can act on

Closure, continuation disposition, document shape, and the operator closeout are governed by the children below. `spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md` decides the origin-branch anchor every closure writes.

## Assertions

### Compliance

- ALWAYS: the `/handoff` skill presents `spx session handoff` payload input by supported harness environment — quoted heredoc for interactive Claude Code and Codex sessions, and one physical `printf '%s\n' ... | spx session handoff` line for programmatic runners that require single-line commands — per `spx/15-agent-tools.pdr.md` ([audit])
