---
name: operate-agent-mail
description: >-
  ALWAYS invoke this skill when a workflow registers a mail identity, sends a message record, lists a recipient's records, or reads or acknowledges a message in the agent-mail store. NEVER construct an `am` command or derive the mail project key without this skill.
argument-hint: "<versioned JSON request> | project-key"
allowed-tools: Bash(printf:*), Bash(python3 "${SKILL_DIR}/scripts/agent_mail.py":*)
---

<objective>
A versioned JSON agent-mail result — a registered identity carrying its store-assigned name, a delivered record carrying its store-assigned id, the recipient's records, or the message the recipient read or acknowledged — under the project key the repository names, or that key alone from the `project-key` form, with every store identity preserved verbatim.
</objective>

<operation_surface>

**Source-owned** means declared and checked by the bundled adapter itself: the operation names, the request and result shapes, and the record fields below are the adapter's own, and it rejects anything outside them. The adapter's own failure details use the term in the same sense.

The source-owned request operations, each submitted as a versioned JSON request to `run`:

| Operation     | Arguments                                                | Result data                                                |
| ------------- | -------------------------------------------------------- | ---------------------------------------------------------- |
| `register`    | `program`, `model`; optional `task`                      | `agent`, the name the store assigned, and the store's `id` |
| `send`        | `record`                                                 | the `record` with its store-assigned `id`                  |
| `list`        | `agent`; optional `allRecords`, `includeBodies`, `limit` | `records` read back for that recipient                     |
| `read`        | `agent`, `messageId`                                     | the `agent` and `messageId` the store marked read          |
| `acknowledge` | `agent`, `messageId`                                     | the `agent` and `messageId` the store marked acknowledged  |

One further form answers outside the request shape, so it takes no JSON request and the request-building steps of `<workflow>` do not reach it. A `run` request naming it is rejected as `operation-unavailable`; its command and both of its answers are in `<invocation_forms>`.

| CLI form      | Arguments | Result data  |
| ------------- | --------- | ------------ |
| `project-key` | none      | `projectKey` |

The operation rules:

- **Registration carries no name.** A `register` request never names the agent; the store assigns the name from its own vocabulary, and the result's `agent` carries it verbatim as the identity every later operation addresses.
- **Listing marks nothing.** `list` returns the recipient's records the recipient has not yet read or acknowledged, and changes no record's read state.
- **All records.** `list` with `allRecords: true` returns every record the recipient holds, including the ones already read or acknowledged, so a session that takes over a mail identity reads back what its predecessor marked read.
- **Bodies.** `list` returns each record's `body` only with `includeBodies: true`. Without it, every record reads back with `body: ""`, so an empty `body` from such a listing says nothing about the message; list again with `includeBodies: true` before acting on or relaying a record's content.
- **Read.** `read` marks one message read, visible to the recipient alone.
- **Acknowledge.** `acknowledge` is a read the sender can observe.
- **Only two operations change read state.** `read` and `acknowledge` change a record's read state; no other operation does.
- **Bounds.** `limit` is an integer from 1 to 1000, and `messageId` is the integer `id` a record carries, from 1 to 1000000000; a value outside either range is rejected with `invalid-schema` before any command runs.
- **Store ids.** Every `id` a result carries — a record's and the registered agent's — is an integer from 1 to 1000000000; a store response whose `id` is absent or outside that range fails as `invalid-schema`.
- **No NUL character.** A text argument or record field carrying a NUL character is rejected with `invalid-schema` before any command runs.

The record rules:

- **Fields.** A `record` carries exactly `schema` (`1`), `kind`, `correlation`, `sender`, `recipient`, `subject`, `body`, and `ackRequired`; the store assigns `id` on delivery.
- **Kinds a sender writes.** `order`, `fact`, `question`, `answer`, `delegation-request`, and the four terminal handbacks `delegation-completed`, `delegation-failed`, `delegation-rejected`, and `delegation-unavailable`.
- **Kinds read back.** On read-back the adapter reports each record's kind as one of the kinds a sender writes or as `unclassified`, and `subject` carries the text to use in either case. Never derive a kind from a subject: the adapter owns the prefix it writes and the conditions a row meets to classify, and a row missing any of them reads as `unclassified` with its subject verbatim.
- **Mapping.** The adapter maps `correlation` onto the store's thread, `kind` onto a subject prefix, and `ackRequired` onto the store's acknowledgement requirement, and reads each back; a store limit never shapes the record.
- **Correlation.** Every correlation survives the round trip unchanged. The adapter encodes a correlation the store's thread alphabet rejects and decodes it on read, so the store's own thread display shows the encoded form; read the correlation from the adapter's result, never from the store's display. A correlation whose written thread would exceed the store's 128-character limit is rejected with `invalid-schema` before any command runs.
- **One recipient.** `recipient` names one agent. A value carrying the store's `,` separator is rejected with `invalid-schema` before any command runs.
- **Foreign rows.** A row another sender wrote reads back rather than failing the listing: without a thread it reads with `correlation: null` and kind `unclassified`, and an acknowledgement status other than `required` or `acked` reads as `ackRequired: false`.
- **Malformed rows.** A row without the store's `id`, `from`, or `subject` key is a malformed store response and fails the listing as `invalid-schema`.

