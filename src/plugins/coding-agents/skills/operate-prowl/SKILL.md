---
name: operate-prowl
description: >-
  ALWAYS invoke this skill when a workflow needs a public Prowl operation or a correlated delegation handback between Prowl coding agents. NEVER run Prowl command help or construct the public CLI command directly when this capability is available.
argument-hint: "<operation, delegation, or JSON request>"
allowed-tools: Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py":*), {{! tool('ask_user') !}}
---

<objective>
A versioned JSON Prowl operation result or one correlated terminal delegation handback, with complete public identities and checked command status preserved verbatim.
</objective>

<operation_surface>

The source-owned operation names are:

| Operation    | Arguments                                                                                           | Mutation authorization |
| ------------ | --------------------------------------------------------------------------------------------------- | ---------------------- |
| `list`       | none                                                                                                | no                     |
| `agents`     | none                                                                                                | no                     |
| `read`       | one selector; optional `last`, `waitStable`, stability bounds                                       | no                     |
| `send`       | one selector, `text`; optional `noEnter`, `noWait`, `capture`, `timeout` with the constraints below | no                     |
| `key`        | one selector, `key`; optional `repeat`                                                              | required               |
| `focus`      | one selector                                                                                        | required               |
| `tab-create` | optional selector and `path`                                                                        | required               |
| `tab-close`  | one selector; optional `force`                                                                      | required               |
| `pane-close` | one selector; optional `force`                                                                      | required               |
| `open`       | optional `path`                                                                                     | required               |

A selector is exactly one of `target`, `worktree`, `tab`, or `pane`. Preserve its complete public value. For `send`, `capture` cannot combine with `noEnter` or `noWait`, and `timeout` cannot combine with `noWait`. The adapter always requests public JSON and owns every Prowl command token and flag.

</operation_surface>

<workflow>

1. Interpret `$ARGUMENTS` as one low-level operation, one delegation request, or one terminal handback. When it is empty, require a concrete operation before running the adapter.
2. For `list`, `agents`, `read`, or `send`, build this source-owned request shape and set only arguments the operation accepts:

```json
{
  "schemaVersion": 1,
  "operation": "agents",
  "arguments": {}
}
```

`list` inventories instantiated terminal panes only. A worktree visible in Prowl's sidebar but never entered in the current app process can be absent from `list` because it has no pane UUID yet.

3. For `key`, `focus`, `tab-create`, `tab-close`, `pane-close`, or `open`, require an explicit user instruction authorizing that exact external mutation in the same turn. `open` can visibly switch focus and create a first terminal tab, so it is never read-only. When authorization is absent, use `{{! tool('ask_user') !}}` with the exact operation and complete target identity; do not run the adapter. After authorization, add `"mutationAuthorized": true` inside `arguments`. For `open`, set arguments to `{"mutationAuthorized":true}` or `{"path":"<complete-source-supplied-path>","mutationAuthorized":true}`.
4. Submit a low-level request over stdin.

