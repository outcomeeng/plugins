<!-- Generated from the complete producer set:
src/plugins/coding-agents/skills/operate-prowl/SKILL.md
src/plugins/coding-agents/skills/message-agents/SKILL.md
src/plugins/coding-agents/skills/coordinate-agents/SKILL.md
-->

Apply the complete Prowl resolution, semantic messaging, and coordination producers below to the supplied authoritative evidence. Resolve every operator-named path through the Prowl producer, construct every message through the messaging producer, and return only the coordinator's structured JSON verdict. Do not invoke external tools or send messages during this evaluation; execute the supplied producers against the public evidence in the request.

<pre><code>
<!-- Producer: src/plugins/coding-agents/skills/operate-prowl/SKILL.md -->

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

<operator_target_resolution>

An operator names a target by where the work lives — an absolute worktree path, repository directory, or working directory. Resolve that path through one `resolve-target` invocation before operating:

```bash
printf '%s\n' '{"schemaVersion":1,"path":"<absolute-operator-supplied-path>"}' | python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" resolve-target
```

The resolver runs the public `agents` operation once and returns its complete checked result under `inventory`, every complete participant under `participants`, the complete caller selected from `PROWL_PANE_ID` or the exact `PROWL_WORKTREE_PATH` fallback, and non-caller path matches under `candidates`. When both caller values exist, both must identify the same participant. Each candidate carries its complete participant metadata and a `sendRequestTemplate` with that pane already selected, `noWait: true`, and `text: null`. Fill `text` with the semantic payload; never repair the JSON through shell substitution or a temporary file.

Use the one candidate directly when `status` is `succeeded`. On `identity-ambiguous`, name every candidate by worktree and branch and ask which one; select only from the returned candidates. On `identity-unavailable`, report the supplied path and the returned participant worktrees. The resolver performs no send in every result state.

A target that is not a coding-agent pane is outside what `agents` returns, so no path match is available for it. Say that the operator's target is not among the agent panes and name the ones that are, rather than falling back to an inventory that carries no worktree to match.

Absent from `agents` is not the same as absent from Prowl. A worktree Prowl already knows but has never entered has no pane to match yet and stays reachable through an explicitly authorized `open` request, which takes a path rather than a selector; that is the lazy activation `<failure_modes>` describes. Distinguish it from a target Prowl has no relationship with at all before reporting the operator's target as unavailable.

Report the target back to the operator as the supplied path while using the selected template's pane internally. Never ask the operator for a pane UUID or guess by focus, position, or title.

</operator_target_resolution>

<workflow>

1. Interpret `$ARGUMENTS` as one target resolution, low-level operation, delegation request, or terminal handback. When it is empty, require a concrete operation before running the adapter. Resolve an absolute worktree, repository, or working-directory target per `<operator_target_resolution>` before building its operation request.
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

