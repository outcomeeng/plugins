---
name: wait-for-event
description: >-
  ALWAYS invoke this skill when a coding-agent workflow must wake on the first of an agent-mail record, a herdr-hosted agent session state change, a consumption-control alert, or a clock instant, within one bounded timeout. NEVER poll mail, herdr, or alert state with a standing watcher or a hand-built loop.
argument-hint: "<JSON request>"
allowed-tools: Write, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/wait_event.py":*)
---

<objective>
One JSON line naming the first event any requested source yielded, every source that could not be read, the expiry of the timeout, or the rejection of the request, from one bounded run that ends when the line is printed.
</objective>

<request>

A request is one JSON object naming a required `timeoutSeconds`, a positive number, and a non-empty `sources` array. Each source is an object whose `kind` selects its form:

| Kind    | Fields                                                      | Yields an event when                                                                       |
| ------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `mail`  | `agent`, `id`                                               | a record in the inbox of `agent` has a store id above `id`                                 |
| `pane`  | `sessions`, each `{session, state}`; optional `environment` | the state of a named hosted agent session differs from the `state` passed                  |
| `spend` | `after`; optional `root`                                    | the consumption-control detector recorded an alert after the instant `after`               |
| `clock` | `at`                                                        | the instant `at`, an ISO 8601 instant ending in `Z` that falls before the timeout, arrives |

What the caller passes, taken from the last event it handled:

- `id` is the store id of the last mail record handled, `0` for none, so a run that ends at any point loses no record.
- `state` is the agent state the caller last handled for that session, one of the states `/operate-herdr` projects. `session` is the agent name or pane id herdr reports. `environment` defaults to `herdr`; any other environment projects no agent session state and is reported as unreadable.
- `after` and `at` are ISO 8601 instants ending in `Z`. `root` names the detector state root and defaults to the one `/control-token-spend` uses.

```json
{
  "timeoutSeconds": 600,
  "sources": [
    { "kind": "mail", "agent": "AmberGull", "id": 41 },
    { "kind": "pane", "sessions": [{ "session": "executor-288", "state": "working" }] },
    { "kind": "spend", "after": "2026-10-16T09:00:00Z" },
    { "kind": "clock", "at": "2026-10-16T10:00:00Z" }
  ]
}
```

</request>

<line_forms>

Every run prints exactly one of these, each one JSON object on one line whose `kind` names its form, then exits.

| `kind`              | Carries                                                                                        | Exit |
| ------------------- | ---------------------------------------------------------------------------------------------- | ---- |
| `event`             | `source`, plus the fields below for that source                                                | 0    |
| `timeout`           | `timeoutSeconds`                                                                               | 0    |
| `unreadable-source` | `sources`, one entry per unreadable source with its `source`, `detail`, and identifying fields | 1    |
| `invalid-request`   | `detail` naming the field                                                                      | 2    |

Event fields by `source`:

- `mail`: `record` with the record's `id`, `sender`, `kind`, and `subject`.
- `pane`: `environment`, `session`, the new `state`, and the `previousState` passed.
- `spend`: the alert's `identity`, `recordedUtc`, and `signal`.
- `clock`: `at`.

A source that cannot be read is never a quiet period. A mail store that is unavailable or whose listing does not reach back to `id`, a session absent from the inventory or with incomplete evidence, an unavailable or ambiguous herdr result, an environment without agent session state, and a detector state root that is absent or unreadable each appear in an `unreadable-source` line. Drop or repair the named source before arming again.

</line_forms>

<workflow>

1. Interpret `$ARGUMENTS` as a complete JSON request. When it is empty, run nothing and report that `timeoutSeconds` and at least one source are required.
2. Build the request from the last event handled, naming `timeoutSeconds` and every source to read.
3. Write the request with the file-write tool to a file in the scratch directory the harness names for this session, under a file name unique to the agent and the request, and submit it through the input redirect in `<invocation_form>`. Where the harness names no scratch directory, use the one the environment designates, such as `$RUNNER_TEMP` on a hosted runner.
4. Read the one line the run prints. Act on `event` by handling it, then re-arm with the new `id`, `state`, or `after` instant. Treat `timeout` as no event. Stop on `unreadable-source` or `invalid-request` and report the line verbatim.

</workflow>

<invocation_form>

With `<request-file>` the file written in step 3:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/wait_event.py" < <request-file>
```

</invocation_form>

<constraints>

- ALWAYS supply `timeoutSeconds`; the run has no default timeout and rejects a request without a positive one before reading any source.
- ALWAYS hold a wait to one invocation and re-arm it from the event handled; the script loops only inside its timeout and prints one line.
- NEVER pass a request through a heredoc, a pipe, or an inline argument, and NEVER remove the request file.
- NEVER run `am`, `herdr`, or a consumption-control read to reproduce a wait; the script reads mail through `/operate-agent-mail`, session states through `/operate-herdr`, and alerts through `/control-token-spend`, and builds no command of its own.
- NEVER rely on the wait to acknowledge a record, mark mail read, or prompt a pane; it keeps no cursor, state file, or lock and changes nothing. Record a receipt with `/operate-agent-mail` and steer a pane with `/operate-herdr`.
- NEVER start the wait in the background or keep it as a standing watcher; the next wait is armed after the line is handled.

</constraints>

<testing>

The script is covered over generated requests and controlled command runners and clocks at the adapters' command boundaries: the four line forms and their exit codes, a request without a positive timeout rejected before any source is read, each source's mapping from the capability result to an event, an unreadable-source line, or no event, the first-event order across sources, and the absence of any state, mail, receipt, or pane write.

</testing>

<success_criteria>

- Every run with a valid request prints exactly one line of the four forms and exits within its timeout, leaving no process and no file behind.
- A request without a positive `timeoutSeconds`, a non-object document, and an unknown source kind print `invalid-request` and read no source.
- Every mail, session, alert, or clock event carries the fields `<line_forms>` lists for its source, with store ids and instants preserved verbatim.
- Every source the run cannot read appears in an `unreadable-source` line rather than passing as a quiet period.

</success_criteria>
