---
id: 01a0b229-e718-7996-988b-d465e39f898d
malleability: spec
---

# Agent Mail

PROVIDES a source-owned capability over the agent-mail store — registration, send, listing, read, and acknowledgement — keyed by the repository itself
SO THAT coding-agent communication and orchestration workflows
CAN deliver and read message records between positively identified agent sessions without constructing raw mail commands or resolving the project key themselves

This capability is an agent adapter: the configured way the agent harness lets one agent session communicate with another through the mail store. It governs no agent and no agent session of its own; a mail identity belongs to the agent session that registers it.

## Assertions

### Mappings

- Registration, send, listing, read, and acknowledgement each map one source-owned request shape to one store command and checked result that preserves the store's message, thread, and agent identities verbatim ([test](tests/test_agent_mail.mapping.l1.py))
- A listing request maps to the store's non-marking listing surface in unjudged mode, and a listing request carrying the all-records option maps to that surface's complete form ([test](tests/test_agent_mail.mapping.l1.py))
- A registration request carries no name, and the registration result carries the name the store assigned, verbatim ([test](tests/test_agent_mail.mapping.l1.py))
- The project key maps from the absolute canonical path of the repository's common Git directory, read for the adapter's own working directory with every variable removed that can make Git answer the location question from something other than that directory, so no value the caller inherited moves the answer — neither onto another repository nor away from its own — so every worktree of one pool, the pool's bare repository, and its main checkout resolve one mail project; a working directory that is no repository yields the unavailable result ([test](tests/test_agent_mail.mapping.l1.py))

### Properties

- The fields of the message record `spx/43-coding-agents.enabler/21-agent-communication.enabler` declares map onto the store's fields and back without loss, including a correlation the store's thread alphabet rejects, which round-trips through the adapter's encoding and decoding; a store limit never shapes the record ([test](tests/test_agent_mail.property.l1.py))
- An order to an agent session in an environment whose surface produces no pane-borne handback block, its delegation request, and its one correlated terminal handback are message records the communication node declares, delivered through this capability; every terminal handback maps to exactly one completed, failed, rejected, or unavailable result carrying the complete initiating coordination reference ([test](tests/test_agent_mail.property.l1.py))
- A second terminal handback for one coordination reference that carries the same terminal kind with different content is rejected as a conflicting handback, whose detail names the content difference ([test](tests/test_agent_mail.property.l1.py))

### Compliance

- ALWAYS: an absent store or an unresolvable repository yields the source-owned unavailable result and no fallback ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a mail operation invokes an SPX command ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: a registration result carries the registration token the store returns ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: an operation derives liveness, staleness, or session state from the store's per-agent activity timestamp ([test](tests/test_agent_mail.compliance.l1.py))
- ALWAYS: every emitted result carries the versioned result shape, including the failure whose input does not parse; a runner error of any class maps to the named unavailable or command-failed result; and a text argument carrying a NUL byte is rejected as an invalid schema before any command runs ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: another shipped coding-agents script constructs a raw mail command or derives the project key from Git state ([test](tests/test_agent_mail.compliance.l1.py))
- NEVER: another shipped coding-agents skill instructs a workflow to construct a raw mail command, invoke mail command help, or derive the project key from Git state ([audit])
- A read records that the recipient judged one message; it establishes nothing about the message's content ([audit])
- An acknowledgement is a read the sender can observe; it establishes no agreement, ownership, authorization, or acceptance of a proposal ([audit])
- ALWAYS: for every operation, the argument vector the adapter builds is accepted by the installed store, and every response the adapter parses is a shape that store emits ([probe](probes/installed-store/probe.md))
