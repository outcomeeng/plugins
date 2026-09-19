---
name: message-agents
description: >-
  ALWAYS invoke this skill when sending a message record to a registered agent-mail name with its one-line doorbell, discovering a Prowl coding-agent recipient, or sending facts, ownership proposals, state reports, authorizations, or acknowledgements to another agent pane.
argument-hint: "<JSON message request>"
allowed-tools: Bash(printf:*), Bash(python3 "${SKILL_DIR}/scripts/agent_message.py":*), request_user_input
---

<objective>
One message delivered on the route its request selects — a message record in the agent-mail store with its one-line doorbell, or a source-owned coordination envelope submitted into one complete Prowl pane — with delivery kept distinct from acknowledgement, agreement, authorization, and ownership.
</objective>

<route_selection>

The request shape selects the route. A request carrying `recipient` as an agent-mail name, `correlation`, `body`, and `ackRequired` is a mail request and follows `<mail_route>`. A request carrying `recipientPath`, `facts`, and a pane-bound kind and no `correlation` or `body` is a Prowl request and follows `<workflow>`. A request that mixes the two is `invalid-schema`; the bundled script rejects fields outside the selected route's shape.

</route_selection>

<mail_route>

1. Read `$ARGUMENTS` as one JSON message request with exactly `kind`, `correlation`, `sender`, `recipient`, `subject`, `body`, and `ackRequired`, plus `authority` only on a same-worktree `delegation-request`, plus an optional `doorbell` endpoint. `sender` is the caller's own registered agent-mail name and `recipient` is one registered name. `kind` is one of `order`, `fact`, `question`, `answer`, `delegation-request`, `delegation-completed`, `delegation-failed`, `delegation-rejected`, or `delegation-unavailable`. `correlation` is the thread every reply to one exchange shares. A same-worktree `delegation-request` carries `authority` with exactly `owner` equal to `sender` and `gitMutation: false`; it carries no write scope, because the recipient reads the shared tree and returns its result in the mail record, so an `authority` naming `writeScope` reaches no record, and neither does a request without `authority`. The record body opens with that authority rendered. `doorbell` names where the recipient's pane is found and nothing else: `{"recipientPath": "<absolute worktree, repository, or working-directory path>"}` for a Prowl pane, or `{"agent": "<the herdr agent name>"}` for a herdr pane. `doorbell` never enters the record; remove it from the request before step 2.
2. Pass the request to the bundled script's `mail-request` operation. It returns the `record` and the complete `capability` send request for the agent-mail capability.
3. Use skill `coding-agents:operate-agent-mail` once with that `capability` request unchanged. Preserve its complete result.
4. Pass the capability result to the bundled script's `mail-result` operation as `capabilityResult`. A `succeeded` result whose `data.record` carries the store-assigned `id` returns `status: "delivered"` with the `doorbell.text` line `[<sender>] mail <id>`; any other capability result returns `delivery-failed` with the capability's status and detail preserved. Delivery is the record in the store; stop here on `delivery-failed`.
5. Resolve the doorbell endpoint. Without `doorbell`, ring nothing: report the delivered record with `doorbell.submitted: false` and say that no endpoint was named. With `recipientPath`, use skill `coding-agents:operate-prowl` once for `resolve-target` with that path, exactly as `<workflow>` step 2 does, and select the candidate by the same rules as `<workflow>` step 3; on `identity-unavailable` or an unresolved caller identity, report the exact detail beside the delivered record and ring nothing. With `agent`, the herdr capability selects the session by that name and no resolution runs.
6. Ring the doorbell: send exactly `doorbell.text` and nothing else into the resolved endpoint. For a Prowl pane, fill the selected candidate's `sendRequestTemplate` `text` with `doorbell.text` and use skill `coding-agents:operate-prowl` once with that request; pass the complete checked `send` result back to `mail-result` as `doorbellTransport` beside the same `capabilityResult`, and `doorbell.submitted` is true only with `status: "succeeded"`, `commandExitCode: 0`, and `response.data.input.trailing_enter_sent: true`. For a herdr pane, use skill `coding-agents:operate-herdr` once for `prompt` with the `agent` selector and `doorbell.text`; a herdr prompt carries no trailing-Enter record, so `mail-result` receives no `doorbellTransport`, reports `doorbell.submitted: false`, and the herdr `prompt` result is reported beside it as the doorbell's own evidence. No JSON and no record body reaches a pane. An unsubmitted doorbell leaves the message delivered and is reported beside it; never send the doorbell twice.
7. Report the store-assigned `id`, `correlation`, `status`, `doorbell`, and the recipient by its registered name. `delivered` means the record exists in the store; it NEVER means acknowledged, agreed, authorized, or owned. Acknowledgement is the recipient's separate receipt through the agent-mail capability.
8. To resolve a doorbell that arrives in the caller's own pane, pass its `line` and the `agents` names from the live inventory — the agent-mail registrations or the environment capability's agent list — to the bundled script's `doorbell` operation. It returns the `sender` and `id`, and rejects a line whose sender is absent from that inventory; then read the record through the agent-mail capability's `inbox`.

