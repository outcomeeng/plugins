---
id: 01a0b229-e718-7996-988b-d465e39f898d
malleability: spec
---

# Agent Mail

PROVIDES a source-owned capability over the agent-mail store — registration, send, list, read, acknowledge, and wait — keyed by the repository itself
SO THAT coding-agent communication and orchestration workflows
CAN deliver and read message records between positively identified agent sessions without constructing raw mail commands or resolving the project key themselves

This capability is an agent adapter: the configured way the agent harness lets one agent session communicate with another through the mail store. It governs no agent and no agent session of its own; a mail identity belongs to the agent session that registers it.

## Assertions

### Mappings

- Registration, send, list, read, and acknowledge each map one source-owned request shape to one store command and checked result, and wait maps one source-owned request shape to listing commands bounded by its timeout and one checked result; a registration request carries an optional display name that maps to the store's display name, an absent display name passes no display-name argument, a blank display name passes through as an empty value that clears the label, and every checked result preserves the store's labels verbatim beside its message, thread, and agent identities ([test](tests/test_agent_mail.mapping.l1.py))
- A wait request carrying an id and a timeout maps to the first record addressed to the requester whose store id exceeds that id, read or unread, carried as a listed record; to the named timeout result when no such record is present before the timeout; and to the named unreachable result when the listing cannot reach back to the id ([test](tests/test_agent_mail.mapping.l1.py))
- A listed record with or without a body and a send result carry the store's `sender_display_name` verbatim, null included, and a send result carries `to_display_names` as the mapping from each recipient stable name visible to the reader to its label; no label enters the message record ([test](tests/test_agent_mail.mapping.l1.py))
- The project key maps from the absolute canonical path of the repository's common Git directory, read for the adapter's own working directory with every variable removed that can make Git answer the location question from something other than that directory, so no value the caller inherited moves the answer — neither onto another repository nor away from its own — so every worktree of one pool, the pool's bare repository, and its main checkout resolve one mail project; a working directory that is no repository yields the unavailable result ([test](tests/test_agent_mail.mapping.l1.py))
- A list request maps to the store's non-marking listing surface in its unjudged mode, and a list request carrying the all-records option maps to that surface's complete form ([test](tests/test_agent_mail.mapping.l1.py))
- A read request maps to the store's recipient-only read command and an acknowledge request maps to the store's acknowledgement command, each for one message id; neither request maps to the other's command ([test](tests/test_agent_mail.mapping.l1.py))

### Properties

- The fields of the message record `spx/43-coding-agents.enabler/21-agent-communication.enabler` declares map onto the store's fields and back without loss, including a correlation outside the store's thread alphabet, which round-trips through the adapter's encoding and decoding; a store limit never shapes the record ([test](tests/test_agent_mail.property.l1.py))
- An order to an agent session in an environment whose surface produces no pane-borne handback block, its delegation request, and its one correlated terminal handback are message records the communication node declares, delivered through this capability; every terminal handback maps to exactly one completed, failed, rejected, or unavailable result carrying the complete initiating coordination reference ([test](tests/test_agent_mail.property.l1.py))
- A second terminal handback for one coordination reference that carries the same terminal kind with different content is rejected as a conflicting handback, whose detail names the content difference ([test](tests/test_agent_mail.property.l1.py))

### Scenarios

- Against the installed native `am` carrying position labels, a registration with a label followed by send, list, and doorbell shows the label on each surface, and a send right after startup and right after a label change authenticates ([probe](probes/position-labels/probe.md))
- ALWAYS: for every operation, the argument vector the adapter builds is accepted by the installed store, and every response the adapter parses is a shape that store emits ([probe](probes/installed-store/probe.md))

### Compliance

- ALWAYS: the adapter rejects an empty string in every text field of every operation except a registration's display name ([test](tests/test_agent_mail.compliance.l1.py))
- ALWAYS: an absent store or an unresolvable repository yields the source-owned unavailable result and no fallback ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a mail operation invokes an SPX command ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a registration result carries the registration token the store returns ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a mail operation selects, routes, or addresses by a label; the stable name or the store id selects every target ([test](tests/test_agent_mail.compliance.l1.py))
- ALWAYS: `/operate-agent-mail` instructs a position to register only its own identity, with its own label ([audit])
- NEVER: another shipped coding-agents script constructs a raw mail command, in argument-vector or shell-string form, or derives the project key from Git state ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: another shipped coding-agents skill instructs a workflow to construct a raw mail command, invoke mail command help, or derive the project key from Git state ([audit])
- NEVER: a wait request without a timeout runs a store command, and no store command inside a wait outlives the timeout ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a wait keeps a cursor, state file, or lock ([test](tests/test_agent_mail.compliance.l1.py))
- ALWAYS: every emitted result carries the versioned result shape, including the failure whose input does not parse, and a runner error of any class maps to the named store-unavailable or command-failed result ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a text argument carrying a NUL byte reaches a store command; the request is rejected as an invalid schema first ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a send whose correlation's written thread id exceeds the store's 128-character limit reaches a store command; the request is rejected as an invalid schema first ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: an operation derives liveness, staleness, or session state from the store's per-agent activity timestamp ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a list, a wait, or any operation other than the read and the acknowledgement changes a record's read state ([test](tests/test_agent_mail.compliance.l1.py))
- A read records, visibly to the recipient alone, that the recipient judged one message; it establishes nothing about the message's content ([audit:read-semantics])
- An acknowledgement is a read the sender can observe; it establishes no agreement, ownership, authorization, or acceptance of a proposal ([audit:acknowledgement-semantics])
