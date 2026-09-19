# Message Record and Delivery Routes

One Python 3.13+ standard-library script shipped inside `/message-agents` declares the message record this node owns — `schema`, `id`, `correlation`, `kind`, `sender`, `recipient`, `subject`, `body`, and `ackRequired`, with the kinds a sender writes — and validates every delivery result on the node's two routes: the mail route, where a checked `send` result of the agent-mail capability carrying a store-assigned `id` is delivery and the doorbell is the one pane line `[<sender>] mail <id>`, and the Prowl submission route, where checked public Prowl input evidence that trailing Enter submitted the turn is delivery. The script reads each capability's public result by its own field constants, executes no command, opens no store, and imports no other skill's script; the agent-mail adapter maps the record this node declares onto the store's fields and reads them back.

## Rationale

The record is the unit of meaning and the store is the unit of delivery, so the node that owns communication semantics declares the record and the capability that owns the store maps it. The declaration lives in this node's script as named constants because the field names and kinds are values the spec tree declares; the adapter's mapping table carries the same names as its compliance with that declaration, and their agreement is audit evidence under `spx/12-shipped-scripting.adr.md`, never a second declaration a test could restate. A `__file__`-relative import of the adapter is rejected: `spx/43-coding-agents.enabler/18-agent-mail.enabler/21-agent-mail-adapter.adr.md` makes `/operate-agent-mail` the owner of all bundled-script access, and a script that reaches across skill directories manufactures the cross-skill path that decision forbids. The script validates the agent-mail `send` result and the Prowl `send` result by the same means, its own field constants over each capability's public result, so both routes are checked the same way and neither route needs a subprocess, a store handle, or a mock.

The doorbell carries no payload because a pane collapses a pasted block to a placeholder the sender cannot verify, while a one-line pointer arrives intact; the record in the store is what the recipient reads. A doorbell into a Prowl pane is submitted as a turn, and its submission evidence is the Prowl trailing-Enter record, so a pointer that remains editable in the recipient's pane is reported as an unsubmitted doorbell beside a delivered message, never as a failed delivery. Parsing a doorbell resolves its sender against an inventory the caller supplies from the live environment, because a line in a pane proves nothing about who wrote it. The same-worktree authority a delegation request carries — the sender as tracked-file and Git owner, no write scope, no Git mutation — is validated as structured fields before the body is rendered, because a rule that lives only in prose is one a recipient can miss; the rendered body keeps it readable. The authority names no write scope because the recipient's result is the handback record's body, and any draft artifact home belongs to the `spx` CLI, not to a plugin-shipped script.

## Invariants

- Every record the script builds for the mail route is a record the agent-mail capability's `send` accepts unchanged.
- The doorbell text the script renders from a delivered result parses back to the same sender and id.
- A delivery result on either route carries `acknowledged`, `agreed`, and `ownershipEstablished` as false.
- A delivered mail result carries the store-assigned `id` verbatim from the capability's result and no other id.

## Verification

### Testing

- ALWAYS: every kind a sender writes maps to one record carrying exactly the fields this node declares, and the agent-mail capability's `send` accepts that record unchanged ([mapping])
- ALWAYS: a checked succeeded `send` result of the agent-mail capability maps to the delivered mail result carrying the record's store-assigned id verbatim and the doorbell line `[<sender>] mail <id>`; a failed or unavailable result maps to `delivery-failed` with the capability's status and detail preserved ([mapping])
- ALWAYS: a rendered doorbell parses back to its sender and id ([property])
- NEVER: a doorbell whose sender is absent from the supplied inventory resolves to a sender ([compliance])
- NEVER: a delivered result on either route establishes acknowledgement, agreement, ownership, or mutation authorization ([compliance])
- NEVER: a same-worktree delegation request whose authority omits the sender as owner, names a write scope, or admits Git mutation reaches a record ([compliance])
- NEVER: a mail delivery result is delivered without the capability's checked succeeded `send` result, and a doorbell is submitted without checked Prowl input evidence that trailing Enter was sent ([compliance])

### Audit

- ALWAYS: the record field names and kinds this node's script declares equal the ones this node's spec declares, and the agent-mail adapter's record mapping carries the same names as its compliance — that agreement is audit evidence, never a value a test or harness restates ([audit])
- ALWAYS: the script reads each capability's public result by its own field constants and validates it structurally before deriving a delivery result ([audit])
- NEVER: the script executes a subprocess, reads the mail store, constructs a mail or environment command, or imports another skill's bundled script ([audit])
- NEVER: a message record or delivery record is written under `.spx/` or any other repository path; the store holds the record and the script holds no persistence ([audit])
- NEVER: a caller supplies the doorbell text, the store-assigned id, or a delivery status; each derives from the capability's checked result ([audit])
- ALWAYS: the mail route and the Prowl submission route are selected by the caller's request shape, and the script rejects a request that mixes fields of both ([audit])
