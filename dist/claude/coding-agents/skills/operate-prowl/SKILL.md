---
name: operate-prowl
description: >-
  ALWAYS invoke this skill when a workflow needs a public Prowl operation or a correlated delegation handback between Prowl coding agents. NEVER run Prowl command help or construct the public CLI command directly when this capability is available.
argument-hint: "<operation, delegation, or JSON request>"
allowed-tools: Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py":*), AskUserQuestion
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

<operator_target_resolution>

An operator names a target by where the work lives — a worktree path, a repository directory, the working directory of the agent they mean, or a phrase describing it ("the agent in the frontend checkout", "my other window"). An operator never supplies a pane UUID, and a reply that asks for one has misread the request.

Resolve an operator-named target to a pane before operating:

1. Run `agents` (or `list` when the target need not be an agent) to get the complete inventory with each pane's worktree and repository.
2. Match the operator's phrasing against those worktree and repository paths. A path the operator gives may be a subdirectory of the worktree root, so match by containment, not string equality.
3. Operate on the matched pane's complete UUID.

Report the target back to the operator the way they named it — the worktree or directory — while using the pane UUID internally. Echoing a UUID to an operator who named a directory forces them to verify a value they never supplied.

When the inventory holds no match, say which worktrees are present rather than asking the operator to supply an identifier they do not have. When more than one pane matches, name the candidates by worktree and branch and ask which one; never guess by focus, position, or title.

</operator_target_resolution>

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

3. For `key`, `focus`, `tab-create`, `tab-close`, `pane-close`, or `open`, require an explicit user instruction authorizing that exact external mutation in the same turn. `open` can visibly switch focus and create a first terminal tab, so it is never read-only. When authorization is absent, use `AskUserQuestion` with the exact operation and complete target identity; do not run the adapter. After authorization, add `"mutationAuthorized": true` inside `arguments`. For `open`, set arguments to `{"mutationAuthorized":true}` or `{"path":"<complete-source-supplied-path>","mutationAuthorized":true}`.
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
  "returnAddress": {
    "pane": "<sender's own complete pane id>",
    "handbackCommand": "<exact command the recipient runs to notify the sender>"
  },
  "coordinationReference": null
}
```

`returnAddress` is required. The sender cannot poll for completion, so the recipient is the only party that can close the loop — and it can only do that when the delegation itself carries the sender's own complete pane id and the exact command to reach it. A delegation without a return address is a request the sender can never learn the answer to.

The result carries the complete source-owned `delegation` envelope. Preserve it for the terminal handback; transport success is not acceptance or completion.
7. The recipient submits exactly one terminal result to `handback`, carrying the original `delegation`, one `kind`, and one supported result form:

- `delegation-completed`
- `delegation-failed`
- `delegation-rejected`
- `delegation-unavailable`

A complete inline result uses `inlineResult`. A durable result uses `resultReference` plus a bounded `projection`; both forms may appear together. The adapter rejects a missing result, a reference without projection, and a conflicting terminal handback.
8. Return the complete terminal result to the delegating workflow. Do not poll the recipient, add acceptance or progress phases, or infer completion from pane output.

</workflow>

<handback_delivery>

Completion travels by push, never by pull. The sender's environment blocks polling loops by design, so a sender that "checks later" has no later to check in — it reads once, sees nothing, and moves on while the finished result sits on disk. The recipient closes the loop or nobody does.

**A durable result separates payload from signal.** The file carries the payload; one line sent into the sender's pane carries the signal. Write the file first, then send. `resultReference` names the complete absolute path and `projection` carries the bounded summary, so the sender knows what landed without opening it.

**The recipient delivers the handback by sending one line into the return address's pane**, using the `send` operation with normal trailing-Enter behavior. That send lands as a turn in the sender's session, which is what makes it a signal rather than a message the sender must go looking for. A `noEnter` send prefills the sender's editor and signals nothing.

**The sender states the return address at delegation time**, not after. Along with its own pane id and the exact command, the sender names the environment traps in `<environment_traps>` — a recipient that discovers those traps by hitting them has already spent the turn the delegation was meant to buy.

</handback_delivery>

<environment_traps>

Two environment conditions silently break a handback. Name both in the delegation's return address rather than leaving the recipient to find them.

**The CLI may not be on `PATH`.** A recipient whose shell cannot resolve the command reads the failure as "the environment is unavailable" and abandons the handback. The executable bundled inside the application resolves when `PATH` does not, so the return address carries the command form that works in the recipient's environment rather than a bare command name.

**A non-default socket may belong to a different instance.** When the socket is overridden, the CLI talks to whichever instance owns that socket — which can be another agent's verification harness holding no real panes rather than the operator's live application. An empty or unrecognizable pane inventory is that condition, not an absent recipient. Confirm the inventory contains the expected panes before concluding a target is gone, and use the same socket value for every command in the exchange.

</environment_traps>

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

**A delegation had no return path, so the operator became the message bus.** Claude asked a recipient to write a file, then had no signal that it had. Polling loops are blocked in the environment, so Claude read the pane once, saw nothing, and moved on — while a complete result sat on disk. The operator ended up carrying the answer between the two agents by hand. The delegation carried no return address, so the recipient could not push and the sender could not pull. Send the sender's own pane id, the exact handback command, and `<environment_traps>` in the delegation itself, and require the recipient to send one line on completion per `<handback_delivery>`.

**A single read was mistaken for a terminal answer.** Claude treated one empty pane read as evidence the recipient had produced nothing, when it proved only that nothing was on screen at that instant. A read establishes the pane's state at the moment it ran and never establishes that a delegation is incomplete. Completion arrives as the recipient's handback; its absence is an open delegation, not a negative result.

**An overridden socket was read as an empty environment.** Claude pointed the CLI at a non-default socket, saw an inventory with none of the expected panes, and concluded the recipient was gone. The socket belonged to a different instance — a verification harness, not the operator's live application. Confirm the inventory contains the expected panes before concluding a target is absent, per `<environment_traps>`.

</failure_modes>

<success_criteria>

- A successful public operation is mechanically established only when the bundled script exits zero and emits `schemaVersion: 1`, `status: "succeeded"`, `commandExitCode: 0`, and a public `response` object without exposing Prowl command grammar.
- Every positively identified Prowl participant retains complete public identities verbatim.
- Every delegation preserves its initiating coordination reference through exactly one completed, failed, rejected, or unavailable terminal handback.
- Every delegation carries a return address with the sender's own complete pane id, the exact handback command, and the `<environment_traps>` conditions, so the recipient can push completion without discovering the environment first.
- A durable handback writes its file before sending, and the notification reaches the sender's pane as a submitted turn rather than editor prefill.
- An operator-named target is resolved from the worktree or directory the operator supplied and reported back in those terms, never as a pane UUID the operator must verify.
- Terminal results carry complete inline content or an exact durable reference with a bounded projection.
- Unauthorized focus, key, creation, closure, and open requests fail before Prowl runs.
- Lazy activation is established by an authorized `open` result carrying `resolution: exact-root`, `created_tab: true`, and the complete returned pane identity.
- No workflow polls, invokes help, or depends on a separate environment-control skill.

</success_criteria>
