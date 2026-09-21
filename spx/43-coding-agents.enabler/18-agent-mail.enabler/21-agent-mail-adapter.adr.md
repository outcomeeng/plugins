# Agent Mail Adapter

One Python 3.13+ standard-library adapter shipped inside `/operate-agent-mail` owns the complete public `am` command grammar for registration, send, inbox, and receipt, the project-key derivation from the repository's own common Git directory, the message-record field mapping onto the store's fields and back, response validation, and credential scrubbing. It exposes typed importable operations and a versioned JSON CLI; other coding-agents skills invoke `/operate-agent-mail` as a capability and never construct `am` argument vectors, read the store's database, or derive the project key themselves. No mail operation invokes an SPX command, so the capability depends on no SPX command surface.

## Rationale

One capability keeps store command knowledge and the record mapping testable and portable while preserving the skill-directory boundary plugin packaging requires. The project key is the repository's common Git directory because that directory is the one identity every checkout of a repository agrees on: a linked worktree, the pool's bare repository, and the pool's main checkout all resolve the same path, and deleting any individual checkout removes none of it. A key that names one checkout makes a repository's mail identity accidental and mortal — the checkout it names can be deleted while the registrations and message records keyed to it remain, and no later read can prove the project belongs to its own repository. Resolving the key inside the adapter also leaves the capability depending on no other command surface, so a retired argument vector elsewhere cannot break every mail operation. The message record carries fields the store lacks — a kind and a correlation — so the adapter maps them onto fields the store does carry, the subject prefix and the thread id, and reads them back, which keeps the record the unit of meaning while the store stays the unit of delivery. Registration returns a token that proves ownership of the name; the adapter removes it from every result because a token in a result reaches conversation transcripts and pane reads. The adapter binds to one store's command surface, so it stays plugin-local under `spx/12-shipped-scripting.adr.md`, whose extraction rule governs its generic logic.

## Invariants

- One source-owned operation registry covers register, send, inbox, and receipt.
- One project-key resolver maps the repository's absolute common Git directory, read for the adapter's own working directory, to the project key — normalized to an absolute path carrying no `.` or `..` segment, no repeated separator, and no trailing separator — or to the repository-unresolved result; it reads no working directory, environment variable, or parent path as a fallback.
- One record mapping is a bijection between a message record and the store fields the adapter writes: `correlation` to the thread id, `kind` to the subject prefix, `sender` to the sender, `recipient` to the recipients, `subject` to the subject remainder, `body` to the body, `ackRequired` to the acknowledgement requirement, and the store-assigned `id` to the record id.
- Every command execution is bounded, argument-vector based, fully reaped before return, and isolated from the adapter request stream.
- Store identities — message ids, thread ids, agent names, timestamps — remain byte-for-byte values from the public response.
- Captured usage and public-response fixtures identify their source-tool version pin: `am` 0.3.24 for store grammar and responses. A change to that pin, or a live probe that reports grammar or response drift, invalidates the affected fixtures and requires recapture before they serve as oracles. The project key has no captured oracle, because the checkout shapes a real repository takes are the oracle the resolver is read against.
- A registration result never carries the store's registration token.
- An absent `am` executable yields the store-unavailable result; a working directory that resolves to no repository, an absent Git executable, and a Git invocation that reports no absolute common directory each yield the repository-unresolved result. Neither result triggers a fallback.
- The adapter's external programs are the store CLI and Git; no operation's execution path reaches another program.

## Verification

### Testing

- ALWAYS: each source-owned operation maps a valid versioned request to the exact `am` argument vector for that operation under the resolved project key ([mapping])
- ALWAYS: a linked worktree, the pool's bare repository, and the pool's main checkout each map to one project key, that key being the pool's bare repository directory, and a working directory that is no repository maps to the repository-unresolved result ([mapping])
- ALWAYS: public `am` responses map to versioned source-owned results or named command failures without value rewriting ([mapping])
- ALWAYS: every message record maps onto the store fields and back to an equal record ([property])
- ALWAYS: a terminal handback record maps to exactly one terminal result carrying the complete initiating coordination reference; a matching repeated handback is idempotent and a conflicting terminal kind for one reference is rejected ([property])
- NEVER: a registration result carries the registration token the store returns ([compliance])
- ALWAYS: an absent `am` executable maps to the store-unavailable result and a working directory where no program resolves maps to the repository-unresolved result ([mapping])
- NEVER: an operation reaches a program outside the adapter's own command vectors — every operation completes where only those programs resolve ([compliance])
- NEVER: a shipped coding-agents Python script outside `/operate-agent-mail` constructs an `am` argument vector or derives a project key from Git state ([compliance])

### Audit

- NEVER: a shipped coding-agents skill outside `/operate-agent-mail` instructs a workflow to construct `am` commands, invoke `am` command help, or read the store's database ([audit])
- ALWAYS: the store subprocess boundary accepts a dependency-injected `CommandRunner` Protocol and the default runner uses null-device stdin, captured output, and a bounded timeout ([audit])
- ALWAYS: tests inject controlled runner implementations only under `/test` Stage 5 exception 1 (failure simulation) or exception 2 (interaction protocols) ([audit])
- ALWAYS: `/operate-agent-mail` owns all bundled-script access; composing skills invoke the capability through the skill surface rather than manufacturing a cross-skill filesystem path ([audit])
- NEVER: framework mocks or monkeypatching replace store behavior or the command-runner boundary ([audit])
- NEVER: the adapter owns another workflow's retry, checkpoint, persistence, result interpretation, or continuation decision ([audit])
