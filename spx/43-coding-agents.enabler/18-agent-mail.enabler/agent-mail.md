---
id: 01a0b229-e718-7996-988b-d465e39f898d
malleability: spec
---

# Agent Mail

PROVIDES a source-owned capability over the agent-mail store — registration, send, inbox, and receipt — keyed by the repository the SPX CLI identifies
SO THAT coding-agent communication and orchestration workflows
CAN deliver and read message records between positively identified agent sessions without constructing raw mail commands or inspecting Git state

This capability is an agent adapter: the configured way the agent harness lets one agent session communicate with another through the mail store. It governs no agent and no agent session of its own; a mail identity belongs to the agent session that registers it.

## Assertions

### Mappings

- Registration, send, inbox, and receipt each map one source-owned request shape to one mail command and checked result that preserves the store's message, thread, and agent identities verbatim
- The fields of a message record map onto the store's fields and back without loss; a store limit never shapes the record
- A receipt is the recipient's record in the store that it has read one message; it establishes nothing about the message's content, and no message state — agreement, ownership, authorization, or the acknowledgement of a proposal — derives from it
- An order to an agent session in an environment whose surface produces no pane-borne handback block, its delegation request, and its one correlated terminal handback are message records of this capability; every terminal handback maps to exactly one completed, failed, rejected, or unavailable result carrying the complete initiating coordination reference
- The project key maps from the `worktree-pool` record's main checkout path in `spx diagnose --format json`, so every worktree of one pool resolves one mail project; a diagnosis that reports no main checkout path yields the unavailable result

### Compliance

- ALWAYS: an absent store or an unavailable SPX diagnosis yields the source-owned unavailable result and no fallback
- NEVER: another shipped coding-agents script or skill constructs a raw mail command or derives the project key from Git state