The project-key rules:

- **The key.** The project key is the normalized absolute path of the repository's own common Git directory, the one `projectKey` every result carries.
- **One project per repository.** Every worktree of one pool, the pool's bare repository, and the pool's main checkout resolve one key, and no checkout's deletion removes it.
- **Own working directory only.** The adapter reads the key for its own working directory before every operation, so run it from a checkout of the repository whose mail project is meant; no environment variable, parent path, or other working directory redirects it to another project.
- **Unresolved.** A working directory that is no repository, an absent Git executable, and a lookup reporting no absolute directory each yield `repository-unresolved`, with no fallback.

</operation_surface>

<workflow>

1. Read `$ARGUMENTS` as exactly one of two inputs: one complete versioned JSON request, or the literal `project-key`. Any other input — empty text, an operation name followed by loose arguments, or any other string — runs nothing: report that the skill takes one versioned JSON request or `project-key`, and never translate free text into a request. When the input is `project-key`, take its form in `<invocation_forms>` and stop; steps 2 to 4 govern requests only.
2. Check the request against this source-owned shape: exactly `schemaVersion` (`1`), `operation`, and `arguments`, where `arguments` holds only the fields the operation accepts in `<operation_surface>`:

   ```json
   {
     "schemaVersion": 1,
     "operation": "send",
     "arguments": {
       "record": {
         "schema": 1,
         "kind": "fact",
         "correlation": "<correlation>",
         "sender": "<sender name>",
         "recipient": "<recipient name>",
         "subject": "<subject>",
         "body": "<body>",
         "ackRequired": true
       }
     }
   }
   ```

3. Submit the request over stdin in one of the forms in `<invocation_forms>`.
4. Read the result by the exit code:
   - **Exit 0.** `status: "succeeded"` with exactly seven fields, every one of them preserved: `schemaVersion`, `operation`, `status`, `commandExitCode`, `projectKey`, the store's `response`, and `data`. A delivered message is the `record` in `data` carrying its store-assigned `id`.
   - **Exit 1.** The adapter read the request and it failed. The result carries `schemaVersion`, `operation` — the requested operation, or `unknown` where the request named none — `status`, and `detail`.
   - **Failure statuses.** `status` is one of `command-failed`, `invalid-schema`, `store-unavailable`, `repository-unresolved`, or `operation-unavailable`.
   - **Store exit code.** A failure also carries `commandExitCode` when a store command ran to completion, including a zero exit whose response the adapter rejected as `invalid-schema`; it is absent when no store command completed.
   - **Exit 2 with a result.** Stdin was not readable as one JSON object. The result carries `schemaVersion`, `operation: "unknown"`, `status: "invalid-schema"`, and `detail`, and no `commandExitCode`.
   - **Exit 2 without a result.** The command line named no CLI form or an unknown one: stdout is empty and stderr carries the usage text. Correct the command to a form in `<invocation_forms>`; never parse the empty stdout as a result.
   - **No fallback.** Stop on the exact `status` and `detail` of every failure; none of them admits a fallback command, key, or store.

</workflow>

<invocation_forms>

When the shell accepts multiline input:

```bash
python3 "${SKILL_DIR}/scripts/agent_mail.py" run <<'JSON'
{"schemaVersion":1,"operation":"list","arguments":{"agent":"<recipient name>","includeBodies":true}}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"schemaVersion":1,"operation":"list","arguments":{"agent":"<recipient name>","includeBodies":true}}' | python3 "${SKILL_DIR}/scripts/agent_mail.py" run
```

To read the project key alone:

```bash
python3 "${SKILL_DIR}/scripts/agent_mail.py" project-key
```

The `project-key` form reads no stdin and answers in one of two shapes:

- **Exit 0.** `{"projectKey": "<absolute path>"}`.
- **Exit 1.** `{"status": "repository-unresolved", "detail": "<reason>"}`.

Neither shape carries `schemaVersion`, `operation`, `commandExitCode`, `response`, or `data`, because the form runs no store command.

</invocation_forms>

<constraints>

