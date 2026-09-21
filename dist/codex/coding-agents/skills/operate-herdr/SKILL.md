---
name: operate-herdr
description: >-
  ALWAYS invoke this skill when operating on agent sessions herdr hosts — agent inventory, read, bounded wait, prompt, start, relaunch, stop, keystroke, or worktree open. NEVER run herdr command help or construct the public CLI command directly when this capability is available.
argument-hint: "<operation or JSON request>"
allowed-tools: Bash(printf:*), Bash(python3 "${SKILL_DIR}/scripts/herdr_environment.py":*)
---

<objective>
A versioned JSON herdr operation result preserving complete hosted-session identities, the server's own states, checked command status, and every success, lifecycle, schema, authorization, availability, or command-failure outcome in its source-owned shape.
</objective>

<operation_surface>

The source-owned operation names are:

| Operation       | Arguments                                                        | Mutation authorization |
| --------------- | ---------------------------------------------------------------- | ---------------------- |
| `inventory`     | none                                                             | no                     |
| `read`          | one selector; optional `source`, `lines`                         | no                     |
| `wait`          | one selector, `timeout`; optional `until`                        | no                     |
| `prompt`        | one selector, `text`; optional `wait` with `timeout` and `until` | no                     |
| `key`           | one selector, `keys`                                             | required               |
| `start`         | `name`, `kind`, `pane`, `timeout`; optional `agentArguments`     | required               |
| `relaunch`      | as `start`, for a pane whose earlier agent session ended         | required               |
| `stop`          | `pane`                                                           | required               |
| `open-worktree` | `path`                                                           | required               |

A selector is exactly one of `agent` (a live agent name) or `pane` (a pane id such as `w1:p1`). `timeout` is milliseconds and is required on every wait: `wait`, `prompt` with `wait: true`, `start`, and `relaunch`; the adapter's subprocess bound always exceeds it. `until` lists the server's states `idle`, `working`, `blocked`, `done`, and `unknown`. `source` is one of `visible`, `recent`, `recent-unwrapped`, and `detection`. The adapter owns every herdr command token and flag.

`read` returns the session's terminal text, not a JSON envelope. `open-worktree` opens a workspace for an existing worktree without taking focus and returns its root pane; `start` launches the named agent kind into a pane at its shell prompt and succeeds only when herdr reports the session ready for input within the bound. `stop` closes the pane and the session in it.

</operation_surface>

<lifecycle_statuses>

Herdr reports lifecycle conditions as error codes; the adapter projects the ones a workflow acts on to a named `status` and keeps the code under `errorCode`:

| herdr code             | `status`               | Meaning                                                     |
| ---------------------- | ---------------------- | ----------------------------------------------------------- |
| `server_not_running`   | `server-not-running`   | no server at the socket; the launch is refused, no fallback |
| `agent_not_found`      | `identity-unavailable` | the selector names no hosted session                        |
| `agent_not_ready`      | `agent-not-ready`      | start saw the agent but it is blocked during startup        |
| `agent_blocked`        | `agent-blocked`        | the session waits at an approval or question UI             |
| `agent_prompt_stalled` | `prompt-stalled`       | the prompt was written but no activity followed             |
| `timeout`              | `wait-timeout`         | the bound elapsed before a matching state                   |

Every other code stays verbatim under `command-failed`. `server-not-running` also arrives with no `errorCode` when no `herdr` executable resolves on the machine: no command ran, so there is no envelope, and the `detail` says so. A stalled or timed-out result does not prove the prompt was never delivered; read the session before submitting it again.

</lifecycle_statuses>

<workflow>

1. Interpret `$ARGUMENTS` as one operation with its arguments, or as a complete JSON request. When it is empty, run nothing and report that one operation from `<operation_surface>` is required; the adapter has no default operation.
2. Build this source-owned request shape and set only the arguments the operation accepts:

```json
{
  "schemaVersion": 1,
  "operation": "prompt",
  "arguments": {
    "agent": "officer1",
    "text": "[PeachFrog] mail 100",
    "wait": true,
    "timeout": 120000
  }
}
```

