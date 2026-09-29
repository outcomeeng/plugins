---
name: operate-herdr
description: >-
  ALWAYS invoke this skill when running a public herdr operation — agent inventory, read, bounded wait, prompt, start, relaunch, stop, keystroke, worktree create, or worktree open — on agent sessions herdr hosts. NEVER run herdr command help or construct the public CLI command directly.
argument-hint: "<operation or JSON request>"
allowed-tools: Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/herdr_environment.py":*)
---

<objective>
A versioned JSON herdr operation result — hosted-session identities and the server's own agent states preserved verbatim, each agent whose evidence lacks a projected field named as an incomplete item, and a created or opened worktree's path, workspace, and root pane — or one named status for a session that is not running, not found, not ready, blocked, stalled, timed out, or missing the evidence a readiness judgment reads.
</objective>

<operation_surface>

The source-owned operation names are:

| Operation         | Arguments                                                        | Mutation authorization |
| ----------------- | ---------------------------------------------------------------- | ---------------------- |
| `inventory`       | none                                                             | no                     |
| `read`            | one selector; optional `source`, `lines`                         | no                     |
| `wait`            | one selector, `timeout`; optional `until`                        | no                     |
| `prompt`          | one selector, `text`; optional `wait` with `timeout` and `until` | no                     |
| `key`             | one selector, `keys`                                             | required               |
| `start`           | `name`, `kind`, `pane`, `timeout`; optional `agentArguments`     | required               |
| `relaunch`        | as `start`, for a pane whose earlier agent session ended         | required               |
| `stop`            | `pane`                                                           | required               |
| `create-worktree` | `workspace`; optional `branch`, `base`, `path`                   | required               |
| `open-worktree`   | `workspace`, `path`                                              | required               |

A selector is exactly one of `agent` (a live agent name) or `pane` (a pane id such as `w1:p1`). `timeout` is milliseconds and is required on every wait: `wait`, `prompt` with `wait: true`, `start`, and `relaunch`; the adapter's subprocess bound always exceeds it. `until` lists the server's states `idle`, `working`, `blocked`, `done`, and `unknown`. `source` is one of `visible`, `recent`, `recent-unwrapped`, and `detection`. `workspace` is the id of the herdr workspace a new worktree groups with, such as `w1F`; a `create-worktree` or `open-worktree` request without it returns `invalid-schema` before any herdr command runs. The adapter owns every herdr command token and flag.

`read` returns the session's terminal text, not a JSON envelope. `start` launches the named agent kind into a pane at its shell prompt and succeeds only when herdr reports the session ready for input within the bound. `stop` submits the agent's own `/exit` to the pane: Claude Code and Codex, the agents `start` launches, end their session on it, and the pane stays open at its shell, so `relaunch` into the same pane follows.

`create-worktree` creates a Git worktree — on `branch` from `base` at `path` where the request names them, herdr's defaults otherwise — and opens it as its own herdr workspace in one operation; `open-worktree` does the same for the existing worktree at `path`. Neither takes focus. Herdr groups the new workspace with the one the request names as a linked-worktree workspace; the new workspace is never the named one. The result's `worktree` object carries the checkout's `path`, the new `workspace`, and that workspace's `rootPane`, which is the `pane` a `start` into the worktree takes. `create-worktree` records no worktree-occupancy claim; the agent session `start` launches in the worktree claims it at its own start.

</operation_surface>

<lifecycle_statuses>

Herdr reports lifecycle conditions as error codes; the adapter projects the codes that call for distinct handling to a named `status` and keeps the code under `errorCode`:

| herdr code             | `status`               | Meaning                                                     |
| ---------------------- | ---------------------- | ----------------------------------------------------------- |
| `server_not_running`   | `server-not-running`   | no server at the socket; the launch is refused, no fallback |
| `agent_not_found`      | `identity-unavailable` | the selector names no hosted session                        |
| `agent_not_ready`      | `agent-not-ready`      | start saw the agent but it is blocked during startup        |
| `agent_blocked`        | `agent-blocked`        | the session waits at an approval or question UI             |
| `agent_prompt_stalled` | `prompt-stalled`       | the prompt was written but no activity followed             |
| `timeout`              | `wait-timeout`         | the bound elapsed before a matching state                   |

Every other code stays verbatim under `command-failed`. `server-not-running` also arrives with no `errorCode` when no `herdr` executable resolves on the machine: no command ran, so there is no envelope, and the `detail` says so. A stalled or timed-out result does not prove the prompt was never delivered; read the session before submitting it again.

`agent-evidence-incomplete` carries no herdr code: a `start`, `relaunch`, or `wait` whose readiness judgment needs a field the agent's evidence lacks — `interactive_ready` for start and relaunch, `agent_status` for wait — returns it with the incomplete item under `session` in place of a readiness verdict.

</lifecycle_statuses>

<workflow>

1. Interpret `$ARGUMENTS` as one operation with its arguments, or as a complete JSON request. When it is empty, run nothing and return the result that one operation from `<operation_surface>` is required; the adapter has no default operation.
2. Build this source-owned request shape and set only the arguments the operation accepts:

```json
{
  "schemaVersion": 1,
  "operation": "create-worktree",
  "arguments": {
    "workspace": "w1F",
    "branch": "work/change-42",
    "mutationAuthorized": true
  }
}
```

