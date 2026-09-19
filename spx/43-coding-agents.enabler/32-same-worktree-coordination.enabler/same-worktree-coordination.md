# Same-Worktree Coordination

PROVIDES bounded authority and context exchange for coding agents operating in one worktree
SO THAT advisory collaborators
CAN produce durable results without interfering with tracked files or Git state

## Assertions

- A same-worktree delegation records the sender as the tracked-file and Git owner and carries no write scope: the recipient reads the shared tree and returns its result in the mail record, and the mail body is the payload. The plugin validates that shape and writes nothing; a draft artifact home belongs to the `spx` CLI, whose `.spx/` state logic `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` keeps out of every plugin-shipped script.
- The sender names every required input in the delegation request — a tracked path the recipient reads through the shared tree, or text in the request body — before delivery, and the recipient returns its terminal answer in the handback record's body.
- The recipient never edits tracked files, stages or commits changes, checks out or synchronizes branches, invokes `/sync-base`, or directly traverses product content in the shared worktree.
- Missing or conflicting sender ownership, or a delegation that names a write scope, produces a signal gap and no work request.
- Every same-worktree request and terminal handback is a message record the communication contract declares, delivered through the agent-mail capability with the one-line doorbell the communication contract declares; no record lives under `.spx/`.
