---
id: 01a14494-efad-7c41-8082-1972cff8904a
malleability: spec
---

# Event Wait

PROVIDES one bounded wait over an agent session's mail, herdr-hosted agent session states, consumption-control alerts, and a clock instant, shipped as the `wait_event` script of the `/wait-for-event` skill
SO THAT coding-agent workflows
CAN wake on the first event any named source yields without a standing watcher, and learn of every source they cannot read

## Assertions

### Properties

- Every run that starts with a valid request ends by printing exactly one line, an event line, an unreadable-source line, or a timeout line, and exits ([test](tests/test_event_wait.property.l1.py))

### Mappings

- A mail source carrying an id maps the agent-mail capability's wait result to an event line carrying the record's id, sender, kind, and subject, its timeout result to no event, and its unreachable or unavailable result to an unreadable-source line ([test](tests/test_event_wait.mapping.l1.py))
- A pane source naming herdr-hosted agent sessions, each with the state the caller last handled, maps to an event line naming the first session whose state, as the herdr environment capability projects it, differs from the state passed; a session absent from the inventory, an incomplete item, or an unavailable or ambiguous herdr result maps to an unreadable-source line ([test](tests/test_event_wait.mapping.l1.py))
- A pane source naming a pane in an environment whose capability projects no agent session state maps to an unreadable-source line naming that environment ([test](tests/test_event_wait.mapping.l1.py))
- A spend source carrying an instant maps the first alert record the consumption-control detector recorded after that instant to an event line carrying its identity and signal, and an unreadable detector state root to an unreadable-source line ([test](tests/test_event_wait.mapping.l1.py))
- A clock source carrying an instant before the timeout maps the arrival of that instant to a clock event line ([test](tests/test_event_wait.mapping.l1.py))
- A request is one JSON document on standard input naming its sources and its timeout, the request form the agent-mail and herdr adapters take; a document that is not one JSON object, or that names an unknown source kind, maps to the invalid-request line ([test](tests/test_event_wait.mapping.l1.py))
- The event line, the unreadable-source line, the timeout line, and the invalid-request line map to distinct source-owned line forms, each one JSON object on one line whose `kind` field names its form, the event and timeout lines exiting zero and the other two exiting nonzero ([test](tests/test_event_wait.mapping.l1.py))

### Compliance

- A request without a timeout, or with a timeout that is not positive, prints one invalid-request line and exits before reading any source ([test](tests/test_event_wait.compliance.l1.py))
- NEVER: a run keeps a cursor, state file, or lock, sends mail, marks mail read, records a receipt, or prompts or keys a pane ([test](tests/test_event_wait.compliance.l1.py))
- NEVER: a run outlives its timeout, starts a background process, or loops after printing its line ([test](tests/test_event_wait.compliance.l1.py))
- ALWAYS: `wait_event` reads mail through the agent-mail capability, agent session states through the herdr environment capability, and alerts through the consumption-control read, each by a `__file__`-relative import inside the plugin, and constructs no raw mail, herdr, or consumption-control command ([audit])
- ALWAYS: `/wait-for-event` documents the request, which the caller writes to a payload file in its scratch directory and supplies through an input redirect, its required timeout, the id, states, and instants the caller passes from the last event it handled, and the four line forms ([audit])
