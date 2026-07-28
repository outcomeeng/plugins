# Pickup

PROVIDES the resumption side of session continuity — reconciling a session document's recorded claims against current state, then loading the node it anchors and presenting an evaluated continuation proposal
SO THAT an agent claiming a session written by another context
CAN act on what the repository supports now rather than on what was true when the session was written

Claim reconciliation and the resumption flow it feeds are governed by the children below. `spx/21-spec-tree.enabler/76-sessions.enabler/65-pickup-claim-verification.adr.md` decides the reconciliation mechanism.

## Assertions

The assertions specifying this concern live in the children.