5. Accept only `status: "succeeded"` for a submitted operation. Preserve the complete versioned result, `commandExitCode`, and public `response` values. For `open`, preserve `response.data.resolution`, `created_tab`, and the complete target; `exact-root` with `created_tab: true` is the lazy equivalent of clicking a known sidebar worktree that has no terminal pane. `new-root` means Prowl added a previously unknown root and never proves a prepared recovery target existed. For submitted `send`, require `commandExitCode: 0` and preserve `response.data.input.trailing_enter_sent`; success with that field false or absent does not prove the turn left the editor. Once the checked send reports `trailing_enter_sent: true`, the turn is queued and delivery is complete; never send it again because the entry box becomes free. Stop with the exact `status` and `detail` on `command-failed`, `invalid-schema`, `prowl-unavailable`, `mutation-unauthorized`, or `operation-unavailable`.
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
  "instruction": "<complete bounded request, ending with the return path per <handback_delivery>>",
  "coordinationReference": null
}
```

The envelope already carries the return address: `sender.pane` is the sender's own complete pane, and the recipient reads it from the delegation it receives. Nothing else needs a field. What the recipient cannot infer is the exact command that reaches that pane and the environment conditions that break it, so the `instruction` ends by naming both per `<handback_delivery>`. The sender cannot poll for completion, so the recipient is the only party that can close the loop; an instruction that omits the handback is a request the sender can never learn the answer to.

The result carries the complete source-owned `delegation` envelope. Preserve it for the terminal handback; transport success is not acceptance or completion.

A direct delegation submission uses the same stdin boundary:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" delegate <<'JSON'
{"sender":{"agent":"agent-a","pane":"11111111-1111-4111-8111-111111111111","worktree":"/repo-a","branch":"work/a","repository":"/repo.git","run":"run-a"},"recipient":{"agent":"agent-b","pane":"22222222-2222-4222-8222-222222222222","worktree":"/repo-b","branch":"work/b","repository":"/repo.git","run":"run-b"},"subject":"Review resolver evidence","instruction":"Write the result first. Then run exactly: printf '%s\\n' '{\"schemaVersion\":1,\"operation\":\"send\",\"arguments\":{\"pane\":\"11111111-1111-4111-8111-111111111111\",\"text\":\"Resolver evidence review completed; terminal result follows.\",\"noWait\":true}}' | python3 \"${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py\" run. Capture the complete result and require status succeeded, commandExitCode 0, and response.data.input.trailing_enter_sent true. Use the default socket, confirm the expected panes, and use this bundled command path when the CLI is absent from PATH.","coordinationReference":null}
JSON
```

7. The recipient submits exactly one terminal result to `handback`, carrying the original `delegation`, one `kind`, and one supported result form:

- `delegation-completed`
- `delegation-failed`
- `delegation-rejected`
- `delegation-unavailable`

A complete inline result uses `inlineResult`. A durable result uses a scheme-bearing `resultReference` plus a bounded `projection`; use `file:///absolute/path` for a local file. Both forms may appear together. The adapter rejects a missing result, a reference without a URI scheme or projection, and a conflicting terminal handback.

A direct inline handback submission carries the complete returned delegation:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py" handback <<'JSON'
{"delegation":{"schemaVersion":1,"kind":"delegation-request","coordinationReference":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa","sender":{"agent":"agent-a","pane":"11111111-1111-4111-8111-111111111111","worktree":"/repo-a","branch":"work/a","repository":"/repo.git","run":"run-a"},"recipient":{"agent":"agent-b","pane":"22222222-2222-4222-8222-222222222222","worktree":"/repo-b","branch":"work/b","repository":"/repo.git","run":"run-b"},"subject":"Review resolver evidence","instruction":"Write the result first. Then run exactly: printf '%s\\n' '{\"schemaVersion\":1,\"operation\":\"send\",\"arguments\":{\"pane\":\"11111111-1111-4111-8111-111111111111\",\"text\":\"Resolver evidence review completed; terminal result follows.\",\"noWait\":true}}' | python3 \"${CLAUDE_SKILL_DIR}/scripts/prowl_environment.py\" run. Capture the complete result and require status succeeded, commandExitCode 0, and response.data.input.trailing_enter_sent true. Use the default socket, confirm the expected panes, and use this bundled command path when the CLI is absent from PATH."},"kind":"delegation-completed","inlineResult":"Resolver evidence approved."}
JSON
```

8. Return the complete terminal result to the delegating workflow. Do not poll the recipient, add acceptance or progress phases, or infer completion from pane output.

</workflow>

<handback_delivery>

Completion travels by push, never by pull. The sender's environment blocks polling loops by design, so a sender that "checks later" has no later to check in — it reads once, sees nothing, and moves on while the finished result sits on disk. The recipient closes the loop or nobody does.

**A durable result separates payload from signal.** The file carries the payload; one line sent into the sender's pane carries the signal. Write the file first, then send. `resultReference` names the complete scheme-bearing reference — `file:///absolute/path` for a local file — and `projection` carries the bounded summary, so the sender knows what arrived without opening it.

**The recipient delivers the handback by sending one line into the return address's pane**, using the `send` operation with normal trailing-Enter behavior. That send lands as a turn in the sender's session, which is what makes it a signal rather than a message the sender must go looking for. A `noEnter` send prefills the sender's editor and signals nothing.

