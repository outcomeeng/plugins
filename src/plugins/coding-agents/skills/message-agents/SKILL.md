---
name: message-agents
description: >-
  ALWAYS invoke this skill when discovering a Prowl coding-agent recipient or sending facts, ownership proposals, state reports, authorizations, or acknowledgements to another agent pane.
allowed-tools: Skill, Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py":*)
---

<objective>
A source-owned coordination envelope delivered through `/operate-prowl` to one complete Prowl pane identity, with transport status kept distinct from acknowledgement, agreement, authorization, and ownership.
</objective>

<workflow>

1. Invoke `/operate-prowl` for the `agents` operation. Require `status: "succeeded"`; stop with its exact status and detail otherwise.
2. Pass the public agent array and the active `PROWL_PANE_ID` or `PROWL_WORKTREE_PATH` environment evidence to the bundled script's `discover` operation over stdin. The script returns one complete caller and all complete targets.
3. Require `status: "prowl-pane"`, one complete caller identity, and one target selected by its complete `pane` UUID. Stop with the exact status and detail on `unsupported-terminal`, `caller-ambiguous`, or `invalid-schema`; NEVER select by title, focus, position, or prose.
4. Build a message request with `toPane`, `kind`, `subject`, `facts`, optional `request`, optional `coordinationReference`, optional `mutationTarget`, optional `observedState`, and optional `accepted`. `kind` is exactly `ownership-proposal`, `fact`, `acknowledgement`, `mutation-state`, or `mutation-authorization`. An acknowledgement, mutation-state report, or mutation authorization MUST reuse the active proposal UUID; an initiating proposal or fact MUST omit it so the adapter creates a new UUID. An acknowledgement MUST carry boolean `accepted`; every other kind omits it.
5. For a delegated mutation, use the source-owned handshake:
   - An `ownership-proposal` carries `mutationTarget` with exact `pane`, `worktree`, `branch`, `repository`, full `head`, and `status` values; pane, worktree, branch, and repository match the live recipient identity.
   - A `mutation-state` response carries the same target plus `observedState` with exact `worktree`, `branch`, `repository`, full `head`, and `status` values matching the live sender identity.
   - A `mutation-authorization` carries the checked target and observed state and targets that same live recipient. Any mismatch returns `invalid-identity` before delivery planning.
6. Pass the discovery and message request to the bundled script's `build` operation. It returns the complete `envelope` and a semantic `delivery` containing `toPane` and `text`.
7. Invoke `/operate-prowl` for one `send` operation using the delivery's complete pane, exact text, and immediate-return mode. NEVER construct environment command arguments outside that capability.
8. Pass the envelope and the exact environment result to the bundled script's `result` operation. Set `delivered` true only when `/operate-prowl` returned `status: "succeeded"` and `commandExitCode: 0`; preserve the complete environment result under `transport`.
9. Report the complete `coordinationReference`, checked `commandExitCode`, and delivery `status`. `delivered` means only that the environment capability accepted transport; it NEVER means acknowledged, agreed, authorized, or owned. Stop with the exact status and detail on `delivery-failed`, `invalid-identity`, `environment-unavailable`, or `invalid-schema`.

</workflow>

<command_forms>

Pass every payload over stdin. When the shell accepts multiline input:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" build <<'JSON'
{"discovery":{},"messageRequest":{}}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"discovery":{},"messageRequest":{}}' | python3 "${CLAUDE_SKILL_DIR}/scripts/agent_message.py" build
```

</command_forms>

<constraints>

- ALWAYS preserve complete source-supplied agent, pane, worktree, branch, repository, run, coordination-reference, mutation-target, observed-state, and transport identities.
- ALWAYS invoke `/operate-prowl` for public environment discovery and delivery.
- NEVER scan transcript files, use another terminal multiplexer, or ask the operator to relay a message as a fallback.
- NEVER select an endpoint by title, focus, position, inferred prose, or an undeclared environment.
- NEVER convert transport success into acknowledgement, agreement, ownership, mutation authorization, or continuation state.

</constraints>

<testing>

Before release, exercise `discover_callers`, `coordination_reference`, `build_envelope`, `send_request`, `delivery_request`, and `delivery_result` with complete public identities and controlled environment-result payloads. Exercise CLI dispatch for `discover`, `build`, and `result` with stdin payloads. The matrix covers unique and ambiguous callers, optional run-identity preservation and rejection, accepted and rejected acknowledgements, all message kinds, complete HEAD/status validation, exact mutation target/state matching, malformed identities and optional fields, non-unique pane selection, delivered and failed environment results, and transport results that never establish acknowledgement, agreement, authorization, or ownership.

</testing>

<success_criteria>

- Discovery passes only with `status: "prowl-pane"`, one complete caller, and complete public targets.
- Build passes only with one validated envelope and one semantic delivery bound to the target's complete pane UUID.
- Delivery passes only after `/operate-prowl` returns a checked successful result; every failure preserves its exact status, detail, and command exit code when present.
- Caller, recipient, mutation-target, and observed-state identities validate before delivery.
- Transport delivery remains distinct from acknowledgement, agreement, authorization, ownership, and continuation.

</success_criteria>
