# Agent Mail Adapter

CONSTRAINS every access to the agent-mail store from the coding-agents plugin
TO one Python 3.13+ standard-library adapter shipped inside `/operate-agent-mail`, which owns the complete public `am` command grammar for registration, the registrations listing, send, list, read, acknowledge, and wait, the project-key resolution, which keys each repository's registrations and message records to the absolute canonical path of the common Git directory of the repository an operation acts on, the message-record field mapping and correlation encoding, the pass-through of position labels, response validation, and credential scrubbing, behind typed importable operations and a versioned JSON CLI
SO THAT one script carries every store command and record mapping, every checkout of a repository resolves one mail project, and no mail operation depends on another command surface

## Verification

### Test.Mapping: operation-commands

Each source-owned operation maps a valid versioned request to one store command under the resolved project key, and no operation maps to another operation's command.

| Case             | Store command                                                                                      |
| ---------------- | -------------------------------------------------------------------------------------------------- |
| register         | the store's registration command, with `display_name` only when the request carries a display name |
| registrations    | the store's agent-listing command                                                                  |
| send             | the store's send command carrying the record's mapped fields                                       |
| list             | the store's non-marking listing surface in its unjudged form, `am robot inbox --unread`            |
| list-all-records | the complete form of the same surface, `am robot inbox --all`                                      |
| read             | the store's recipient-only read command for one message id, `am mail read`                         |
| acknowledge      | the store's acknowledgement command for one message id, `am mail ack`                              |
| wait             | the complete form of the listing surface, `am robot inbox --all`, repeated until the wait ends     |

### Test.Mapping: repository-key

A request's optional `repository` maps to the project key of the repository it names, read by the same lookup the adapter runs in its own working directory, and the result's project key reports the store the operation acted on.

| Case                 | Project key                                                 |
| -------------------- | ----------------------------------------------------------- |
| no-repository        | the key of the adapter's own working directory              |
| named-checkout       | the key the adapter derives when it stands in that checkout |
| project-key-option   | the key of the path `--repository <absolute-path>` names    |
| named-non-repository | the repository-unresolved result                            |

### Test.Mapping: pool-keys

Every checkout shape of one worktree pool maps to one project key, the pool's bare repository directory, whether the adapter stands in it or a request names it.

| Case            | Project key                          |
| --------------- | ------------------------------------ |
| linked-worktree | the pool's bare repository directory |
| bare-repository | the pool's bare repository directory |
| main-checkout   | the pool's bare repository directory |
| symlinked-route | the key of the checkout it reaches   |
| no-repository   | the repository-unresolved result     |

### Test.Mapping: location-variables

Each variable that Git's own behaviour confirms moves a lookup's answer off the invoking working directory, and the complete confirmed set together, maps to no change in the resolved key; the domain is read from Git, never from the adapter's removal list.

| Case                      | Resolved key                     |
| ------------------------- | -------------------------------- |
| names-another-repository  | the working directory's own key  |
| bounds-discovery-above    | the working directory's own key  |
| complete-confirmed-set    | the working directory's own key  |
| working-directory-no-repo | the repository-unresolved result |

### Test.Mapping: record-fields

One record mapping is a bijection between a message record and the store fields the adapter writes.

| Case         | Store field                                     |
| ------------ | ----------------------------------------------- |
| correlation  | the thread id, through the correlation encoding |
| kind         | the subject prefix                              |
| sender       | the sender                                      |
| recipient    | the recipients                                  |
| subject      | the subject remainder                           |
| body         | the body                                        |
| ack-required | the acknowledgement requirement                 |
| id           | the record id the store assigns                 |

### Test.Mapping: thread-ids

A correlation inside the store's thread alphabet — an alphanumeric first character, then letters, digits, `.`, `_`, or `-`, at most 128 characters in all — that does not begin with `xc-` is written unchanged, and every other correlation is written as `xc-` followed by its UTF-8 bytes, each byte outside letters, digits, `.`, and `-` spelled as `_` and two lowercase hex digits.

