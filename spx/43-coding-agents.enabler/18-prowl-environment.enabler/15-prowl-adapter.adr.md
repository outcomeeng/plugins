# Prowl Environment Adapter

One Python 3.13+ standard-library adapter shipped inside `/operate-prowl` owns the complete public Prowl command grammar, response validation, participant projection, and delegation-state reduction. It exposes typed importable operations and a versioned JSON CLI; other coding-agents skills invoke `/operate-prowl` as a capability and never construct Prowl argument vectors or import its bundled script across skill boundaries.

## Rationale

One capability keeps Prowl command knowledge testable and portable while preserving the skill-directory boundary required by plugin packaging. A pure delegation reducer makes duplicate and conflicting terminal handbacks deterministic without making the adapter own workflow persistence or execution decisions.

## Invariants

- One source-owned operation registry covers list, agents, read, send, key, focus, tab create, tab close, pane close, and open.
- Every command execution is bounded, argument-vector based, fully reaped before return, and isolated from the adapter request stream unless the operation supplies explicit stdin.
- A delegation reducer maps one request and one terminal handback to a terminal state; a matching repeated handback is idempotent and a conflicting terminal handback is invalid.
- Prowl response identities, statuses, conclusions, exit codes, and result references remain byte-for-byte values from the public response.
- Focus, key injection, creation, and closure operations cannot construct an argument vector unless the request carries explicit mutation authorization.

## Verification

### Testing

- ALWAYS: each source-owned operation maps a valid versioned request to the exact Prowl argument vector for that operation ([mapping])
- ALWAYS: public Prowl responses map to versioned source-owned results or named schema and command failures without value rewriting ([conformance])
- ALWAYS: default subprocess execution maps absent operation input to null-device stdin and explicit operation input to an exact captured-text pipe ([conformance])
- ALWAYS: matching repeated terminal handbacks are idempotent and conflicting terminal kinds for one coordination reference are rejected ([property])
- ALWAYS: requests for focus, key injection, tab or pane creation, and tab or pane closure fail before command execution when mutation authorization is absent ([compliance])
- NEVER: a shipped coding-agents Python script outside `/operate-prowl` constructs a Prowl argument vector or invokes Prowl command help ([compliance])

### Audit

- NEVER: a shipped coding-agents skill outside `/operate-prowl` instructs a workflow to construct Prowl commands, invoke Prowl command help, or depend on an external environment-control skill ([audit])

- ALWAYS: the Prowl subprocess boundary accepts a dependency-injected `CommandRunner` Protocol and the default runner uses null-device stdin when input is absent, captured text input when present, captured output, and a bounded timeout ([audit])
- ALWAYS: tests inject controlled runner implementations only under `/test` Stage 5 exception 1 (failure simulation) or exception 2 (interaction protocols) ([audit])
- ALWAYS: `/operate-prowl` owns all bundled-script access; composing skills invoke the capability through the runtime skill surface rather than manufacturing a cross-skill filesystem path ([audit])
- NEVER: framework mocks or monkeypatching replace Prowl behavior or the command-runner boundary ([audit])
- NEVER: the adapter owns another workflow's retry, checkpoint, persistence, result interpretation, or continuation decision ([audit])
