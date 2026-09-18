---
name: operate-agent-mail
description: >-
  ALWAYS invoke this skill when a workflow registers a mail identity, sends a message record, reads an inbox, or records a receipt in the agent-mail store. NEVER construct an `am` command or derive the mail project key from Git state when this capability is available.
argument-hint: "<operation or JSON request>"
allowed-tools: Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/agent_mail.py":*)
---

<objective>
A versioned JSON agent-mail operation result — a registered identity, a delivered record with its store-assigned id, the recipient's records, or a receipt — under the project key the SPX diagnosis names, with every store identity preserved verbatim.
</objective>

<operation_surface>

The source-owned operation names are:

| Operation  | Arguments                                                | Result data                                  |
| ---------- | -------------------------------------------------------- | -------------------------------------------- |
| `register` | `agent`, `program`, `model`; optional `task`             | the registered `agent` name and store id     |
| `send`     | `record`                                                 | the `record` with its store-assigned `id`    |
| `inbox`    | `agent`; optional `unreadOnly`, `includeBodies`, `limit` | `records` read back for that recipient       |
| `receipt`  | `agent`, `messageId`                                     | the `agent` and `messageId` the store marked |

A `record` carries exactly `schema` (`1`), `kind`, `correlation`, `sender`, `recipient`, `subject`, `body`, and `ackRequired`; the store assigns `id` on delivery. The kinds a sender writes are `order`, `fact`, `question`, `answer`, `delegation-request`, and the four terminal handbacks `delegation-completed`, `delegation-failed`, `delegation-rejected`, and `delegation-unavailable`. A read-back record whose subject carries no kind prefix reports `unclassified`. The adapter maps `correlation` onto the store's thread, `kind` onto a subject prefix, and `ackRequired` onto the store's acknowledgement requirement, and reads each back; a store limit never shapes the record.

The project key is the pool's main checkout path from `spx diagnose --format json`'s `worktree-pool` record, so every worktree of one pool resolves one mail project. The adapter runs that diagnosis itself before every operation and reads no Git state, working directory, or environment variable in its place.

</operation_surface>

<workflow>

1. Interpret `$ARGUMENTS` as one operation with its arguments, or as a complete JSON request. When it is empty, require a concrete operation before running the adapter.
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

3. Submit the request over stdin.

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

4. Accept only `status: "succeeded"`. Preserve the complete versioned result: `commandExitCode`, `projectKey`, the store's `response`, and `data`. A delivered message is the `record` in `data` carrying its store-assigned `id`; that id is the value a doorbell line names. Stop with the exact `status` and `detail` on `command-failed`, `invalid-schema`, `store-unavailable`, `diagnosis-unavailable`, or `operation-unavailable`; none of them admits a fallback command, key, or store.

</workflow>

<constraints>

- ALWAYS execute the bundled script through `${CLAUDE_SKILL_DIR}`; never import it from another filesystem location or manufacture a path outside this skill directory.
- ALWAYS preserve store identities verbatim: message ids, thread ids, agent names, and timestamps.
- NEVER invoke raw `am` commands, `am` command help, or read the store's database.
- NEVER derive the project key from Git state, the working directory, or an environment variable; the diagnosis is its only source.
- NEVER treat a receipt as agreement, ownership, authorization, or the acknowledgement of a proposal; it records only that the recipient read one message.
- NEVER report or relay the registration token the store returns; the adapter removes it from every result.

</constraints>

<testing>

Before release, import the bundled module with controlled `CommandRunner` implementations under the interaction-protocol and failure-simulation exceptions. Run every registry operation and require the exact `am` argument vector under the diagnosed project key; round-trip generated records through the store field mapping; reduce repeated and conflicting terminal handbacks; run the CLI where no executable resolves and require `diagnosis-unavailable` with no fallback; and require a registration result that carries no token.

</testing>

<success_criteria>

- A successful operation is established only when the bundled script exits zero and emits `schemaVersion: 1`, `status: "succeeded"`, `commandExitCode: 0`, `projectKey`, `response`, and `data` without exposing `am` command grammar.
- Every record sent and read back carries the same `kind`, `correlation`, `sender`, `recipient`, `subject`, `body`, and `ackRequired`, plus the store-assigned `id` on read.
- An absent store or an unavailable diagnosis yields its named unavailable result and no fallback.
- No registration result carries the store's registration token.

</success_criteria>