</mail_route>

<workflow>

1. Read `$ARGUMENTS`. When it is empty or whitespace, stop with `invalid-schema` and require one JSON message request containing `recipientPath`, `kind`, `subject`, and `facts`; perform no discovery or delivery. Otherwise interpret it as that request, with `recipientPath` holding the recipient's absolute worktree, repository, or working-directory path and with any applicable coordination fields. The request may carry `toPane` only as a complete identity assertion from an upstream coordination plan and may carry `handback` only as the complete structured block returned by `/operate-prowl plan-handback`. When required data is absent, stop and name it before discovery or delivery; never invent message data or ask for a pane UUID.
2. Use skill `coding-agents:operate-prowl` once for `resolve-target` with the supplied path. Preserve the complete result. It returns the checked inventory, complete caller and participants, and non-caller candidates whose `sendRequestTemplate` already selects each pane with immediate-return mode and normal trailing-Enter behavior.
3. Require a complete resolved caller and one selected candidate. On `identity-ambiguous` with `caller: null`, report the exact detail as an unresolved caller-identity conflict and stop; never ask the operator to select from the empty candidate set. Otherwise, when the request carries `toPane`, match it against the captured non-caller candidates before considering cardinality: exactly one matching candidate selects it, while zero or multiple matches stop with `invalid-identity`. Without `toPane`, use the sole candidate on `succeeded`. On `identity-ambiguous`, use `request_user_input` for one single-select question: number candidates in resolver order, show each candidate's complete pane, worktree, branch, and repository, and map the answer back to that exact captured candidate and its `sendRequestTemplate` without rerunning resolution. When the runtime's option cap is below the candidate count, include the complete numbered inventory in the question and accept an exact candidate number through its free-form response; never omit a candidate. On `identity-unavailable`, report the exact detail and participant worktrees. NEVER select by title, focus, position, prose, or the caller's pane.
4. Build the bundled script's `discovery` input directly from the resolver result: `caller` is the returned caller, `targets` is the returned complete participant list, and `status` is `prowl-pane`. Set `toPane` from the selected candidate's complete participant. This source-owned bridge uses the captured resolver result directly; never write an intermediate file or run an ad hoc transformation script.
5. Build the bundled script's message request with the selected candidate's `toPane`, `kind`, `subject`, `facts`, optional `request`, optional `handback`, optional `coordinationReference`, optional `mutationTarget`, optional `observedState`, and optional `accepted`. `recipientPath` has completed target resolution and never enters the envelope. `kind` is exactly `ownership-proposal`, `fact`, `acknowledgement`, `mutation-state`, or `mutation-authorization`. An acknowledgement, mutation-state report, or mutation authorization MUST reuse the active proposal UUID; an initiating proposal or fact MUST omit it so the adapter creates a new UUID. An acknowledgement MUST carry boolean `accepted`; every other kind omits it. Only a `fact` production request carries `handback`. When it does, use skill `coding-agents:operate-prowl` for `plan-handback` with the captured caller as sender, the selected participant as recipient, and that block's semantic `completionText`; require a successful result whose returned handback matches the request byte-for-byte, and pass the complete result to the bundled script as top-level `handbackPlan`. Reject top-level `command`, `handbackCommand`, `returnPane`, or `adapterPath` fields and never reconstruct the block.
6. For a delegated mutation, use the source-owned handshake:
   - An `ownership-proposal` carries `mutationTarget` with exact `pane`, `worktree`, `branch`, `repository`, full `head`, and `status` values; pane, worktree, branch, and repository match the live recipient identity.
   - A `mutation-state` response carries the same target plus `observedState` with exact `worktree`, `branch`, `repository`, full `head`, and `status` values matching the live sender identity.
   - A `mutation-authorization` carries the checked target and observed state and targets that same live recipient. Any mismatch returns `invalid-identity` before delivery planning.