| Case               | Thread id                             |
| ------------------ | ------------------------------------- |
| inside-alphabet    | the correlation unchanged             |
| begins-with-escape | the escaped form                      |
| outside-alphabet   | the escaped form                      |
| foreign-thread     | read back verbatim as the correlation |

### Test.Mapping: labels

The store's position labels pass through verbatim beside the message record, null included, and never enter the record or its mapping.

| Case                  | Result field                                                                                       |
| --------------------- | -------------------------------------------------------------------------------------------------- |
| listed-record         | `sender_display_name`, with or without a body                                                      |
| send-result           | `sender_display_name`, and `to_display_names` from each visible recipient stable name to its label |
| registration-label    | the request's display name passed as the store's `display_name`                                    |
| registration-no-label | no display-name argument                                                                           |
| registrations-listing | each registration's stable name and its label                                                      |

### Test.Mapping: wait-outcomes

A wait request carrying an id and a timeout maps to the first record addressed to the requester whose store id exceeds that id, read or unread, or to a named outcome.

| Case                | Outcome                                         |
| ------------------- | ----------------------------------------------- |
| unread-record-above | `received`, with that record as a listed record |
| read-record-above   | `received`, with that record as a listed record |
| none-before-timeout | `timeout`                                       |
| listing-short       | `unreachable`, never a later record             |

### Test.Mapping: ack-required

A listed record's acknowledgement status maps to `ackRequired` true when the store shows an acknowledgement required, whether still owed or given, and to false for every other status.

| Case     | ackRequired |
| -------- | ----------- |
| required | true        |
| pending  | true        |
| acked    | true        |
| none     | false       |

### Test.Mapping: responses

Public `am` responses map to versioned source-owned results or named failures, and store identities — message ids, thread ids, agent names, timestamps — stay byte-for-byte values from the response, except that a thread id the adapter wrote in its encoded form reads back as the correlation it encodes.

| Case                | Result                           |
| ------------------- | -------------------------------- |
| store-success       | a succeeded result               |
| store-failure       | the command-failed result        |
| absent-store        | the store-unavailable result     |
| no-program-resolves | the repository-unresolved result |

### Test.Compliance: repository selection

- one-resolver: ALWAYS: one project-key resolver maps the repository's absolute common Git directory, read for the working directory of the repository a request names or for the adapter's own working directory when it names none, to the project key or to the repository-unresolved result, and reads no other working directory, environment variable, or parent path in its place.
- repository-shape: NEVER: a request whose `repository` is not an absolute path string reaches a store command; it is rejected as an invalid schema first.
- unresolved-no-fallback: ALWAYS: a named path that resolves to no repository yields the repository-unresolved result, and a named path never yields the key of the adapter's working directory.
- no-overlay: NEVER: the adapter reads an overlay or configuration to select a repository; a workflow that selects its repository from declared configuration does so before it calls the capability.
- key-normalized: ALWAYS: the resolver normalizes the lookup's answer textually to an absolute path with no `.` or `..` segment, no repeated separator, and no trailing separator, and never re-resolves a symlink.

### Test.Compliance: requests

- operation-registry: ALWAYS: one source-owned operation registry covers register, registrations, send, list, read, acknowledge, and wait, and no operation keeps the names inbox or receipt.
- request-shapes: ALWAYS: a list request carries `agent` and optional `allRecords`, `includeBodies`, and `limit`; a read request and an acknowledge request each carry `agent` and `messageId`; a registrations request carries only the optional `repository`; and a request carrying `unreadOnly` is rejected as an invalid schema.
- nul-rejected: NEVER: a text argument carrying a NUL byte reaches a store command; the request is rejected as an invalid schema first.
- thread-length: NEVER: a send whose correlation's written thread id exceeds 128 characters reaches a store command; the request is rejected as an invalid schema first.
- versioned-result: ALWAYS: every emitted result carries the versioned result shape, including the failure whose input does not parse, and a runner error of any class maps to the named store-unavailable or command-failed result.
- list-bodies: ALWAYS: a list request that omits `includeBodies` maps to the listing command with `--include-bodies`, and only a list request carrying `includeBodies` false maps to the form without it.

### Test.Compliance: identity

