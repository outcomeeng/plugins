---
id: 01a0b229-e718-7996-988b-d465e39f898d
malleability: spec
---

# Agent Mail

PROVIDES a source-owned capability over the agent-mail store — registration, send, inbox, and receipt — keyed by the repository itself
SO THAT coding-agent communication and orchestration workflows
CAN deliver and read message records between positively identified agent sessions without constructing raw mail commands or resolving the project key themselves

This capability is an agent adapter: the configured way the agent harness lets one agent session communicate with another through the mail store. It governs no agent and no agent session of its own; a mail identity belongs to the agent session that registers it.

## Assertions

### Mappings

- Registration, send, inbox, and receipt each map one source-owned request shape to one mail command and checked result; a registration request carries an optional display name that maps to the store's display name, and every checked result preserves the store's labels verbatim beside its message, thread, and agent identities ([test](tests/test_agent_mail.mapping.l1.py))
- An inbox item with or without a body and a send result carry the store's `sender_display_name` verbatim, null included, and a send result carries `to_display_names` as the mapping from each recipient stable name visible to the reader to its label; no label enters the message record ([test](tests/test_agent_mail.mapping.l1.py))
- The project key maps from the absolute canonical path of the repository's common Git directory, read for the adapter's own working directory with every variable removed that can make Git answer the location question from something other than that directory, so no value the caller inherited moves the answer — neither onto another repository nor away from its own — so every worktree of one pool, the pool's bare repository, and its main checkout resolve one mail project; a working directory that is no repository yields the unavailable result ([test](tests/test_agent_mail.mapping.l1.py))

### Properties

- The fields of the message record `spx/43-coding-agents.enabler/21-agent-communication.enabler` declares map onto the store's fields and back without loss; a store limit never shapes the record ([test](tests/test_agent_mail.property.l1.py))
- An order to an agent session in an environment whose surface produces no pane-borne handback block, its delegation request, and its one correlated terminal handback are message records the communication node declares, delivered through this capability; every terminal handback maps to exactly one completed, failed, rejected, or unavailable result carrying the complete initiating coordination reference ([test](tests/test_agent_mail.property.l1.py))

### Scenarios

- Against the installed native `am` carrying position labels, a registration with a label followed by send, inbox, and doorbell shows the label on each surface, and a send right after startup and right after a label change authenticates ([probe](probes/position-labels/probe.md))

### Compliance

- ALWAYS: an absent store or an unresolvable repository yields the source-owned unavailable result and no fallback ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a mail operation invokes an SPX command ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a registration result carries the registration token the store returns ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a mail operation selects, routes, or addresses by a label; the stable name or the store id selects every target ([test](tests/test_agent_mail.compliance.l1.py))
- ALWAYS: `/operate-agent-mail` instructs a position to register only its own identity, with its own label ([audit])
- NEVER: another shipped coding-agents script constructs a raw mail command or derives the project key from Git state ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: another shipped coding-agents skill instructs a workflow to construct a raw mail command, invoke mail command help, or derive the project key from Git state ([audit])
- A receipt is the recipient's record in the store that it has read one message; it establishes nothing about the message's content, and no message state — agreement, ownership, authorization, or the acknowledgement of a proposal — derives from it ([audit])