7. Pass the discovery and message request to the bundled script's `build` operation. It returns the complete `envelope` and a semantic `delivery` containing `toPane` and `text`.
8. Confirm the selected candidate template's pane equals the delivery's complete `toPane`, fill its null `text` with the delivery's exact text, and use skill `coding-agents:operate-prowl` once with that request. NEVER alter its `pane` or `noWait`, construct a second request, use `noEnter`, or retry after the editor becomes free.
9. Pass the envelope and the exact environment result to the bundled script's `result` operation. Set `delivered` true only when the Prowl capability returned a complete checked `send` result with `status: "succeeded"`, `commandExitCode: 0`, and public `response.data.input.trailing_enter_sent: true`; preserve that complete result under `transport`. The bundled script rejects delivered status when any checked transport or submission field is absent or inconsistent. Prefilled text that remains in the recipient editor is not delivered.
10. Report the complete `coordinationReference`, checked `commandExitCode`, and delivery `status`. Once trailing Enter is confirmed, the turn is queued and no second send is needed. `delivered` means only that the environment capability accepted transport; it NEVER means acknowledged, agreed, authorized, or owned. Stop with the exact status and detail on `delivery-failed`, `invalid-identity`, `environment-unavailable`, or `invalid-schema`.

</workflow>

<command_forms>

Pass every payload over stdin. When the shell accepts multiline input:

```bash
python3 "${SKILL_DIR}/scripts/agent_message.py" mail-request <<'JSON'
{"messageRequest":{"kind":"fact","correlation":"<thread>","sender":"<own-name>","recipient":"<name>","subject":"<subject>","body":"<body>","ackRequired":false}}
JSON

python3 "${SKILL_DIR}/scripts/agent_message.py" mail-result <<'JSON'
{"capabilityResult":{},"doorbellTransport":null}
JSON

python3 "${SKILL_DIR}/scripts/agent_message.py" doorbell <<'JSON'
{"line":"[<sender>] mail <id>","agents":[]}
JSON

python3 "${SKILL_DIR}/scripts/agent_message.py" build <<'JSON'
{"discovery":{},"messageRequest":{},"handbackPlan":null}
JSON

python3 "${SKILL_DIR}/scripts/agent_message.py" result <<'JSON'
{"envelope":{},"delivered":false,"commandExitCode":1,"transport":{},"detail":"<exact-environment-detail>"}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"messageRequest":{"kind":"fact","correlation":"<thread>","sender":"<own-name>","recipient":"<name>","subject":"<subject>","body":"<body>","ackRequired":false}}' | python3 "${SKILL_DIR}/scripts/agent_message.py" mail-request
printf '%s\n' '{"capabilityResult":{},"doorbellTransport":null}' | python3 "${SKILL_DIR}/scripts/agent_message.py" mail-result
printf '%s\n' '{"line":"[<sender>] mail <id>","agents":[]}' | python3 "${SKILL_DIR}/scripts/agent_message.py" doorbell
printf '%s\n' '{"discovery":{},"messageRequest":{},"handbackPlan":null}' | python3 "${SKILL_DIR}/scripts/agent_message.py" build
printf '%s\n' '{"envelope":{},"delivered":false,"commandExitCode":1,"transport":{},"detail":"<exact-environment-detail>"}' | python3 "${SKILL_DIR}/scripts/agent_message.py" result
```