**The sender states the handback at delegation time**, not after, by ending the `instruction` with two things the recipient cannot infer from the envelope: the exact command that reaches `sender.pane`, and the `<environment_traps>` conditions that break it. A recipient that discovers those traps by hitting them has already spent the turn the delegation was meant to buy. The pane itself needs no restating — it already travels as `sender.pane`.

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

Before release, import the bundled module with controlled `CommandRunner` implementations under the interaction-protocol and failure-simulation exceptions. Run the documented `run` form with an `agents` payload and require `status: "succeeded"`, `commandExitCode: 0`, and a public response; run `resolve-target` with pane-only, worktree-only, and combined caller evidence and require one inventory call, caller exclusion, and zero sends; fill one returned send template and require `response.data.input.trailing_enter_sent: true`; run `delegate` and `handback` with the documented envelope shapes and require the initiating coordination reference and `sender.pane` to survive. Cover every operation mapping, public JSON failure, mutation rejection before command construction, URI-bearing delegation result forms, repeated terminals, conflicting terminals, malformed input, missing Prowl, and CLI stdin dispatch. An unknown top-level delegation key is rejected instead of silently dropped.

</testing>

<failure_modes>

**A selectorless tab creation was rejected.** Claude applied the shared selector requirement to `tab-create`, even though the public operation accepts both selectorless and selected forms. The shared request builder hid the operation-specific shape. Build `tab-create` from its declared optional-selector contract and preserve optional `path` independently.

**An advertised operation had no construction branch.** Claude listed `open` in the public surface but grouped only list, agents, read, and send into the non-mutating workflow. Claude then had to infer the request shape. Keep every advertised operation in an explicit construction branch; `open` accepts empty arguments or one source-supplied `path`, always with explicit mutation authorization.

**A visible worktree was absent from `list`.** Claude inferred missing Prowl topology because a sidebar row had no listed pane. The row was known but not entered; `open` returned `resolution: exact-root`, `created_tab: true`, and the first pane UUID. Treat `list` as the terminal inventory and use authorized `open` for visible lazy activation.

**A delegation had no return path, so the operator became the message bus.** Claude asked a recipient to write a file, then had no signal that it had. Polling loops are blocked in the environment, so Claude read the pane once, saw nothing, and moved on — while a complete result sat on disk. The operator ended up carrying the answer between the two agents by hand. The delegation carried no return address, so the recipient could not push and the sender could not pull. Send the sender's own pane id, the exact handback command, and `<environment_traps>` in the delegation itself, and require the recipient to send one line on completion per `<handback_delivery>`.

**A single read was mistaken for a terminal answer.** Claude treated one empty pane read as evidence the recipient had produced nothing, when it proved only that nothing was on screen at that instant. A read establishes the pane's state at the moment it ran and never establishes that a delegation is incomplete. Completion arrives as the recipient's handback; its absence is an open delegation, not a negative result.

**An overridden socket was read as an empty environment.** Claude pointed the CLI at a non-default socket, saw an inventory with none of the expected panes, and concluded the recipient was gone. The socket belonged to a different instance — a verification harness, not the operator's live application. Confirm the inventory contains the expected panes before concluding a target is absent, per `<environment_traps>`.

**Target resolution was rebuilt around scratch files.** Claude wrote the `agents` result and discovery result through dynamic redirects under `$SP`. The dangerous-command guard terminated the command because the shell would open an unproved path with truncation. Claude then rewrote the same operation as a Python script, bypassing the stop instead of using a sanctioned capability. Invoke `resolve-target` over direct stdin, keep its returned JSON as the tool result, and stop when a guard terminates that command family; never reformulate the blocked operation.

</failure_modes>

<success_criteria>

