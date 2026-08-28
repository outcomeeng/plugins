# Agent Communication

PROVIDES a source-owned message vocabulary and deterministic delivery requests for supported coding-agent environments
SO THAT inter-worktree coordination and other coding-agent workflows
CAN exchange facts and authority messages through complete participant identities without embedding environment transport mechanics in prompt prose

## Assertions

### Mappings

- Ownership proposals, one-way facts, acknowledgements, mutation-state reports, mutation authorizations, and delivery failures map to distinct source-owned message and result states ([test](tests/test_agent_message.mapping.l1.py))
- Every acknowledgement, mutation-state report, and mutation authorization preserves the complete active proposal reference, while every message that initiates a coordination reference receives a new UUID ([test](tests/test_agent_message.mapping.l1.py))
- A production request preserves one source-generated structured handback block containing semantic completion text, exact command, success criteria, retry policy, socket, and expected panes ([test](tests/test_agent_message.mapping.l1.py))

### Compliance

- ALWAYS: delivery validates complete sender and recipient agent, environment endpoint, worktree, branch, repository, and applicable run identities before sending ([test](tests/test_agent_message.compliance.l1.py))
- ALWAYS: delegated-mutation proposals, state reports, and authorizations validate exact endpoint, worktree, branch, repository, full-HEAD, and status fields before transport ([test](tests/test_agent_message.compliance.l1.py))
- ALWAYS: successful message delivery requires checked public Prowl input evidence that trailing Enter submitted the turn; text remaining editable in the recipient pane is not delivery ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: successful transport delivery establishes acknowledgement, agreement, ownership, or mutation authorization ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: communication targets by title, focus, position, inferred prose, or an undeclared fallback environment ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: a communication caller supplies a handback command, return pane fact, or cross-skill script path; production requests accept only the structured block returned by the environment capability ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: communication skills construct environment command arguments directly; delivery routes through the source-owned environment capability ([audit])
