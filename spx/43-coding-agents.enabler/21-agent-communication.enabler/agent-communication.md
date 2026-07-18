# Agent Communication

PROVIDES a source-owned message vocabulary and deterministic delivery adapter for supported coding-agent terminals
SO THAT inter-worktree coordination and other coding-agent workflows
CAN exchange facts and requests through explicit Prowl pane identities without embedding transport mechanics in prompt prose

## Assertions

### Mappings

- Supported, unsupported, and ambiguous caller evidence maps to `prowl-pane`, `unsupported-terminal`, or `caller-ambiguous` without fallback ([test](tests/test_agent_message.mapping.l1.py))
- Ownership proposals, one-way facts, acknowledgements, mutation-state reports, mutation authorizations, and delivery failures map to distinct source-owned message and result states ([test](tests/test_agent_message.mapping.l1.py))
- Every acknowledgement, mutation-state report, and mutation authorization preserves the complete active proposal reference, while every message that initiates a coordination reference receives a new UUID ([test](tests/test_agent_message.mapping.l1.py))

### Compliance

- ALWAYS: delivery validates complete sender and recipient agent, pane, worktree, branch, repository, and applicable run identities before sending ([test](tests/test_agent_message.compliance.l1.py))
- ALWAYS: message delivery passes the rendered envelope to `prowl send` over subprocess stdin and reports the checked command result ([test](tests/test_agent_message.compliance.l1.py))
- ALWAYS: delegated-mutation proposals, state reports, and authorizations validate exact pane, worktree, branch, repository, full-HEAD, and status fields against the live sender or recipient identity before transport ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: successful transport delivery establishes acknowledgement, agreement, ownership, or mutation authorization ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: communication targets by title, focus, position, inferred prose, or a non-Prowl fallback channel ([test](tests/test_agent_message.compliance.l1.py))