- A successful public operation is mechanically established only when the bundled script exits zero and emits `schemaVersion: 1`, `status: "succeeded"`, `commandExitCode: 0`, and a public `response` object without exposing Prowl command grammar.
- Every positively identified Prowl participant retains complete public identities verbatim.
- Every delegation preserves its initiating coordination reference through exactly one completed, failed, rejected, or unavailable terminal handback.
- Every delegation's `instruction` ends with the exact command reaching `sender.pane` and the `<environment_traps>` conditions, so the recipient can push completion without discovering the environment first; the pane itself is read from the envelope, never restated as a separate field.
- A durable handback writes its file before sending, and the notification reaches the sender's pane as a submitted turn rather than editor prefill.
- One `resolve-target` invocation returns the checked inventory, complete caller and participants, non-caller path matches, and candidate-specific immediate-return send templates without sending.
- An operator-named target is reported as the supplied worktree or directory, never as a pane UUID the operator must verify.
- Terminal results carry complete inline content or an exact durable reference with a bounded projection.
- Unauthorized focus, key, creation, closure, and open requests fail before Prowl runs.
- Lazy activation is established by an authorized `open` result carrying `resolution: exact-root`, `created_tab: true`, and the complete returned pane identity.
- No workflow polls, invokes help, or depends on a separate environment-control skill.

</success_criteria>


<!-- Producer: src/plugins/coding-agents/skills/message-agents/SKILL.md -->

---
name: message-agents
description: >-
  ALWAYS invoke this skill when discovering a Prowl coding-agent recipient or sending facts, ownership proposals, state reports, authorizations, or acknowledgements to another agent pane.
argument-hint: "<JSON message request>"
allowed-tools: Skill, Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py":*), {{! tool('ask_user') !}}
---

<objective>
A source-owned coordination envelope delivered through `/operate-prowl` to one complete Prowl pane identity, with transport status kept distinct from acknowledgement, agreement, authorization, and ownership.
</objective>

<workflow>

1. Interpret `$ARGUMENTS` as one JSON message request containing `recipientPath` with the recipient's absolute worktree, repository, or working-directory path, `kind`, `subject`, `facts`, and any applicable coordination fields. The request may carry `toPane` only as a complete identity assertion from an upstream coordination plan. When required data is absent, stop and name it before discovery or delivery; never invent message data or ask for a pane UUID.
2. Invoke `/operate-prowl` once for `resolve-target` with the supplied path. Preserve the complete result. It returns the checked inventory, complete caller and participants, and non-caller candidates whose `sendRequestTemplate` already selects each pane with immediate-return mode and normal trailing-Enter behavior.
3. Require one selected candidate. When the request carries `toPane`, match it against the captured non-caller candidates before considering cardinality: exactly one matching candidate selects it, while zero or multiple matches stop with `invalid-identity`. Without `toPane`, use the sole candidate on `succeeded`; on `identity-ambiguous`, ask the operator to choose among the returned worktree and branch metadata, then select that exact candidate from the captured result without rerunning resolution; on `identity-unavailable`, report the exact detail and participant worktrees. NEVER select by title, focus, position, prose, or the caller's pane.
4. Build the bundled script's `discovery` input directly from the resolver result: `caller` is the returned caller, `targets` is the returned complete participant list, and `status` is `prowl-pane`. Set `toPane` from the selected candidate's complete participant. This source-owned bridge uses the captured resolver result directly; never write an intermediate file or run an ad hoc transformation script.
5. Build the bundled script's message request with the selected candidate's `toPane`, `kind`, `subject`, `facts`, optional `request`, optional `coordinationReference`, optional `mutationTarget`, optional `observedState`, and optional `accepted`. `recipientPath` has completed target resolution and never enters the envelope. `kind` is exactly `ownership-proposal`, `fact`, `acknowledgement`, `mutation-state`, or `mutation-authorization`. An acknowledgement, mutation-state report, or mutation authorization MUST reuse the active proposal UUID; an initiating proposal or fact MUST omit it so the adapter creates a new UUID. An acknowledgement MUST carry boolean `accepted`; every other kind omits it.
6. For a delegated mutation, use the source-owned handshake:
   - An `ownership-proposal` carries `mutationTarget` with exact `pane`, `worktree`, `branch`, `repository`, full `head`, and `status` values; pane, worktree, branch, and repository match the live recipient identity.
   - A `mutation-state` response carries the same target plus `observedState` with exact `worktree`, `branch`, `repository`, full `head`, and `status` values matching the live sender identity.
   - A `mutation-authorization` carries the checked target and observed state and targets that same live recipient. Any mismatch returns `invalid-identity` before delivery planning.
