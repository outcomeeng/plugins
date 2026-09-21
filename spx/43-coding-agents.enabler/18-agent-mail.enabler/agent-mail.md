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

- Registration, send, and receipt each map one source-owned request shape to one mail command and checked result; inbox maps its request to the store's listing command and returns the recipient's records, preserving the store's message, thread, and agent identities verbatim ([test](tests/test_agent_mail.mapping.l1.py))
- The project key maps from the `worktree-pool` record's main checkout path in `spx diagnose --format json`, so every worktree of one pool resolves one mail project; a diagnosis that reports no main checkout path yields the unavailable result ([test](tests/test_agent_mail.mapping.l1.py))

### Properties

- The fields of the message record `spx/43-coding-agents.enabler/21-agent-communication.enabler` declares map onto the store's fields and back without loss; a store limit never shapes the record ([test](tests/test_agent_mail.property.l1.py))
- An order to an agent session in an environment whose surface produces no pane-borne handback block, its delegation request, and its one correlated terminal handback are message records the communication node declares, delivered through this capability; every terminal handback maps to exactly one completed, failed, rejected, or unavailable result carrying the complete initiating coordination reference ([test](tests/test_agent_mail.property.l1.py))

### Compliance

- ALWAYS: an absent store or an unavailable SPX diagnosis yields the source-owned unavailable result and no fallback ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a registration result carries the registration token the store returns ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: another shipped coding-agents script constructs a raw mail command or derives the project key from Git state ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: another shipped coding-agents skill instructs a workflow to construct a raw mail command, invoke mail command help, or derive the project key from Git state ([audit])
- A receipt is the recipient's record in the store that it has read one message; it establishes nothing about the message's content, and no message state — agreement, ownership, authorization, or the acknowledgement of a proposal — derives from it ([audit])