- ALWAYS execute the bundled script exactly as `<invocation_forms>` spells it.
- NEVER import the script from another filesystem location, manufacture a path to it outside this skill directory, or copy its path spelling into an agent definition or an exported variable — only the spelling in `<invocation_forms>` resolves.
- ALWAYS preserve store identities verbatim: message ids, thread ids, agent names, and timestamps — each is a value the store holds, and a transformed copy matches no stored value, so an id, thread id, or name addresses nothing and a timestamp misstates the store's record.
- ALWAYS supply arguments under the field names in `<operation_surface>` and leave the mapping to the adapter: it alone turns a field into an `am` option or a store field and reads it back, and it rejects an argument outside the operation's shape as `invalid-schema` rather than dropping it.
- NEVER invoke raw `am` commands, `am` command help, or read the store's database.
- NEVER derive the project key outside the adapter; it reads the key from the repository, and no working directory, environment variable, or parent path stands in for it.
- NEVER treat a read as an evaluation of the message's content; it records only that the recipient marked one message read.
- NEVER treat an acknowledgement as agreement, ownership, authorization, or acceptance of a proposal; it is a read the sender can observe.
- NEVER derive liveness, staleness, or session state from the per-agent activity timestamp a store response carries — the store writes it once at registration and never maintains it.
- NEVER report or relay the registration token the store returns; the adapter removes it from every result.

</constraints>

<testing>

The evidence for the bundled adapter lives in the repository that ships this skill, `https://github.com/outcomeeng/plugins`, in the spec node whose front matter carries `id: 01a0b229-e718-7996-988b-d465e39f898d`, and the paths below are relative to that node's directory; a consumer install carries the skill without it. The deterministic tests run over generated requests, records, and repository shapes, with controlled `CommandRunner` implementations at the command boundary and real Git repositories behind the lookup.

`tests/test_agent_mail.mapping.l1.py`:

- every operation's request → the argument vector the store's captured usage text accepts, each option bound to its own value and both values of every optional boolean generated;
- a `list` request → the store's non-marking listing of unread records, and with `allRecords: true` → that listing's complete form;
- a `register` request → a command carrying no name, and a result whose `agent` is the name the store assigned;
- a listing row → a record for its recipient on every classification branch, with `kind` and `subject` asserted for each;
- a `recipient` carrying `,` → `invalid-schema` before any command runs;
- a pool's linked worktree, bare repository, main checkout, and a symlinked route to one of them → one project key; the pool's parent directory → `repository-unresolved`;
- each redirecting variable Git confirms, alone and all together → no change in the key;
- captured store responses and captured store failures → the success result or the named failure, with no value rewritten.

`tests/test_agent_mail.property.l1.py`:

- a generated record, including one whose correlation the thread alphabet rejects → the store fields and back to an equal record;
- an `order`, its `delegation-request`, and its one correlated terminal handback → delivered through this skill's own `send`, under one thread;
- a repeated terminal handback → one result; a conflicting kind, or the same kind with different content, for one reference → rejected, with a detail naming the difference. This reduction is a function of the bundled script that neither invocation form reaches: `run` with `send` delivers every handback it is given and checks none against earlier ones.

`tests/test_agent_mail.compliance.l1.py`:

- every operation where no executable resolves → `repository-unresolved`; where Git resolves and the store does not → `store-unavailable`; no fallback in either case;
- a captured registration response → a result without its token;
- a stale or fresh activity timestamp → the same status and data;
- stdin that does not parse → the versioned `invalid-schema` failure;
- a runner error of any class → a named failure result;
- a text argument carrying NUL → `invalid-schema` before any command runs;
- every operation where only the adapter's own programs resolve → completes;
- another shipped script building a raw mail command in argument-vector or shell-string form → reported.

The bundled script also carries the scanners the last compliance domain runs, which detect another shipped script building a raw mail command or deriving the project key from Git state. Neither invocation form reaches them; they are evidence machinery, not part of what this skill performs.

`probes/installed-store/probe.md` records an attested run of registration, send, listing, read, and acknowledgement against the installed `am` 0.3.36, whose committed observations are the captured usage and response fixtures the tests read.

</testing>

<failure_modes>

**A store keyed under the earlier derivation read back as an empty inbox.** Claude read an inbox for an agent that had been registered before the project key moved from the pool's main checkout path to the repository's own common Git directory, and took the empty result as "no messages". The registrations and message records were still in the store under the previous key, so the read was addressing a different project. A listing that reads back empty for an agent known to be registered is a key mismatch until shown otherwise: compare the result's `projectKey` with the key the agent registered under before reading an empty result as an answer. Registering again under the current key yields a new store-assigned name, not the earlier one, and carrying the earlier project's records into the current key is no operation in `<operation_surface>`; it is a store-side change, so report the mismatch and the two keys and leave that change to whoever operates the store.

</failure_modes>

<success_criteria>

- A successful `run` operation is established only when the bundled script exits zero and emits exactly the seven fields of the versioned success result — `schemaVersion: 1`, `operation`, `status: "succeeded"`, `commandExitCode: 0`, `projectKey`, `response`, and `data` — without exposing `am` command grammar; a successful `project-key` form is established only when it exits zero and emits `projectKey`.
- Every record sent and read back through `list` with `includeBodies: true` carries the same `schema`, `kind`, `correlation`, `sender`, `recipient`, `subject`, `body`, and `ackRequired`, plus the store-assigned `id` on read.
- No `list` changes a record's read state; only `read` and `acknowledge` do.
- An absent store or an unresolvable repository yields its named unavailable result and no fallback.
- No registration result carries the store's registration token.

</success_criteria>