When the shell accepts multiline input:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" run <<'JSON'
{"schemaVersion":1,"operation":"agents","arguments":{}}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"schemaVersion":1,"operation":"agents","arguments":{}}' | python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" run
```

5. Accept only `status: "succeeded"`. Preserve the complete versioned result, `commandExitCode`, and public `response` values. For `open`, preserve `response.data.resolution`, `created_tab`, and the complete target; `exact-root` with `created_tab: true` is the lazy equivalent of clicking a known sidebar worktree that has no terminal pane. `new-root` means Prowl added a previously unknown root and never proves a prepared recovery target existed. For submitted `send`, preserve `response.data.input.trailing_enter_sent`; a successful command with that field false or absent does not prove the turn left the editor. Stop with the exact `status` and `detail` on `command-failed`, `invalid-schema`, `prowl-unavailable`, `mutation-unauthorized`, or `operation-unavailable`.
6. For bounded delegation between two identities returned by `agents`, submit this shape to `delegate`:

```json
{
  "sender": {
    "agent": "<complete-agent-id>",
    "pane": "<complete-pane-id>",
    "worktree": "<absolute-worktree-path>",
    "branch": "<complete-branch>",
    "repository": "<absolute-repository-root>",
    "run": "<complete-run-id-when-present>"
  },
  "recipient": {
    "agent": "<complete-agent-id>",
    "pane": "<complete-pane-id>",
    "worktree": "<absolute-worktree-path>",
    "branch": "<complete-branch>",
    "repository": "<absolute-repository-root>",
    "run": "<complete-run-id-when-present>"
  },
  "subject": "<bounded subject>",
  "instruction": "<complete bounded request>",
  "coordinationReference": null
}
```

The result carries the complete source-owned `delegation` envelope. Preserve it for the terminal handback; transport success is not acceptance or completion.
7. The recipient submits exactly one terminal result to `handback`, carrying the original `delegation`, one `kind`, and one supported result form:

- `delegation-completed`
- `delegation-failed`
- `delegation-rejected`
- `delegation-unavailable`

A complete inline result uses `inlineResult`. A durable result uses `resultReference` plus a bounded `projection`; both forms may appear together. The adapter rejects a missing result, a reference without projection, and a conflicting terminal handback.
8. Return the complete terminal result to the delegating workflow. Do not poll the recipient, add acceptance or progress phases, or infer completion from pane output.

</workflow>

<constraints>

- ALWAYS preserve complete source-supplied agent, pane, worktree, branch, repository, run, coordination, status, conclusion, exit-code, and result-reference values.
- ALWAYS execute the bundled script through `${CLAUDE_SKILL_DIR}`; never import it from another filesystem location or manufacture a path outside this skill directory.
- NEVER invoke raw Prowl commands, Prowl command help, or an external environment-control skill.
- NEVER mutate focus, keys, tabs, panes, or open-path selection without explicit authorization for the exact operation and target in the same turn.
- NEVER equate `list` with the sidebar worktree inventory or enumerate filesystem worktrees to compensate for an uninstantiated pane.
- NEVER scan transcripts, parse terminal presentation as identity, or poll for delegation completion.
- NEVER make retry, checkpoint, persistence, result-interpretation, or continuation decisions for another workflow.

</constraints>

<testing>

Before release, import the bundled module with controlled `CommandRunner` implementations under the interaction-protocol and failure-simulation exceptions. Cover every operation mapping, public JSON success and failure, exact participant projection, mutation rejection before command construction, delegation result forms, repeated terminals, conflicting terminals, malformed input, missing Prowl, and CLI stdin dispatch.

</testing>

<failure_modes>

**A selectorless tab creation was rejected.** Claude applied the shared selector requirement to `tab-create`, even though the public operation accepts both selectorless and selected forms. The shared request builder hid the operation-specific shape. Build `tab-create` from its declared optional-selector contract and preserve optional `path` independently.

**An advertised operation had no construction branch.** Claude listed `open` in the public surface but grouped only list, agents, read, and send into the non-mutating workflow. Claude then had to infer the request shape. Keep every advertised operation in an explicit construction branch; `open` accepts empty arguments or one source-supplied `path`, always with explicit mutation authorization.

**A visible worktree was absent from `list`.** Claude inferred missing Prowl topology because a sidebar row had no listed pane. The row was known but not entered; `open` returned `resolution: exact-root`, `created_tab: true`, and the first pane UUID. Treat `list` as the terminal inventory and use authorized `open` for visible lazy activation.

</failure_modes>

<success_criteria>

- A successful public operation is mechanically established only when the bundled script exits zero and emits `schemaVersion: 1`, `status: "succeeded"`, `commandExitCode: 0`, and a public `response` object without exposing Prowl command grammar.
- Every positively identified Prowl participant retains complete public identities verbatim.
- Every delegation preserves its initiating coordination reference through exactly one completed, failed, rejected, or unavailable terminal handback.
- Terminal results carry complete inline content or an exact durable reference with a bounded projection.
- Unauthorized focus, key, creation, closure, and open requests fail before Prowl runs.
- Lazy activation is established by an authorized `open` result carrying `resolution: exact-root`, `created_tab: true`, and the complete returned pane identity.
- No workflow polls, invokes help, or depends on a separate environment-control skill.

</success_criteria>
