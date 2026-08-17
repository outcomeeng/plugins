# Handoff

PROVIDES the closing side of session continuity — deciding when a session may close, what continuation each closure thread carries, what the session document records, and what the operator is told
SO THAT an agent whose work has reached a stopping point
CAN leave the repository, the queue, and the operator in a state the next context can act on

Closure, continuation disposition, document shape, and the operator closeout are governed by the children below. `spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md` decides the origin-branch anchor every closure writes.

## Assertions

### Compliance

- NEVER: `/handoff` removes the runtime worktree occupancy claim; handoff creates fresh session documents when a continuation reader is needed, archives superseded same-conversation artifacts after the fresh document is verified, and steps off the Git branch when required, while the live worktree claim remains present until a later claim replaces it or liveness marks it free ([audit])
- ALWAYS: `/handoff` invokes `/understand`, then `/contextualize` on the governing node, only immediately before it reads or edits coordination notes or other governed product content; claimed-session and marker recovery from conversation markers and `spx session` output triggers neither, per `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md` ([audit])
