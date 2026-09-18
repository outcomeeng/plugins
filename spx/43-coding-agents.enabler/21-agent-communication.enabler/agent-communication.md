# Agent Communication

PROVIDES a source-owned message record, message vocabulary, and deterministic delivery requests for supported coding-agent environments
SO THAT inter-worktree coordination, officer orchestration, and other coding-agent workflows
CAN exchange facts, orders, questions, answers, and authority messages through complete participant identities without embedding environment transport mechanics in prompt prose

## Message record

A message between agent sessions is a message record with exactly these fields: `schema`, the record schema version; `id`, assigned by the store on delivery; `correlation`, the thread every reply to one exchange shares; `kind`; `sender` and `recipient`, each one agent-mail name; `subject`; `body`; and `ackRequired`. The kinds a sender writes are `order`, `fact`, `question`, `answer`, `delegation-request`, and the four terminal handbacks `delegation-completed`, `delegation-failed`, `delegation-rejected`, and `delegation-unavailable`; a read-back record whose subject carries no kind reads as `unclassified`. The agent-mail capability `spx/43-coding-agents.enabler/18-agent-mail.enabler` maps this record onto the store's fields and back without loss; a store limit never shapes the record.

A same-worktree delegation request carries the authority `spx/43-coding-agents.enabler/32-same-worktree-coordination.enabler` declares: the sender as the tracked-file and Git owner, the recipient's exact write scope, and no Git mutation by the recipient. The record renders that authority in its body, and a same-worktree delegation request without it reaches no record.

## Delivery routes

On the mail route, the record in the store is delivery: a message is delivered when the agent-mail capability's checked `send` result carries the record with its store-assigned `id`. The doorbell into the recipient's pane is exactly one line, `[<sender>] mail <id>`, and nothing else; no JSON and no record body reaches a pane, and no message record lives under `.spx/`. Acknowledgement is the recipient's separate receipt. A pane line counts as a sender's doorbell only when its sender resolves in the live agent inventory. A doorbell into a Prowl pane is submitted as a turn; its submission evidence is the Prowl trailing-Enter record.

On the Prowl submission route, the envelope of ownership proposals, one-way facts, acknowledgements, mutation-state reports, and mutation authorizations travels as the pane text, and delivery is checked public Prowl input evidence that trailing Enter submitted the turn.

## Assertions

### Mappings

- Every kind a sender writes maps to one message record carrying exactly the fields this node declares, and the agent-mail capability's `send` accepts that record unchanged ([test](tests/test_mail_record.mapping.l1.py))
- A checked succeeded `send` result of the agent-mail capability maps to the delivered mail result carrying the record's store-assigned id verbatim and the doorbell line `[<sender>] mail <id>`; a failed or unavailable capability result maps to `delivery-failed` with its status and detail preserved ([test](tests/test_mail_record.mapping.l1.py))
- Ownership proposals, one-way facts, acknowledgements, mutation-state reports, mutation authorizations, and delivery failures map to distinct source-owned message and result states ([test](tests/test_agent_message.mapping.l1.py))
- Every acknowledgement, mutation-state report, and mutation authorization preserves the complete active proposal reference, while every message that initiates a coordination reference receives a new UUID ([test](tests/test_agent_message.mapping.l1.py))

### Properties

- A rendered doorbell parses back to its sender and id ([test](tests/test_doorbell.property.l1.py))
- Every valid source-generated structured handback block is preserved unchanged in a production request ([test](tests/test_agent_message.property.l1.py))

### Compliance

- NEVER: a doorbell whose sender is absent from the supplied live inventory resolves to a sender ([test](tests/test_mail_delivery.compliance.l1.py))
- ALWAYS: a mail delivery result is delivered only with the capability's checked succeeded `send` result, and a doorbell is submitted only with checked Prowl input evidence that trailing Enter was sent; an unsubmitted doorbell is reported beside the delivered message, never as a failed delivery ([test](tests/test_mail_delivery.compliance.l1.py))
- NEVER: a same-worktree delegation request whose authority omits the sender as owner, names an empty write scope, or admits Git mutation reaches a record ([test](tests/test_mail_delivery.compliance.l1.py))
- NEVER: a message record or delivery record is written under `.spx/` or any other repository path; the store holds the record ([audit])
- NEVER: another shipped coding-agents skill instructs a workflow to send a doorbell that carries more than the one pointer line, or to place a record body in a pane ([audit])
- ALWAYS: delivery validates complete sender and recipient agent, environment endpoint, worktree, branch, repository, and applicable run identities before sending ([test](tests/test_agent_message.compliance.l1.py))
- ALWAYS: delegated-mutation proposals, state reports, and authorizations validate exact endpoint, worktree, branch, repository, full-HEAD, and status fields before transport ([test](tests/test_agent_message.compliance.l1.py))
- ALWAYS: delivery on the Prowl submission route requires checked public Prowl input evidence that trailing Enter submitted the turn; text remaining editable in the recipient pane is not delivery ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: successful delivery on either route establishes acknowledgement, agreement, ownership, or mutation authorization ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: communication targets by title, focus, position, inferred prose, or an undeclared fallback environment ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: a communication caller supplies a handback command, return pane fact, or cross-skill script path; production requests accept only the structured block returned by the environment capability ([test](tests/test_agent_message.compliance.l1.py))
- NEVER: communication skills construct environment command arguments directly; delivery routes through the source-owned environment capability ([audit])