7. Pass the discovery and message request to the bundled script's `build` operation. It returns the complete `envelope` and a semantic `delivery` containing `toPane` and `text`.
8. Confirm the selected candidate template's pane equals the delivery's complete `toPane`, fill its null `text` with the delivery's exact text, and invoke `/operate-prowl` once with that request. NEVER alter its `pane` or `noWait`, construct a second request, use `noEnter`, or retry after the editor becomes free.
9. Pass the envelope and the exact environment result to the bundled script's `result` operation. Set `delivered` true only when `/operate-prowl` returned a complete checked `send` result with `status: "succeeded"`, `commandExitCode: 0`, and public `response.data.input.trailing_enter_sent: true`; preserve that complete result under `transport`. The bundled script rejects delivered status when any checked transport or submission field is absent or inconsistent. Prefilled text that remains in the recipient editor is not delivered.
10. Report the complete `coordinationReference`, checked `commandExitCode`, and delivery `status`. Once trailing Enter is confirmed, the turn is queued and no second send is needed. `delivered` means only that the environment capability accepted transport; it NEVER means acknowledged, agreed, authorized, or owned. Stop with the exact status and detail on `delivery-failed`, `invalid-identity`, `environment-unavailable`, or `invalid-schema`.

</workflow>

<command_forms>

Pass every payload over stdin. When the shell accepts multiline input:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" build <<'JSON'
{"discovery":{},"messageRequest":{}}
JSON