Every operation exits 0 on its success shape — `record` present for `mail-request`, `status: "delivered"` for `mail-result`, `id` present for `doorbell`, `delivery.status: "ready"` for `build`, `status: "delivered"` for `result` — and 2 otherwise. On `invalid-schema` or `invalid-identity` the output is the three-field `{schemaVersion, status, detail}` object. On `delivery-failed` the output is the full delivery result: `mail-result` returns `status`, `capabilityStatus`, `detail`, `commandExitCode`, and the three coordination flags set to false; `result` returns `status`, `coordinationReference`, `commandExitCode`, `transport`, `detail`, and the same three flags.

</command_forms>

<constraints>

- ALWAYS preserve complete source-supplied agent, pane, worktree, branch, repository, run, coordination-reference, mutation-target, observed-state, and transport identities.
- ALWAYS report the selected target using the exact `recipientPath` supplied by the caller on the Prowl route, and the registered `recipient` name on the mail route, while using a resolved pane UUID only inside the delivery or doorbell operation.
- ALWAYS invoke `coding-agents:operate-prowl` for source-owned target resolution and Prowl delivery, `coding-agents:operate-agent-mail` for mail delivery and receipt, and `coding-agents:operate-herdr` for a herdr doorbell; the bundled script executes no command and reads no store.
- ALWAYS send a doorbell as exactly the one line `[<sender>] mail <id>` into an endpoint the request named and the environment capability resolved; no JSON and no record body reaches a pane, and no message record is written under `.spx/`.
- ALWAYS preserve a production request's complete source-generated `handback` block unchanged.
- ALWAYS require the matching complete successful `/operate-prowl plan-handback` result before building a production request.
- NEVER accept or construct a handback command, return-pane field, or cross-skill adapter path.
- ALWAYS retain each complete command result in the active tool context and feed it into the next source-owned operation; no scratch file or shell redirect is part of this workflow.
- NEVER scan transcript files, use another terminal multiplexer, or ask the operator to relay a message as a fallback.
- NEVER select an endpoint by title, focus, position, inferred prose, or an undeclared environment.
- NEVER convert transport success or a stored record into acknowledgement, agreement, ownership, mutation authorization, or continuation state.

</constraints>

<testing>

Before release, exercise `coordination_reference`, `build_envelope`, `send_request`, `delivery_request`, and `delivery_result` with complete resolver identities and controlled environment-result payloads. Run the documented `build` stdin form and require `delivery.status: "ready"`; run the documented `result` form with a complete successful `send` payload and require `status: "delivered"`, then remove or alter each required transport field and require rejection. The matrix covers authoritative `toPane` selection from ambiguous candidates, caller exclusion, optional run-identity preservation and rejection, accepted and rejected acknowledgements, all message kinds, complete HEAD/status validation, exact mutation target/state matching, a production request that preserves the source-generated handback block only with its matching complete `plan-handback` result, rejection of caller-authored executable handback fields, malformed identities and optional fields, and transport results that never establish acknowledgement, agreement, authorization, or ownership.

The mail route's exercised properties: every record kind maps to a record the agent-mail capability accepts unchanged; the capability's checked `send` result over the store's captured reply maps to `delivered` with the store id and the doorbell line, and a rejected or absent store maps to `delivery-failed` with the capability's status and detail; generated doorbells parse back to their sender and id; a sender absent from the inventory and a line carrying more than the doorbell are rejected; a delivered result requires every checked capability field and a zero exit code; a same-worktree delegation without complete authority reaches no record.