3. For `key`, `start`, `relaunch`, `stop`, `create-worktree`, or `open-worktree`, run the request only when it names its exact target — one selector for `key`, the `pane` for `start`, `relaunch` and `stop`, the `workspace` for `create-worktree`, the `workspace` and worktree `path` for `open-worktree` — and carries `"mutationAuthorized": true` inside `arguments`, which states the operator's authorization for that target. Set the flag only when the request arrived with it or the operator authorized that exact target; never add it while interpreting a plain-text request. A request without it is not run.
4. Submit the request over stdin in one of the forms in `<invocation_forms>`.
5. Accept only `status: "succeeded"`. Preserve the complete versioned result, `commandExitCode`, and the public `response`: herdr's own JSON envelope for every operation but `read`, and for `read` herdr's terminal text verbatim under `output`. Read the projection the operation adds:
   - `inventory` carries `agents`, one item per hosted session with `name`, `agent`, `agent_status`, `pane_id`, `tab_id`, `workspace_id`, `cwd`, and `interactive_ready`. An agent whose evidence lacks any of those fields is an incomplete item: the fields its evidence carries, verbatim, and the missing names under `missingFields`. Every other agent stays complete.
   - `start`, `relaunch`, `wait`, `read`, and `prompt` carry under `session` the one hosted session they acted on, projected as an inventory item is. A `read` or `prompt` addressed to an agent whose evidence is incomplete still succeeds and carries the incomplete item.
   - `create-worktree` and `open-worktree` carry `worktree` with `path`, `workspace`, and `rootPane`.
6. On any other `status`, act on a named status from `<lifecycle_statuses>`, and stop with the exact `status` and `detail` on `command-failed`, `invalid-schema`, `mutation-unauthorized`, or `operation-unavailable`.

</workflow>

<invocation_forms>

When the shell accepts multiline input:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/herdr_environment.py" run <<'JSON'
{"schemaVersion":1,"operation":"inventory","arguments":{}}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"schemaVersion":1,"operation":"inventory","arguments":{}}' | python3 "${CLAUDE_SKILL_DIR}/scripts/herdr_environment.py" run
```

</invocation_forms>

<constraints>

- ALWAYS execute the bundled script through `${CLAUDE_SKILL_DIR}`; never import it from another filesystem location or manufacture a path outside this skill directory.
- ALWAYS preserve herdr identities and states verbatim: agent names, pane, tab, and workspace ids, and the server's own `agent_status`.
- ALWAYS carry an explicit `timeout` on every wait; the adapter rejects an unbounded wait before any command runs.
- ALWAYS address a worktree's agent session through the `rootPane` and `workspace` its worktree result returns, never through a pane of the workspace the request named.
- NEVER invoke raw herdr commands, herdr command help, or `herdr --skill`, the skill text herdr prints for agents; the adapter owns the grammar, and that text would put a second, unversioned grammar into the conversation.
- NEVER create a worktree for a herdr-hosted agent session with `git worktree add` — `create-worktree` creates the checkout and its grouped workspace in one authorized operation.
- NEVER run `key`, `start`, `relaunch`, `stop`, `create-worktree`, or `open-worktree` without authorization for its exact target in the request.
- NEVER produce or expect a pane-borne handback block; the environment surface carries prompts and keystrokes only, and message records travel through the agent-mail capability.

</constraints>

<testing>

The bundled adapter is covered by tests over the generated request domain and herdr's captured responses, with controlled `CommandRunner` implementations at the herdr boundary: every registry operation's argument vector is read against herdr's captured usage text and carries a subprocess bound above the request's timeout; every captured response — each command's success envelope, the read's terminal text, and every error envelope herdr emitted — maps to its result without rewriting; the captured start, wait, and prompt responses project the session's identity and state; the captured inventory, and inventories varied from its first item over every server state, project to complete participants while absent or duplicated selectors resolve to their named results; a captured inventory carrying an agent without a name and one without `interactive_ready`, and inventories varied by dropping each projected field, project every incomplete agent to its incomplete item and every other agent in full; start, relaunch, and wait return `agent-evidence-incomplete` exactly when a field their readiness judgment reads is missing, while read and prompt succeed carrying the item; the captured worktree create and open responses project to the checkout's path, a workspace other than the named one, and that workspace's root pane, and herdr's captured worktree list for the named workspace lists the checkout as a linked worktree open in the returned workspace; a worktree request without `workspace` runs no command; `create-worktree` runs its one command and nothing more; `stop` runs the prompt vector carrying `/exit`, herdr's captured pane list keeps the pane at its shell, and a relaunch into it succeeds; every projected error code maps to its named status and an unprojected code to `command-failed` with the code verbatim; every mutating request fails with authorization absent or `false`, every wait-bearing request fails without a timeout, and a request executed through the adapter against a child that outlives the derived bound returns `command-failed`.

</testing>

<success_criteria>

- A successful operation is established only when the bundled script exits zero and emits `schemaVersion: 1`, `status: "succeeded"`, `commandExitCode: 0`, and the public `response` without exposing herdr command grammar.
- Every hosted session in an inventory result keeps its complete public identity and the server's own state, or appears as an incomplete item naming exactly the fields its evidence lacks; no incomplete agent removes another agent from the result.
- A worktree result names the checkout's path, a workspace herdr grouped with the named one, and that workspace's root pane.
- A successful stop leaves its pane open at its shell.
- Every projected herdr error code reaches the caller as its named status with the code and message verbatim.
- No mutating operation, no worktree request without a workspace, and no unbounded wait reaches herdr.

</success_criteria>
