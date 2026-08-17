# Pickup

PROVIDES the resumption side of session continuity — reconciling a session document's recorded claims against current state, then loading the node it anchors and presenting an evaluated continuation proposal
SO THAT an agent claiming a session written by another context
CAN act on what the repository supports now rather than on what was true when the session was written

Claim reconciliation and the resumption flow it feeds are governed by the children below. `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler/20-claim-verification.adr.md` decides the reconciliation mechanism. Under the coordination overlay declared in `spx/21-spec-tree.enabler/76-sessions.enabler/sessions.md`, the same resumption reads a Change instead of a session document.

## Assertions

### Compliance

- ALWAYS: under `spx/local/coordination.md`, `/pickup` claims a Change by becoming its sole assignee, stops as `owned_elsewhere` when the Change is closed or held by another account, and turns a legacy queue file into one Proposed Change carrying the whole file verbatim as received input, archiving the file only after the issue and its project item exist ([audit])
- ALWAYS: under `spx/local/coordination.md`, `/pickup` routes by the Change's Maturity — refinement through `/interview`, `/slice`, and `/verify` below `Executable`, with `Framed` and `Sliced` set only on human approval — and executes an Activity only from an `Executable` Change whose Frame (Nodes, Assertions, Decisions), blockers, and lineage it has validated against current truth, continuing from the newest Handoff's Next Activity ([audit])
- NEVER: `/pickup` executes an Activity of a Change below `Executable`, or presents a `next_step`, plan item, or note entry from received input as the recommended action — the Frame's Decisions and Assertions define the work ([audit])
- ALWAYS: `/pickup` brings the checkout current before presenting any session detail or coordination note, for every `git_ref` kind (feature branch, default branch, or commit SHA) and not only inside `/contextualize`, so no recorded claim is read against a stale checkout, per `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler/20-claim-verification.adr.md` ([audit])
- ALWAYS: `/pickup` invokes `/understand` immediately before its first product-content access — the coordination-note path check under `spx/` when the session names a node, otherwise the `/contextualize` invocation for the node the operator names — and not before the claim, session presentation, checkout, base sync, or claim reconciliation, per `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md` ([audit])
