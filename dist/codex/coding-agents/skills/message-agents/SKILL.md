---
name: message-agents
description: >-
  ALWAYS invoke this skill when discovering a Prowl coding-agent recipient or sending facts, ownership proposals, or acknowledgements to another agent pane.
allowed-tools: Bash(printf:*), Bash(python3 "${SKILL_DIR}/scripts/agent_message.py":*)
---

<objective>
A caller-discovery result and a source-owned coordination-envelope delivery result for complete Prowl pane UUIDs, with transport status kept distinct from acknowledgement, agreement, and ownership.
</objective>

<workflow>

1. Discover the caller and recipients:

   `python3 "${SKILL_DIR}/scripts/agent_message.py" discover`

2. Require `status: "prowl-pane"`, one complete caller identity, and one target selected by its complete `pane` UUID. Stop with the exact status and detail on `unsupported-terminal`, `caller-ambiguous`, `prowl-unavailable`, `delivery-failed`, or `invalid-schema`; NEVER select by title, focus, position, or prose.
3. Build a request with `toPane`, `kind`, `subject`, `facts`, optional `request`, optional `coordinationReference`, optional `mutationTarget`, and optional `observedState`. `kind` is `ownership-proposal`, `fact`, `acknowledgement`, `mutation-state`, or `mutation-authorization`. An acknowledgement, mutation-state report, or mutation authorization MUST reuse the active proposal UUID; an initiating proposal or fact MUST omit it so the adapter creates a new UUID.
4. For a delegated mutation, use the source-owned handshake:
   - An `ownership-proposal` carries `mutationTarget` with exact `pane`, `worktree`, `branch`, `repository`, full `head`, and `status` values; its pane/worktree/branch/repository values match the live recipient identity.
   - A `mutation-state` response carries the same target plus `observedState` with exact `worktree`, `branch`, `repository`, full `head`, and `status` values matching the live sender identity.
   - A `mutation-authorization` carries the checked target and observed state and targets that same live recipient. Any mismatch returns `invalid-identity` before transport.
5. Deliver the JSON over stdin using the form the active shell accepts.

When the shell accepts multiline input:

```bash
python3 "${SKILL_DIR}/scripts/agent_message.py" send <<'JSON'
{"toPane":"<complete-pane-uuid>","kind":"fact","subject":"<subject>","facts":["<authoritative fact>"],"request":null}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"toPane":"<complete-pane-uuid>","kind":"fact","subject":"<subject>","facts":["<authoritative fact>"],"request":null}' | python3 "${SKILL_DIR}/scripts/agent_message.py" send
```

6. Report the complete `coordinationReference`, checked `commandExitCode`, and delivery `status`. `delivered` means only that Prowl accepted the transport command; it NEVER means acknowledged, agreed, or authorized. Stop with the exact status and detail on `delivery-failed`, `invalid-identity`, `prowl-unavailable`, or `invalid-schema`.

</workflow>

<testing>

Before release, call the importable `discover_callers(roster, environment)`, `coordination_reference(kind, active_reference)`, `build_envelope(...)`, `send_request(request, discovery, runner)`, and `send_envelope(envelope, runner)` entrypoints with injected recording runners, then exercise CLI dispatch through `main(["discover"])` and `main(["send"])` with send payloads supplied on stdin.

The release matrix covers:

- one exact caller match -> `prowl-pane` with one complete caller;
- missing caller evidence -> `unsupported-terminal`, and multiple matches -> `caller-ambiguous`, with no send from either state;
- `ownership-proposal` and `fact` -> new coordination UUIDs, while `acknowledgement`, `mutation-state`, and `mutation-authorization` -> the complete active proposal UUID;
- mutation proposals, state reports, and authorizations -> exact live-identity matching for target worktree, branch, repository, and pane, with mismatches rejected before transport;
- a complete fact request on stdin -> one `prowl send --pane <uuid> --no-wait --json` argument vector with the rendered envelope on subprocess stdin;
- malformed stdin JSON, unknown `kind`, non-string optional fields, missing identity fields, and title/focus/position/prose/channel selectors -> `invalid-schema` or `invalid-identity` before transport;
- nonzero Prowl exit, or a zero-exit public payload whose `ok` field is not `true` -> `delivery-failed` with the checked `commandExitCode` rather than `delivered`;
- malformed zero-exit Prowl JSON -> `invalid-schema` with `commandExitCode: 0`;
- zero-exit Prowl response with `ok: true` -> `delivered` with `commandExitCode: 0`, `acknowledged: false`, `agreed: false`, and `ownershipEstablished: false`.

</testing>

<failure_modes>

<failure name="caller identity read from the wrong public fields">

**What happened:** Claude read branch and repository values from similarly named but non-authoritative Prowl fields, so a live pane could not produce the complete identity the send contract requires.

**Why it failed:** Prowl supplies branch at `project.branch` and repository root at `worktree.root_path`; guessing parallel field locations broke correlation.

**How to avoid:** Consume identities only through `identity_from_agent()` and stop with the exact discovery status when any required public field is absent or ambiguous.

</failure>

<failure name="transport acceptance treated as recipient agreement">

**What happened:** Claude risked advancing ownership after a successful send even though Prowl had established only that it accepted the transport command.

**Why it failed:** Delivery, acknowledgement, agreement, and ownership are independent states; collapsing them lets one workflow claim another workflow's decision.

**How to avoid:** Treat `delivered` plus `commandExitCode: 0` as transport evidence only and require a separate acknowledgement carrying the complete active coordination reference.

</failure>

<failure name="malformed targeting reached transport">

**What happened:** Claude could silently ignore unknown message kinds, non-string optional fields, and selector-shaped fields before the request contract was hardened.

**Why it failed:** Ignored fields made an invalid request appear deliverable and obscured which exact pane identity selected the recipient.

**How to avoid:** Validate the complete request and both identities before `delivery_command()` runs; reject every unsupported field, malformed identity, and non-unique pane UUID with `invalid-schema` or `invalid-identity`.

</failure>

</failure_modes>

<constraints>

- ALWAYS preserve complete source-supplied agent, pane, worktree, branch, repository, run, coordination-reference, mutation-target, and observed-state identities.
- NEVER scan transcript files, use another terminal multiplexer, or ask the operator to relay a message as a fallback.
- NEVER convert transport success into ownership, mutation authorization, or continuation state.

</constraints>

<success_criteria>

- `discover` passes only with `status: "prowl-pane"`, one complete `caller`, and the complete public `targets`; `unsupported-terminal`, `caller-ambiguous`, `prowl-unavailable`, `delivery-failed`, or `invalid-schema` fails discovery with the exact `detail`.
- `send` passes only with `status: "delivered"`, `commandExitCode: 0`, the complete `coordinationReference`, `acknowledged: false`, `agreed: false`, and `ownershipEstablished: false`.
- `delivery-failed`, `invalid-identity`, `prowl-unavailable`, or `invalid-schema` fails send with the exact `status`, `detail`, and checked `commandExitCode` when Prowl ran.
- Caller, recipient, mutation-target, and observed-state identities validate before the source-owned `delivery_command()` argument vector runs.
- The rendered envelope reaches `prowl send` through subprocess stdin, and transport delivery remains distinct from acknowledgement, agreement, and ownership.

</success_criteria>
