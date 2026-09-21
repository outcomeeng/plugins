---
name: operate-agent-mail
description: >-
  ALWAYS invoke this skill when a workflow registers a mail identity, sends a message record, reads an inbox, or records a receipt in the agent-mail store. NEVER construct an `am` command or resolve the mail project key when this capability is available.
argument-hint: "<operation or JSON request>"
allowed-tools: Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/agent_mail.py":*)
---

<objective>
A versioned JSON agent-mail operation result — a registered identity, a delivered record with its store-assigned id, the recipient's records, or a receipt — under the project key the repository names, with every store identity preserved verbatim.
</objective>

<operation_surface>

The source-owned operation names are:

| Operation     | Arguments                                                | Result data                                  |
| ------------- | -------------------------------------------------------- | -------------------------------------------- |
| `register`    | `agent`, `program`, `model`; optional `task`             | the registered `agent` name and store id     |
| `send`        | `record`                                                 | the `record` with its store-assigned `id`    |
| `inbox`       | `agent`; optional `unreadOnly`, `includeBodies`, `limit` | `records` read back for that recipient       |
| `receipt`     | `agent`, `messageId`                                     | the `agent` and `messageId` the store marked |
| `project-key` | none                                                     | the `projectKey` the repository names        |

The record and its delivery rules:

- **Fields.** A `record` carries exactly `schema` (`1`), `kind`, `correlation`, `sender`, `recipient`, `subject`, `body`, and `ackRequired`; the store assigns `id` on delivery.
- **Kinds a sender writes.** `order`, `fact`, `question`, `answer`, `delegation-request`, and the four terminal handbacks `delegation-completed`, `delegation-failed`, `delegation-rejected`, and `delegation-unavailable`. A read-back record whose subject carries no kind prefix reports `unclassified`.
- **Mapping.** The adapter maps `correlation` onto the store's thread, `kind` onto a subject prefix, and `ackRequired` onto the store's acknowledgement requirement, and reads each back; a store limit never shapes the record.
- **One recipient.** `recipient` names one agent. A value carrying the store's `,` separator is rejected with `invalid-schema` before any command runs.
- **Foreign rows.** A row another sender wrote reads back rather than failing the inbox read: without a thread it reads as `unclassified` with `correlation: null` and its subject verbatim, and an acknowledgement status other than `pending` or `acked` reads as `ackRequired: false`. A row without the store's `id`, `from`, or `subject` key is a malformed store response and fails the read as `invalid-schema`.

The project key is the repository's own common Git directory, so every worktree of one pool, the pool's bare repository, and the pool's main checkout resolve one mail project, and no checkout's deletion removes it. The adapter reads that directory for its own working directory before every operation and reads no working directory, environment variable, or parent path in its place. A working directory that is no repository yields `repository-unresolved`.

</operation_surface>

<workflow>

1. Interpret `$ARGUMENTS` as one operation with its arguments, or as a complete JSON request. When it is empty, run nothing and report that one operation from `<operation_surface>` is required; the adapter has no default operation.
2. Build this source-owned request shape and set only the arguments the operation accepts:

   ```json
   {
     "schemaVersion": 1,
     "operation": "send",
     "arguments": {
       "record": {
         "schema": 1,
         "kind": "fact",
         "correlation": "change-88-exec",
         "sender": "AmberGull",
         "recipient": "PeachFrog",
         "subject": "changeset pushed",
         "body": "Full commit SHA and branch, verbatim.",
         "ackRequired": true
       }
     }
   }
   ```

3. Submit the request over stdin in one of the forms in `<invocation_forms>`.
4. For a `run` request, accept only `status: "succeeded"`. Preserve the complete versioned result: `commandExitCode`, `projectKey`, the store's `response`, and `data`. A delivered message is the `record` in `data` carrying its store-assigned `id`. Stop with the exact `status` and `detail` on `command-failed`, `invalid-schema`, `store-unavailable`, `repository-unresolved`, or `operation-unavailable`; none of them admits a fallback command, key, or store. The `project-key` operation answers in its own shape, stated with its form below.

</workflow>

<invocation_forms>

When the shell accepts multiline input:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/agent_mail.py" run <<'JSON'
{"schemaVersion":1,"operation":"inbox","arguments":{"agent":"AmberGull","unreadOnly":true,"includeBodies":true}}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"schemaVersion":1,"operation":"inbox","arguments":{"agent":"AmberGull","unreadOnly":true,"includeBodies":true}}' | python3 "${CLAUDE_SKILL_DIR}/scripts/agent_mail.py" run
```

To read the project key alone:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/agent_mail.py" project-key
```

This form answers `{"projectKey": "<absolute path>"}` and exits zero, or `{"status": "repository-unresolved", "detail": "<reason>"}` and exits non-zero. It carries no `schemaVersion`, `status` on success, `commandExitCode`, `response`, or `data`, because it runs no store command.

</invocation_forms>

<constraints>

- ALWAYS execute the bundled script through `${CLAUDE_SKILL_DIR}`; never import it from another filesystem location or manufacture a path outside this skill directory, because the skill loader substitutes that expression into this body before the command runs, so only this spelling reaches the shell as this skill's real directory; it is no shell variable, and copying it into an agent definition or exporting it yields an empty prefix rather than an error.
- ALWAYS preserve store identities verbatim: message ids, thread ids, agent names, and timestamps, because downstream skills index on the literal and the operator compares it against the store.
- ALWAYS supply arguments under the field names in `<operation_surface>` and leave the mapping to the adapter: it alone turns a field into an `am` option or a store field and reads it back, and it rejects an argument outside the operation's shape as `invalid-schema` rather than dropping it.
- NEVER invoke raw `am` commands, `am` command help, or read the store's database.
- NEVER derive the project key outside the adapter; it reads the key from the repository, and no working directory, environment variable, or parent path stands in for it.
- NEVER treat a receipt as agreement, ownership, authorization, or the acknowledgement of a proposal; it records only that the recipient read one message.
- NEVER report or relay the registration token the store returns; the adapter removes it from every result.

</constraints>

<testing>

The bundled adapter is covered over generated request, record, and repository-lookup domains, with controlled `CommandRunner` implementations at the command boundary:

- every registry operation's argument vector is read against the store CLI's captured usage text under the resolved project key;
- a real pool's linked worktree, bare repository, main checkout, and a symlinked route to one of them each resolve one key, while the pool's parent directory resolves none;
- generated records round-trip through the store field mapping;
- an `order`, its `delegation-request`, and its one correlated terminal handback are delivered through this capability's own send path;
- repeated and conflicting terminal handbacks reduce to one result;
- the CLI run where no executable resolves returns `repository-unresolved` with no fallback, for every operation;
- every operation completes where only the adapter's own programs resolve;
- a captured registration response reaches the result without its token.

</testing>

<success_criteria>

- A successful `run` operation is established only when the bundled script exits zero and emits `schemaVersion: 1`, `status: "succeeded"`, `commandExitCode: 0`, `projectKey`, `response`, and `data` without exposing `am` command grammar; a successful `project-key` operation is established only when it exits zero and emits `projectKey`.
- Every record sent and read back carries the same `kind`, `correlation`, `sender`, `recipient`, `subject`, `body`, and `ackRequired`, plus the store-assigned `id` on read.
- An absent store or an unresolvable repository yields its named unavailable result and no fallback.
- No registration result carries the store's registration token.

</success_criteria>
