---
name: operate-herdr
description: >-
  ALWAYS invoke this skill when running a public herdr operation — agent inventory, read, bounded wait, prompt, start, relaunch, stop, keystroke, worktree create, or worktree open — on agent sessions herdr hosts. NEVER run herdr command help or construct the public CLI command directly.
argument-hint: "<operation or JSON request>"
allowed-tools: Bash(printf '%s\n' '{"schemaVersion":1,:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/herdr_environment.py":*)
---

<objective>
One versioned JSON result per herdr operation — `status: "succeeded"` with herdr's public response and the operation's projection, identities and states verbatim, or a failure `status` from `<lifecycle_statuses>` or among `command-failed`, `invalid-schema`, `mutation-unauthorized`, and `operation-unavailable` with its `detail` — except for stdin holding no single JSON object, which yields an unversioned `invalid-schema` result carrying only `status` and `detail`.
</objective>

<operation_surface>

The source-owned operation names are:

| Operation         | Arguments                                                        | Mutation authorization            |
| ----------------- | ---------------------------------------------------------------- | --------------------------------- |
| `inventory`       | none                                                             | no                                |
| `read`            | one selector; optional `source`, `lines`                         | no                                |
| `wait`            | one selector, `timeout`; optional `until`                        | no                                |
| `prompt`          | one selector, `text`; optional `wait` with `timeout` and `until` | when `text` is `/exit` or `/quit` |
| `key`             | one selector, `keys`                                             | required                          |
| `start`           | `name`, `kind`, `pane`, `timeout`; optional `agentArguments`     | required                          |
| `relaunch`        | as `start`, for a pane whose earlier agent session ended         | required                          |
| `stop`            | `pane`                                                           | required                          |
| `create-worktree` | `workspace`; optional `branch`, `base`, `path`                   | required                          |
| `open-worktree`   | `workspace`, `path`                                              | required                          |

A selector is exactly one of `agent` (a live agent name) or `pane` (a pane id such as `w1:p1`). `timeout` is milliseconds and is required on every wait: `wait`, `prompt` with `wait: true`, `start`, and `relaunch`; the adapter's subprocess bound always exceeds it. `until` lists the server's states `idle`, `working`, `blocked`, `done`, and `unknown`. `source` is one of `visible`, `recent`, `recent-unwrapped`, and `detection`. `workspace` is the id of the herdr workspace a new worktree groups with, such as `w1F`; a `create-worktree` or `open-worktree` request without it returns `invalid-schema` before any herdr command runs. Every text argument — `agent`, `pane`, `text`, `name`, `kind`, `path`, `workspace`, `branch`, `base` — and every item of `keys` and `until` is non-empty and never begins with `--`, which herdr would read as one of its options; such a request returns `invalid-schema` before any herdr command runs, whatever its authorization, as does a request whose `wait` or `mutationAuthorized` is not a JSON boolean. The adapter judges authorization only for a request it has found well formed. Items of `agentArguments` are exempt: they pass after herdr's `--` separator to the launched agent. The adapter owns every herdr command token and flag.

`read` returns the session's terminal text, not a JSON envelope. `start` launches the named agent kind into a pane at its shell prompt and succeeds only when herdr reports the session ready for input within the bound. `stop` submits the agent's own `/exit` to the pane: Claude Code and Codex, the agents `start` launches, end their session on it, and the pane stays open at its shell, so `relaunch` into the same pane follows. A `prompt` whose `text`, stripped of surrounding whitespace, is `/exit` — `stop`'s own command — or `/quit`, the alias Claude Code and Codex both accept for it, ends the session the same way, so it requires mutation authorization as `stop` does; without it the adapter returns `mutation-unauthorized` before any herdr command runs. A longer message that only mentions either command inside it ends no session and needs no authorization.

`create-worktree` creates a Git worktree — on `branch` from `base` where the request names them, herdr's defaults otherwise, at `path` — and opens it as its own herdr workspace in one operation; `open-worktree` does the same for the existing worktree at `path`. Neither takes focus. Herdr groups the new workspace with the one the request names as a linked-worktree workspace; the new workspace is never the named one. The result's `worktree` object carries the checkout's `path`, the new `workspace`, and that workspace's `rootPane`, which is the `pane` a `start` into the worktree takes. `create-worktree` records no worktree-occupancy claim; the agent session `start` launches in the worktree claims it at its own start.

The adapter accepts `create-worktree` without `path` and then lets herdr choose the checkout location, which no result states before the checkout exists. This skill therefore always sets `path` to an absolute destination, as `<workflow>` step 3 requires.

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

Every other code stays verbatim under `command-failed`. `server-not-running` also arrives with no `errorCode` when no `herdr` executable resolves on the machine: no command ran, so there is no envelope, and the `detail` says so.

`agent-evidence-incomplete` carries no herdr code: a `start`, `relaunch`, or `wait` whose readiness judgment needs a field the agent's evidence lacks — `interactive_ready` for start and relaunch, `agent_status` for wait — returns it with the incomplete item under `session` in place of a readiness verdict.

Every named status ends the operation. Report the exact `status`, `errorCode` when present, `detail`, and any `session`, and take only the follow-up its row names; any further mutating operation is a new request under its own authorization:

| `status`                    | Follow-up                                                                                                      |
| --------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `server-not-running`        | none: never start a herdr server or switch to another environment                                              |
| `identity-unavailable`      | run `inventory` to find the session's current name or pane; never re-address a request from a guessed selector |
| `agent-not-ready`           | `read` the pane before any `relaunch`, which needs its own authorization                                       |
| `agent-blocked`             | `read` the session to see the approval or question; an answer is a new `key` or `prompt` request               |
| `prompt-stalled`            | `read` the session before submitting the prompt again; the prompt may already be delivered                     |
| `wait-timeout`              | `read` the session before any retry; a prompt the request carried may already be delivered                     |
| `agent-evidence-incomplete` | none: report the item's `missingFields`, and treat the session as neither ready nor not ready                  |

</lifecycle_statuses>

<workflow>

1. Interpret `$ARGUMENTS` as one operation with its arguments, or as a complete JSON request. When it is empty, run nothing and return the result that one operation from `<operation_surface>` is required; the adapter has no default operation.
2. Build this source-owned request shape and set only the arguments the operation accepts; the angle-bracketed value is a placeholder for the destination step 3 obtains:

```json
{
  "schemaVersion": 1,
  "operation": "create-worktree",
  "arguments": {
    "workspace": "w1F",
    "branch": "work/change-42",
    "path": "<absolute checkout destination the authorization names>",
    "mutationAuthorized": true
  }
}
```

3. For `key`, `start`, `relaunch`, `stop`, `create-worktree`, `open-worktree`, or a `prompt` whose `text`, stripped of surrounding whitespace, is `/exit` or `/quit`, run the request only when it names its exact target and carries `"mutationAuthorized": true` inside `arguments`, which states the operator's authorization for that target. The target is one selector for `key`; the `pane` for `start`, `relaunch`, and `stop`; the session its selector names for that `prompt`; the workspace and the existing worktree at `path` for `open-worktree`; and for `create-worktree` the workspace and the absolute path of the checkout it writes, which the request carries as `path`. A `create-worktree` authorization that states no absolute destination authorizes no checkout: obtain one that states it, and never omit `path` or choose a destination the operator did not name. One authorization covers one checkout. Set the flag only when the request arrived with it or the operator authorized that exact target; never add it while interpreting a plain-text request. A request without it is not run.
4. Submit the request over stdin in one of the forms in `<invocation_forms>`.
5. Accept only `status: "succeeded"`. Preserve the complete versioned result, `commandExitCode`, and the public `response`: herdr's own JSON envelope for every operation but `read`, and for `read` herdr's terminal text verbatim under `output`. Read the projection the operation adds:
   - `inventory` carries `agents`, one item per hosted session with `name`, `agent`, `agent_status`, `pane_id`, `tab_id`, `workspace_id`, `cwd`, and `interactive_ready`. An agent whose evidence lacks any of those fields is an incomplete item: the fields its evidence carries, verbatim, and the missing names under `missingFields`. Every other agent stays complete.
   - `start`, `relaunch`, `wait`, `read`, and `prompt` carry under `session` the one hosted session they acted on, projected as an inventory item is. A `read` or `prompt` addressed to an agent whose evidence is incomplete still succeeds and carries the incomplete item.
   - `create-worktree` and `open-worktree` carry `worktree` with `path`, `workspace`, and `rootPane`.
6. On any other `status`, the operation carries no projection. For a status `<lifecycle_statuses>` names, report it and apply the follow-up its row names. On `command-failed`, `invalid-schema`, `mutation-unauthorized`, or `operation-unavailable`, stop with the exact `status` and `detail`. When the script exits 2 with only `status: "invalid-schema"` and `detail`, carrying no `schemaVersion` and no `operation`, stdin held no single JSON object and the adapter read no request; stop with that `status` and `detail` the same way.

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

The single-line request opens with `{"schemaVersion":1,`, the prefix this skill's `printf` grant admits.

</invocation_forms>

<constraints>

- ALWAYS execute the bundled script through `${CLAUDE_SKILL_DIR}`; never import it from another filesystem location or manufacture a path outside this skill directory.
- ALWAYS preserve herdr identities and states verbatim: agent names, pane, tab, and workspace ids, and the server's own `agent_status`.
- ALWAYS carry an explicit `timeout` on every wait; the adapter rejects an unbounded wait before any command runs.
- ALWAYS address a worktree's agent session through the `rootPane` and `workspace` its worktree result returns, never through a pane of the workspace the request named.
- NEVER invoke raw herdr commands, herdr command help, or `herdr --skill`, the skill text herdr prints for agents; the adapter owns the grammar, and that text would put a second, unversioned grammar into the conversation.
- NEVER create a worktree for a herdr-hosted agent session with `git worktree add` — `create-worktree` creates the checkout and its grouped workspace in one authorized operation.
- NEVER run `key`, `start`, `relaunch`, `stop`, `create-worktree`, `open-worktree`, or a `prompt` whose `text`, stripped of surrounding whitespace, is `/exit` or `/quit` without authorization for its exact target in the request — that prompt ends the session exactly as `stop` does.
- NEVER run `create-worktree` without an absolute `path` its authorization names — herdr's default location stays unstated until the checkout exists, so the write would land where no one confirmed it.
- NEVER produce or expect a pane-borne handback block; the environment surface carries prompts and keystrokes only, and message records travel through the agent-mail capability.

</constraints>

<testing>

Tested over the generated request domain and herdr's captured responses, with controlled `CommandRunner` implementations at the herdr boundary:

- Every registry operation's argument vector → matches herdr's captured usage text and carries a subprocess bound above the request's timeout ✓
- Every captured response — each success envelope, the read's terminal text, every error envelope herdr emitted → its result, without rewriting ✓
- Captured start, wait, and prompt responses → the session's identity and state ✓
- The captured inventory, and inventories varied from its first item over every server state → complete participants ✓
- Absent or duplicated selectors → their named results ✓
- A captured inventory with an agent lacking a name and one lacking `interactive_ready`, and inventories varied by dropping each projected field → each incomplete agent as its incomplete item, every other agent in full ✓
- Start, relaunch, and wait with a readiness field missing → `agent-evidence-incomplete`, exactly then ✓
- Read and prompt addressed to an incomplete agent → succeed carrying the item ✓
- Captured worktree create and open responses → the checkout's path, a workspace other than the named one, and that workspace's root pane ✓
- Herdr's captured worktree list for the named workspace → lists the checkout as a linked worktree open in the returned workspace ✓
- A worktree request without `workspace` → runs no command ✓
- `create-worktree` → runs its one command and nothing more ✓
- `stop` → runs the prompt vector carrying `/exit`; herdr's captured pane list keeps the pane at its shell; a relaunch into it succeeds ✓
- Every projected error code → its named status; an unprojected code → `command-failed` with the code verbatim ✓
- Every mutating request with authorization absent or `false` → fails ✓
- Every mutating request, and every `prompt` whose `text` is `/exit` or `/quit`, carrying a text argument that begins with `--` under authorization absent or `false`, or carrying `mutationAuthorized` as the text `"true"` → `invalid-schema` and no command ✓
- A `prompt` whose `text` is `/exit` or `/quit`, bare or padded with whitespace, with authorization absent or `false` → `mutation-unauthorized` and no command; with authorization → runs its command, `/exit` as `stop`'s own vector; a longer message mentioning either command, or any other text → runs unauthorized ✓
- Every wait-bearing request without a timeout → fails ✓
- A request against a child that outlives the derived bound → `command-failed` ✓

</testing>

<success_criteria>

- A successful operation is established only when the bundled script exits zero and emits `schemaVersion: 1`, `status: "succeeded"`, `commandExitCode: 0`, and the public `response` without exposing herdr command grammar.
- Every hosted session in an inventory result keeps its complete public identity and the server's own state, or appears as an incomplete item naming exactly the fields its evidence lacks; no incomplete agent removes another agent from the result.
- A worktree result names the checkout's path, a workspace herdr grouped with the named one, and that workspace's root pane.
- A stop's own result establishes only that herdr accepted `/exit`; its pane's return to the shell is established when a following `relaunch` into that pane, under that relaunch's own authorization, succeeds.
- Every projected herdr error code reaches the caller as its named status with the code and message verbatim.
- No mutating operation and no `prompt` whose `text`, stripped of surrounding whitespace, is `/exit` or `/quit` reaches herdr without authorization, and no worktree request without a workspace or unbounded wait reaches herdr.
- No `create-worktree` reaches herdr without an absolute `path` its authorization names.

</success_criteria>