- no-register-on-behalf: NEVER: the adapter registers an identity on a caller's behalf; a send from a name the named store does not hold returns the store's failure as the command-failed result.
- no-token: NEVER: a registration result carries the registration token the store returns.
- no-credential-refresh: ALWAYS: after a registration the next send authenticates through the credential the store CLI stores at registration, and the adapter makes no credential refresh call.
- no-label-routing: NEVER: an operation selects, routes, or addresses a target by a label; the stable name or the store id selects every target.

### Test.Compliance: read state and waits

- read-state: NEVER: a list, a registrations listing, a wait, or any operation other than the read and the acknowledgement changes a record's read state.
- registrations-read-only: NEVER: a registrations request changes a registration, a record, or a read state.
- wait-timeout: NEVER: a wait request without a timeout runs a store command, and no store command inside a wait outlives the time that remains.
- wait-stateless: NEVER: a wait keeps a cursor, state file, or lock; the caller passes the last id it handled.
- wait-interval: ALWAYS: a wait lists at its start and then at most once per the adapter's wait interval until its first record or its timeout.

### Test.Compliance: boundary

- program-boundary: NEVER: an operation reaches a program other than the store CLI and Git; every operation completes where only those programs resolve.
- no-liveness: NEVER: an operation derives liveness, staleness, or session state from the store's per-agent activity timestamp.
- no-raw-mail-elsewhere: NEVER: a shipped coding-agents Python script outside `/operate-agent-mail` constructs an `am` argument vector or a shell-string `am` command, or derives a project key from Git state.

### Test.Property: record mapping

- record-round-trip: Every message record maps onto the store fields and back to an equal record.
- correlation-round-trip: Every correlation round-trips through the encoding and decoding to itself, every thread id the adapter writes lies inside the store's thread alphabet, and no encoded form equals a correlation the adapter writes unencoded.

### Test.Property: handbacks

- conflicting-handback: A second terminal handback for one correlation that carries the same terminal kind with different content is rejected as a conflicting handback whose detail names the content difference.

### Test.Conformance: fixtures

- fixture-provenance: Each captured usage and public-response fixture names the tool and the build that produced it, and the build it names is the native `am` binary the attested installed-store probe run drove, as that run records it: the path of the executable and the version and capabilities the CLI reports, with a source commit or a SHA-256 only when the run reads one.

### Audit

- injected-runner: ALWAYS: the store subprocess boundary accepts a dependency-injected `CommandRunner` Protocol, and the default runner runs bounded, argument-vector commands with null-device stdin and captured output, fully reaped before return.
- runner-exceptions: ALWAYS: tests inject controlled runner implementations only under `/test` Stage 5 exception 1 (failure simulation) or exception 2 (interaction protocols).
- boundary-stand-in: ALWAYS: a controlled stand-in at the process boundary, an executable on a restricted search path, stands only as exception 2 evidence for the boundary itself and never stands in for store behavior, which the captured responses own.
- no-mocks: NEVER: framework mocks or monkeypatching replace store behavior or the command-runner boundary.
- fixture-recapture: ALWAYS: a change to the build the attested installed-store probe run records, or a probe run that reports grammar or response drift, invalidates the affected fixtures until a probe run recaptures them, and the project key has no captured oracle.
- no-foreign-ownership: NEVER: the adapter owns another workflow's retry, checkpoint, persistence, result interpretation, or continuation decision.
- no-skill-raw-mail: NEVER: a shipped coding-agents skill outside `/operate-agent-mail` instructs a workflow to construct `am` commands, invoke `am` command help, or read the store's database.
- skill-surface-access: ALWAYS: `/operate-agent-mail` owns all bundled-script access, and composing skills invoke the capability through the skill surface rather than manufacturing a cross-skill filesystem path.
- read-semantics: ALWAYS: a read records, visibly to the recipient alone, that the recipient judged one message, and establishes nothing about the message's content.
- acknowledgement-semantics: ALWAYS: an acknowledgement is a read the sender can observe, and establishes no agreement, ownership, authorization, or acceptance of a proposal.
- wait-interval-value: ALWAYS: the adapter's wait interval is 30 seconds.
