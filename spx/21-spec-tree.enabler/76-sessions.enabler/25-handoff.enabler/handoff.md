# Handoff

PROVIDES the closing side of session continuity — deciding when a session may close, what continuation each closure thread carries, what the session document records, and what the operator is told
SO THAT an agent whose work has reached a stopping point
CAN leave the repository, the queue, and the operator in a state the next context can act on

Closure, continuation disposition, document shape, and the operator closeout are governed by the children below. `spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md` decides the origin-branch anchor every closure writes. Under the coordination overlay declared in `spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md`, the continuation a closure writes is a Handoff on a Change and the field transitions follow `spx/21-spec-tree.enabler/76-sessions.enabler/21-change-coordination.pdr.md`; the closure precondition and the work-branch release are unchanged.

## Assertions

### Compliance

- ALWAYS: under `spx/local/coordination.md`, `/handoff` creates a Change by creating the issue, adding it to the Changes project, writing Product, Maturity as Proposed, and Status as Available, and verifying the three fields plus empty assignee state before publishing the Handoff; in-place refinement updates the body, writes the target Maturity, reasserts Status as Available, and verifies the same canonical state ([audit])
- ALWAYS: under `spx/local/coordination.md`, `/handoff` releases a held Change by posting one `Handoff:` comment carrying Branch or PR, Completed Activities, Next Activity, Blockers, and Hazards; removing the assignee; writing Status as Available; and verifying Product, Maturity, Status, empty assignee state, and the latest Handoff in that order — and writes no session document ([audit])
- ALWAYS: under `spx/local/coordination.md`, `/handoff` records continuation for work with no Change as one Proposed, Available Change carrying its received input in the issue body and no Product, Maturity, Lifecycle, or Status body metadata, never as a session document ([audit])
- ALWAYS: under `spx/local/coordination.md`, application, successor refinement, and abandonment close the Change as Applied, Refined, or Abandoned only through the authorized record and complete field readback required by `spx/21-spec-tree.enabler/76-sessions.enabler/21-change-coordination.pdr.md`; this node's creation, in-place refinement, and release path remains valid independently of those terminal transitions ([audit])
- NEVER: `/handoff` posts `Application complete` before the changeset has integrated into the authoritative branch, the Assertions and evidence governing the Change's Nodes are satisfied, and the Output is delivered ([audit])
- NEVER: `/handoff` removes the runtime worktree occupancy claim; handoff creates fresh session documents when a continuation reader is needed, archives superseded same-conversation artifacts after the fresh document is verified, and steps off the Git branch when required, while the live worktree claim remains present until a later claim replaces it or liveness marks it free ([audit])
- ALWAYS: `/handoff` invokes `/understand`, then `/contextualize` on the governing node, only immediately before it reads or edits coordination notes or other governed product content; claimed-session and marker recovery from conversation markers and `spx session` output triggers neither, per `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md` ([audit])
