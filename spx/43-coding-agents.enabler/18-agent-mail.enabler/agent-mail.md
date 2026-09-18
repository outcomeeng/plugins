---
malleability: spec
---

# Agent Mail

PROVIDES a source-owned capability over the agent-mail store — registration, send, inbox, and acknowledgement — keyed by the repository the SPX CLI identifies
SO THAT coding-agent communication and orchestration workflows
CAN deliver and read message records between positively identified agents without constructing raw mail commands or inspecting Git state

## Assertions

### Mappings

- Registration, send, inbox, and acknowledgement each map one source-owned request shape to one mail command and checked result that preserves the store's message, thread, and agent identities verbatim
- A message record's declared fields map onto the store's fields and back without loss; a store limit never shapes the record
- A delegation request and its correlated terminal handback are message records; every terminal handback maps to exactly one completed, failed, rejected, or unavailable result carrying the complete initiating coordination reference
- The project key maps from the `worktree-pool` record's main checkout path in `spx diagnose --format json`, so every worktree of one pool resolves one mail project and a single checkout resolves itself

### Compliance

- ALWAYS: an absent store or an unavailable SPX diagnosis yields the source-owned unavailable result and no fallback
- NEVER: another shipped coding-agents script or skill constructs a raw mail command or derives the project key from Git state