python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" result <<'JSON'
{"envelope":{},"delivered":false,"commandExitCode":1,"transport":{},"detail":"<exact-environment-detail>"}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"discovery":{},"messageRequest":{}}' | python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" build
printf '%s\n' '{"envelope":{},"delivered":false,"commandExitCode":1,"transport":{},"detail":"<exact-environment-detail>"}' | python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" result
```

</command_forms>

<constraints>

- ALWAYS preserve complete source-supplied agent, pane, worktree, branch, repository, run, coordination-reference, mutation-target, observed-state, and transport identities.
- ALWAYS report the selected target using the exact `recipientPath` supplied by the caller while using the resolved pane UUID only inside the delivery operation.
- ALWAYS invoke `/operate-prowl` for source-owned target resolution and delivery.
- ALWAYS retain each complete command result in the active tool context and feed it into the next source-owned operation; no scratch file or shell redirect is part of this workflow.
- NEVER scan transcript files, use another terminal multiplexer, or ask the operator to relay a message as a fallback.
- NEVER select an endpoint by title, focus, position, inferred prose, or an undeclared environment.
- NEVER convert transport success into acknowledgement, agreement, ownership, mutation authorization, or continuation state.

</constraints>

<testing>

Before release, exercise `coordination_reference`, `build_envelope`, `send_request`, `delivery_request`, and `delivery_result` with complete resolver identities and controlled environment-result payloads. Run the documented `build` stdin form and require `delivery.status: "ready"`; run the documented `result` form with a complete successful `send` payload and require `status: "delivered"`, then remove or alter each required transport field and require rejection. The matrix covers authoritative `toPane` selection from ambiguous candidates, caller exclusion, optional run-identity preservation and rejection, accepted and rejected acknowledgements, all message kinds, complete HEAD/status validation, exact mutation target/state matching, malformed identities and optional fields, and transport results that never establish acknowledgement, agreement, authorization, or ownership.

</testing>

<failure_modes>

**Transport success was inferred from an exit code alone.** Claude passed `delivered: true` and `commandExitCode: 0` without the checked `/operate-prowl` result, so downstream output claimed delivery with no transport evidence to inspect. The exit code establishes only one field of the environment result. Pass the complete checked `send` result under `transport`; the bundled script rejects delivered status when any required field is absent or inconsistent.

**Continuation prose remained in the editor.** Claude treated a successful immediate-return send as a submitted turn even though the operator could still see editable text. Require `response.data.input.trailing_enter_sent: true`; a prefill or absent submission field is a delivery failure.

**A request was sent with no way for the answer to come back.** Claude asked a recipient to produce a result and sent no return path, then had no signal when the recipient finished. Polling is blocked by design, so the sender read the recipient's pane once, saw nothing, and moved on while the finished result sat on disk — leaving the operator to carry it between the two agents. A message that asks for something carries the sender's own complete pane and the exact command that reaches it, so the recipient can send one line back on completion.

**A pane UUID was requested from the operator.** Claude asked which pane to send to, when the operator had already named the target the only way they can — by worktree or working directory. Resolve the operator's naming against the live inventory and report the target back in the same terms.

**A blocked redirect was rewritten as another program.** Claude redirected public inventory and discovery JSON into `$SP/agents.json` and `$SP/discovery.json`. The dangerous-command guard terminated the dynamic truncating redirect and instructed Claude to ask for authority. Claude wrote a Python replacement and continued, discarding the guard result. Use `/operate-prowl`'s `resolve-target` result directly in the active tool context. When a guard terminates a command family, stop that family and follow the sanctioned operation or ask the operator; never reformulate it.

</failure_modes>

<success_criteria>

- Target resolution passes only with one complete non-caller candidate selected from the complete checked inventory for `recipientPath`, with any supplied `toPane` matching that candidate.
- Build passes only with one validated envelope and one semantic delivery bound to the target's complete pane UUID.
- Delivery passes only after `/operate-prowl` returns a checked successful result whose public input record confirms trailing Enter was sent; every failure preserves its exact status, detail, and command exit code when present.
- Caller, recipient, mutation-target, and observed-state identities validate before delivery.
- Transport delivery remains distinct from acknowledgement, agreement, authorization, ownership, and continuation.

</success_criteria>


<!-- Producer: src/plugins/coding-agents/skills/coordinate-agents/SKILL.md -->

---
name: coordinate-agents
description: >-
  ALWAYS invoke this skill when coding agents in separate worktrees may overlap, depend on each other, share an external blocker, or need ownership coordination.
allowed-tools: Skill
---

<objective>
A structured coordination decision that preserves independent workflow ownership.
</objective>

<evidence_model>

Use only explicit SPX facts, public runtime projections, checked command results, and operator-confirmed external changes as authoritative evidence. Treat prose inference as advisory. A missing authoritative fact is a signal gap, never permission to scan harness transcripts.

</evidence_model>

<workflow>

1. Identify every participant with complete agent, pane, worktree, branch, repository, and applicable run identities. Capture the complete current caller from `/operate-prowl`'s resolver result before planning messages. An operator names a participant by worktree, repository, or working directory rather than by pane UUID; resolve that naming to a complete identity through `/operate-prowl`'s operator-target resolution, and report participants back to the operator in the terms they used.
2. Classify the relationship from authoritative evidence:
   - `ownership-overlap`: paths, concerns, or an external mutation overlap.
   - `dependency-handoff`: one workflow has a checked fact another consumes.
   - `shared-blocker`: workflows name the same authoritative external-condition key.
   - `independent`: authoritative evidence explicitly establishes no overlap, dependency, shared mutation, or correlated blocker.
   - `signal-gap`: authoritative evidence is absent or cannot establish either a relationship or independence. Advisory prose alone ALWAYS maps here.
3. Emit the structured verdict before delivery:

```json
{
  "status": "coordination-needed | no-coordination | signal-gap",
  "reason": "ownership-overlap | dependency-handoff | shared-blocker | independent | insufficient-evidence",
  "participants": [],
  "operatorAction": null,
  "messages": []
}
```

For a shared blocker, replace `operatorAction: null` with this complete object:

```json
{
  "externalConditionKey": "<complete authoritative key>",
  "status": "<operator-confirmed status>"
}
```

Preserve every input participant in the verdict's `participants` array, dropping none — including a participant the classified relationship does not involve. An operator-named target resolved in step 1 joins that array as a complete identity, because it is a party to the coordination; resolution adds, never replaces. The array therefore holds exactly the input participants plus any resolved target, and never a participant no evidence names.

Each message carries every field in the source-owned message contract: complete `recipientPath` equal to the recipient participant's absolute worktree, complete `toPane` UUID, `kind`, `subject`, `facts`, `request`, `coordinationReference`, `mutationTarget`, `observedState`, and `accepted`. `facts` is always an array of strings, including branches with exactly one fact. Use null for every field that does not apply. `kind` MUST be exactly `ownership-proposal`, `fact`, `acknowledgement`, `mutation-state`, or `mutation-authorization`. Omit or set `coordinationReference` to null for initiating proposals and facts so `/message-agents` creates a UUID; every response kind preserves the active proposal UUID. Only an `acknowledgement` carries boolean `accepted`; every other kind carries `accepted: null`.

Use these branch-owned payloads:

| Branch                      | `subject`                          | `facts`                                                                                                               | `request`                                                                                                   |
| --------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Ownership proposal          | `Ownership overlap`                | one `overlap=<path-or-concern>` string per checked overlapping item                                                   | `Accept or reject this ownership proposal.`                                                                 |
| Delegated-mutation proposal | `Delegated mutation ownership`     | `target identity and state are authoritative`                                                                         | `Report exact pre-mutation state and accept or reject ownership.`                                           |
| Dependency handoff          | `Dependency fact`                  | the checked dependency fact only                                                                                      | null                                                                                                        |
| Production request          | `Dependency production request`    | the exact checked `requestedArtifact` value, then `returnPane=<requester-pane>` and `handbackCommand=<exact-command>` | `Send the handback command when the result is written.`                                                     |
| Shared-blocker recovery     | `Shared blocker restored`          | `externalConditionKey=<key>` and `status=<operator-confirmed-status>`                                                 | null                                                                                                        |
| Mutation authorization      | `Delegated mutation authorization` | `accepted ownership and observed state match the target`                                                              | `Recreate the required change in the target worktree; do not mutate or transfer from the sibling worktree.` |

4. Apply the protocol:

- A checked path or concern overlap produces an `ownership-proposal` with one `overlap=<path-or-concern>` fact per overlapping item; its boundary remains proposed until a matching accepted acknowledgement arrives.
- A dependency handoff sends `kind: "fact"` with checked facts and `request: null`, not another workflow's continuation instructions.
- A dependency handoff that asks another workflow to *produce* something is a production request — its own branch, distinct from handing over an already-checked dependency fact. It still sends `kind: "fact"`. Its first `facts` string is the exact checked `requestedArtifact` value unchanged, with no field-name prefix; the next two are exactly `returnPane=<requester-pane>` and `handbackCommand=<exact-command>`. Its `request` is exactly `Send the handback command when the result is written.` The requester cannot poll — polling loops are blocked by design — so a request with no return path is one the requester can never learn the answer to, and the operator ends up relaying it by hand. When the produced artifact is a file, the file carries the payload and the handback carries only the signal and the complete path. Emit `status: "signal-gap"`, `reason: "insufficient-evidence"`, and no message when the requester's own pane is not among the authoritative participants, since a return path cannot be fabricated.
- A delegated mutation begins with an `ownership-proposal` whose `mutationTarget` contains the recipient's exact pane UUID, worktree path, branch, repository, full HEAD SHA, and status. The recipient performs no mutation until it returns both a matching `acknowledgement` with `accepted: true` and a `mutation-state` message with the same coordination reference and an `observedState` containing its exact worktree, branch, repository, full HEAD SHA, and status.
- When delegated-mutation evidence has no `observedState`, emit one ownership proposal carrying the exact target and request the state report.
- Treat `acceptedAcknowledgement` as authoritative only when its kind is `acknowledgement`, `accepted` is true, its coordination reference equals the active proposal reference, its sender is the target participant, and its recipient is the coordinating participant. When observed state exists but acknowledgement evidence is missing, rejected, or mismatched, emit `status: "coordination-needed"`, `reason: "ownership-overlap"`, and no message.
- When any observed worktree, branch, repository, HEAD, or status value differs from the target, emit `status: "coordination-needed"`, `reason: "ownership-overlap"`, and no message. A mismatch produces no authorization.
- Emit one `mutation-authorization` only when the accepted acknowledgement is valid and every observed value matches. Target the exact recipient pane, preserve the active coordination reference, echo the target and observed state, and set `request` exactly to `Recreate the required change in the target worktree; do not mutate or transfer from the sibling worktree.`
- Every sibling worktree stays read-only to both workflows. Transfer an exact commit only through a separate ownership proposal and accepted acknowledgement; delegated-mutation authorization never transfers a sibling commit.
- A shared blocker produces exactly one non-null `operatorAction` carrying its complete `externalConditionKey` and operator-confirmed `status`. When restoration is operator-confirmed, keep that action record. The current caller consumes the recovery fact from the verdict and `operatorAction`; produce one `kind: "fact"` recovery message for every other affected participant.
- Independent work produces `status: "no-coordination"`, `reason: "independent"`, `operatorAction: null`, and no message only when authoritative evidence explicitly establishes independence. Blocker evidence with distinct complete `externalConditionKey` values and no other relationship evidence establishes that the blockers are independent.
- A signal gap produces `status: "signal-gap"`, `reason: "insufficient-evidence"`, `operatorAction: null`, and no message.

5. Remove any planned message whose `toPane` equals the complete current caller pane, then invoke `/message-agents` once for each remaining message, passing its complete `recipientPath`, `toPane`, and semantic fields unchanged. NEVER call Prowl directly from this skill.
6. Preserve each delivery result separately from the coordination verdict. A delivery counts only when `/message-agents` reports a checked submitted turn; prefilled text or transport without trailing-Enter evidence remains a delivery failure. Each operating workflow re-evaluates its own state after receiving facts.

</workflow>

<constraints>

- NEVER prescribe workflow-specific retries, reconstruct another workflow's successful state, or choose its checkpoint or continuation.
- NEVER establish ownership from a sent proposal; only a matching accepted acknowledgement establishes the boundary.
- NEVER combine blockers whose authoritative external-condition keys differ.
- NEVER authorize a delegated mutation before exact target/state verification, or authorize editing, staging, stashing, checkout, reset, or commit in a sibling worktree.
- NEVER send directly; delivery belongs to `/message-agents`.
- NEVER plan or deliver a message to the complete current caller pane.
- NEVER wait on another workflow by polling its pane, re-reading it on a timer, or treating one empty read as evidence it produced nothing. A read establishes that pane's state at the instant it ran, never that a request is unanswered.
- NEVER leave the operator to carry a result between two workflows. When a request needs an answer, the request itself carries the return path.

</constraints>

<failure_modes>

**A production request went out with no way to answer it.** Claude classified a dependency handoff correctly and sent the checked need, but omitted `returnPane=` and `handbackCommand=`. The recipient produced the result and had no address to send it to. Claude could not poll — polling loops are blocked by design — so it read the recipient's pane once, saw nothing, and moved on while the finished result sat on disk; the operator carried the answer between the two workflows by hand. A production request without both facts is unanswerable by construction.

**One empty pane read was treated as a negative result.** Claude read a recipient's pane, saw nothing relevant, and concluded the workflow had produced nothing. The read established that pane's state at the instant it ran and nothing more. Absence of a handback is an open request; only a returned message closes it.

**A resolved operator target silently changed the participant set.** Claude resolved an operator-named worktree to a complete identity and then returned only that identity, dropping an input participant the classified relationship did not involve. Every input participant is preserved and the resolved target is added; resolution never replaces the array it augments.

</failure_modes>

<success_criteria>

- The structured verdict names whether coordination is needed, its authoritative reason, complete participants, and protocol-valid messages whose delivery result proves submission rather than editor prefill.
- Shared blockers yield one human-owned action, expose the recovery fact to the current workflow in the verdict, and message every other affected workflow without centralizing execution.
- Delegated mutations carry an exact target envelope, require an exact pre-mutation state report, and produce no authorization on any identity mismatch.
- Independent work and signal gaps produce no message.

</success_criteria>

</code></pre>

The authoritative coordination evidence (JSON-encoded):

```json
{input_json}
```
