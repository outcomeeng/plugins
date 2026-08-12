---
name: message-agents
description: >-
  ALWAYS invoke this skill when discovering a Prowl coding-agent recipient or sending facts, ownership proposals, state reports, authorizations, or acknowledgements to another agent pane.
argument-hint: "<JSON message request>"
allowed-tools: Skill, Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py":*), AskUserQuestion
---

<objective>
A source-owned coordination envelope delivered to one complete Prowl pane identity, with transport status kept distinct from acknowledgement, agreement, authorization, and ownership.
</objective>

<workflow>

1. Read `$ARGUMENTS`. When it is empty or whitespace, stop with `invalid-schema` and require one JSON message request containing `recipientPath`, `kind`, `subject`, and `facts`; perform no discovery or delivery. Otherwise interpret it as that request, with `recipientPath` holding the recipient's absolute worktree, repository, or working-directory path and with any applicable coordination fields. The request may carry `toPane` only as a complete identity assertion from an upstream coordination plan. When required data is absent, stop and name it before discovery or delivery; never invent message data or ask for a pane UUID.
2. Invoke `/operate-prowl` once for `resolve-target` with the supplied path. Preserve the complete result. It returns the checked inventory, complete caller and participants, and non-caller candidates whose `sendRequestTemplate` already selects each pane with immediate-return mode and normal trailing-Enter behavior.
3. Require a complete resolved caller and one selected candidate. On `identity-ambiguous` with `caller: null`, report the exact detail as an unresolved caller-identity conflict and stop; never ask the operator to select from the empty candidate set. Otherwise, when the request carries `toPane`, match it against the captured non-caller candidates before considering cardinality: exactly one matching candidate selects it, while zero or multiple matches stop with `invalid-identity`. Without `toPane`, use the sole candidate on `succeeded`. On `identity-ambiguous`, use `AskUserQuestion` for one single-select question: number candidates in resolver order, show each candidate's complete pane, worktree, branch, and repository, and map the answer back to that exact captured candidate and its `sendRequestTemplate` without rerunning resolution. When the runtime's option cap is below the candidate count, include the complete numbered inventory in the question and accept an exact candidate number through its free-form response; never omit a candidate. On `identity-unavailable`, report the exact detail and participant worktrees. NEVER select by title, focus, position, prose, or the caller's pane.
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

Recorded exercised payload/results:

- `build` with a complete resolver-selected recipient and a `fact` request → one envelope and `delivery.status: "ready"` for that recipient pane.
- `result` with `delivered: true`, matching zero exit codes, `status: "succeeded"`, and `response.data.input.trailing_enter_sent: true` → `status: "delivered"`; changing the trailing-Enter field to false → `invalid-schema`.
- `result` with `delivered: false`, exit code 7, and `detail: "transport rejected"` → `status: "delivery-failed"` while acknowledgement, agreement, and ownership remain false.

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
