# Handoff

PROVIDES the closing side of session continuity — deciding when a session may close, what continuation each closure thread carries, what the session document records, and what the operator is told
SO THAT an agent whose work has reached a stopping point
CAN leave the repository, the queue, and the operator in a state the next context can act on

Closure, continuation disposition, document shape, and the operator closeout are governed by the children below. `spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md` decides the origin-branch anchor every closure writes. Under the coordination overlay declared in `spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md`, the continuation a closure writes is a Handoff on a Change; the closure precondition and the work-branch release are unchanged.

## Assertions

### Compliance

- ALWAYS: under `spx/local/coordination.md`, `/handoff` refines what the conversation learned into the held Change's body, then either posts one `Handoff:` comment carrying Branch or PR, Completed Activities, Next Activity, Blockers, and Hazards and removes the assignee, or closes the Change as `Applied`, `Refined`, or `Abandoned` with its authorized comment — and writes no session document ([audit])
- ALWAYS: under `spx/local/coordination.md`, `/handoff` records continuation for work with no Change as one Proposed, Available Change carrying its received input, never as a session document ([audit])
- NEVER: `/handoff` posts `Application complete` before the changeset has integrated into the authoritative branch, the Assertions and evidence governing the Change's Nodes are satisfied, and the Output is delivered ([audit])
- NEVER: `/handoff` removes the runtime worktree occupancy claim; handoff creates fresh session documents when a continuation reader is needed, archives superseded same-conversation artifacts after the fresh document is verified, and steps off the Git branch when required, while the live worktree claim remains present until a later claim replaces it or liveness marks it free ([audit])
- ALWAYS: `/handoff` invokes `/understand`, then `/contextualize` on the governing node, only immediately before it reads or edits coordination notes or other governed product content; claimed-session and marker recovery from conversation markers and `spx session` output triggers neither, per `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md` ([audit])