Recorded exercised payload/results:

- `mail-request` with a `fact` request → one `record` and the `capability` send request; `mail-result` with the capability's succeeded result → `status: "delivered"`, the store id, and `doorbell.text` `[<sender>] mail <id>` with `submitted: false` until a checked doorbell transport is supplied.
- `build` with a complete resolver-selected recipient and a `fact` request → one envelope and `delivery.status: "ready"` for that recipient pane.
- `result` with `delivered: true`, matching zero exit codes, `status: "succeeded"`, and `response.data.input.trailing_enter_sent: true` → `status: "delivered"`; changing the trailing-Enter field to false → `invalid-schema`.
- `result` with `delivered: false`, exit code 7, and `detail: "transport rejected"` → `status: "delivery-failed"` while acknowledgement, agreement, and ownership remain false.

</testing>

<failure_modes>

**Transport success was inferred from an exit code alone.** Claude passed `delivered: true` and `commandExitCode: 0` without the checked `/operate-prowl` result, so downstream output claimed delivery with no transport evidence to inspect. The exit code establishes only one field of the environment result. Pass the complete checked `send` result under `transport`; the bundled script rejects delivered status when any required field is absent or inconsistent.

**Continuation prose remained in the editor.** Claude treated a successful immediate-return send as a submitted turn even though the operator could still see editable text. Require `response.data.input.trailing_enter_sent: true`; a prefill or absent submission field is a delivery failure.

**A request was sent with no way for the answer to come back.** Claude asked a recipient to produce a result and sent no return path, then had no signal when the recipient finished. Polling is blocked by design, so the sender read the recipient's pane once, saw nothing, and moved on while the finished result sat on disk. A production request carries the complete handback block returned by `/operate-prowl plan-handback`, so the recipient can send one line back on completion.

**A pane UUID was requested from the operator.** Claude asked which pane to send to, when the operator had already named the target the only way they can — by worktree or working directory. Resolve the operator's naming against the live inventory and report the target back in the same terms.

**A blocked redirect was rewritten as another program.** Claude redirected public inventory and discovery JSON into `$SP/agents.json` and `$SP/discovery.json`. The dangerous-command guard terminated the dynamic truncating redirect and instructed Claude to ask for authority. Claude wrote a Python replacement and continued, discarding the guard result. Use `/operate-prowl`'s `resolve-target` result directly in the active tool context. When a guard terminates a command family, stop that family and follow the sanctioned operation or ask the operator; never reformulate it.

</failure_modes>

<success_criteria>

- Target resolution passes only with one complete non-caller candidate selected from the complete checked inventory for `recipientPath`, with any supplied `toPane` matching that candidate.
- Build passes only with one validated envelope and one semantic delivery bound to the target's complete pane UUID.
- A production request preserves one source-generated handback block only when the complete successful `plan-handback` result carries the same block, and rejects every caller-authored executable handback field.
- Delivery passes only after `/operate-prowl` returns a checked successful result whose public input record confirms trailing Enter was sent; every failure preserves its exact status, detail, and command exit code when present.
- A mail delivery passes only when `mail-result` returns `status: "delivered"` from a `succeeded` capability result whose `data.record` carries the store-assigned `id`; the doorbell text is `[<sender>] mail <id>` and `doorbell.submitted` is true only with a checked Prowl `send` result carrying `trailing_enter_sent: true`.
- A `delivery-failed` mail result preserves the capability's exact status and detail, and a same-worktree `delegation-request` without complete authority produces no record.
- Caller, recipient, mutation-target, and observed-state identities validate before delivery.
- Transport delivery remains distinct from acknowledgement, agreement, authorization, ownership, and continuation.

</success_criteria>