3. For `key`, `start`, `relaunch`, `stop`, or `open-worktree`, require the request to carry `"mutationAuthorized": true` inside `arguments` for that exact pane. Never infer or add mutation authorization; when it is absent or false, preserve the adapter's `mutation-unauthorized` result.
4. Submit the request over stdin in one of the forms in `<invocation_forms>`.
5. Accept only `status: "succeeded"`. Preserve the complete versioned result, `commandExitCode`, and the public `response`. For every operation but `read`, `response` is herdr's own JSON envelope: an inventory's `result` lists `agents`, and a `start`, `relaunch`, `wait`, or `prompt` result carries the one `agent` it acted on, each with `name`, `agent`, `agent_status`, `pane_id`, `tab_id`, `workspace_id`, `cwd`, and `interactive_ready`. For `read`, herdr writes terminal text, and `response` carries it verbatim under `output`.
6. On any other `status`, act on a named lifecycle status from `<lifecycle_statuses>`, and stop with the exact `status` and `detail` on `command-failed`, `invalid-schema`, `mutation-unauthorized`, or `operation-unavailable`.

</workflow>

<invocation_forms>

When the shell accepts multiline input:

```bash
python3 "${SKILL_DIR}/scripts/herdr_environment.py" run <<'JSON'
{"schemaVersion":1,"operation":"inventory","arguments":{}}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"schemaVersion":1,"operation":"inventory","arguments":{}}' | python3 "${SKILL_DIR}/scripts/herdr_environment.py" run
```

</invocation_forms>

<constraints>

- ALWAYS execute the bundled script through `${SKILL_DIR}`; never import it from another filesystem location or manufacture a path outside this skill directory.
- ALWAYS preserve herdr identities and states verbatim: agent names, pane, tab, and workspace ids, and the server's own `agent_status`.
- ALWAYS carry an explicit `timeout` on every wait; the adapter rejects an unbounded wait before any command runs.
- NEVER invoke raw herdr commands, herdr command help, or `herdr --skill`, the skill text herdr prints for agents; the adapter owns the grammar, and that text would put a second, unversioned grammar into the conversation.
- NEVER mutate a pane — key, start, relaunch, stop, or worktree open — without authorization for that exact pane in the request.
- NEVER produce or expect a pane-borne handback block; the environment surface carries prompts and keystrokes only, and message records travel through the agent-mail capability.

</constraints>

<testing>

The bundled adapter is covered by tests over the generated request domain and herdr's captured responses, with controlled `CommandRunner` implementations at the herdr boundary: every registry operation's argument vector is read against herdr's captured usage text and carries a subprocess bound above the request's timeout; every captured response — each command's success envelope, the read's terminal text, and every error envelope herdr emitted — maps to its result without rewriting; the captured start, wait, and prompt responses project the session's identity and state; the captured inventory, and inventories varied from its first item over every server state, project to complete participants while absent or duplicated selectors resolve to their named results; every projected error code maps to its named status and an unprojected code to `command-failed` with the code verbatim; every mutating request fails with authorization absent or `false`, every wait-bearing request fails without a timeout, and a request executed through the adapter against a child that outlives the derived bound returns `command-failed`.

</testing>

<failure_modes>

**Authorization was inferred from surrounding context.** Claude treated external workflow context as permission to add `mutationAuthorized: true`, so the capability was no longer independently invocable and an isolated skill audit rejected the same independence defect twice. Require the request itself to carry mutation authorization and preserve `mutation-unauthorized` when it does not.

**The objective omitted public failure results.** Claude described the lifecycle alternatives and left `invalid-schema`, `mutation-unauthorized`, `operation-unavailable`, and `command-failed` outside the stated output. The audit could not reconcile the objective with the workflow's complete public result family. Name every source-owned result class in the objective and preserve each returned shape without rewriting.

</failure_modes>

<success_criteria>

- A successful operation is established only when the bundled script exits zero and emits `schemaVersion: 1`, `status: "succeeded"`, `commandExitCode: 0`, and the public `response` without exposing herdr command grammar.
- Every hosted session in an inventory result keeps its complete public identity and the server's own state.
- Every projected herdr error code reaches the result as its named status with the code and message verbatim.
- No mutating operation and no unbounded wait reaches herdr.

</success_criteria>
