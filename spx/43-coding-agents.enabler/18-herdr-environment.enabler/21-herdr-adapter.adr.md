# Herdr Environment Adapter

One Python 3.13+ standard-library adapter shipped inside `/operate-herdr` owns the complete public herdr command grammar for inventory, read, wait, prompt, start, relaunch, stop, key, and worktree open, its response validation, its error-code projection, and its bound on every wait. It exposes typed importable operations and a versioned JSON CLI; other coding-agents skills invoke `/operate-herdr` as a capability and never construct herdr argument vectors or invoke herdr command help.

## Rationale

One capability keeps herdr command knowledge testable and portable while preserving the skill-directory boundary plugin packaging requires. Herdr reports lifecycle conditions as error codes on a public JSON envelope — a server that is not running, an agent that is not found, not ready, blocked, or stalled after a prompt, and a wait that timed out — so the adapter projects each code the operating workflows act on to a named status and preserves every other code verbatim, which lets a caller branch on the named status without parsing message text. Every wait carries an explicit timeout because herdr waits indefinitely without one and a plugin-local adapter owns no open-ended wait under `spx/12-shipped-scripting.adr.md`. Start, relaunch, stop, key, and worktree open change what runs in a pane, so they require mutation authorization in the request as the Prowl node's mutating operations do; prompt submits text to an agent already running and stays ungated as the Prowl node's send does. The adapter binds to one environment's command surface, so it stays plugin-local under `spx/12-shipped-scripting.adr.md`, whose extraction rule governs its generic logic.

## Invariants

- One source-owned operation registry covers inventory, read, wait, prompt, start, relaunch, stop, key, and open-worktree; relaunch shares start's request shape and argument vector and names the case of a pane whose earlier agent session ended.
- Every wait-bearing request — wait, prompt with wait, start, relaunch — carries an explicit millisecond timeout, and the default runner's subprocess bound exceeds it.
- Herdr agent evidence is projected to the complete source-preserved name, agent kind, pane, tab, workspace, working directory, readiness, and the server's own working, blocked, idle, done, and unknown states.
- The herdr error codes `server_not_running`, `agent_not_found`, `agent_not_ready`, `agent_blocked`, `agent_prompt_stalled`, and `timeout` map to named statuses; every other error preserves its code and message verbatim under the command-failed status.
- A read's public response is terminal text, carried verbatim under the result's output field; every other public response is herdr's JSON envelope, carried as the result's response object.
- A start, relaunch, wait, or prompt result carries the one hosted agent session it acted on, projected onto the same complete source-preserved fields as an inventory item.
- Every command execution is bounded, argument-vector based, fully reaped before return, and isolated from the adapter request stream.
- Captured usage and public-response fixtures identify `herdr` 0.9.1 as their source-tool version pin. A change to that pin, or a live probe that reports grammar or response drift, invalidates the affected fixtures and requires recapture before they serve as oracles.
- Start, relaunch, stop, key, and open-worktree cannot construct an argument vector unless the request carries explicit mutation authorization.
- The environment surface carries the launch prompt, prompts, and keystrokes only; no operation produces a pane-borne handback block.

## Verification

### Testing

- ALWAYS: each source-owned operation maps a valid versioned request to the exact herdr argument vector for that operation ([mapping])
- ALWAYS: public herdr responses map to versioned source-owned results, the named lifecycle statuses for the projected error codes, or verbatim command failures without value rewriting ([mapping])
- ALWAYS: a public agent inventory maps to complete source-preserved identities and states or to the named unavailable or ambiguous result ([mapping])
- ALWAYS: requests for start, relaunch, stop, key, and open-worktree fail before command execution when mutation authorization is absent ([compliance])
- NEVER: a wait-bearing request is accepted without an explicit timeout, and the default runner never runs a command without a bound ([compliance])
- NEVER: a shipped coding-agents Python script outside `/operate-herdr` constructs a herdr argument vector or invokes herdr command help ([compliance])

### Audit

- NEVER: a shipped coding-agents skill outside `/operate-herdr` instructs a workflow to construct herdr commands, invoke herdr command help, or depend on an external environment-control skill ([audit])
- ALWAYS: the herdr subprocess boundary accepts a dependency-injected `CommandRunner` Protocol and the default runner uses null-device stdin, captured output, and a bounded timeout ([audit])
- ALWAYS: tests inject controlled runner implementations only under `/test` Stage 5 exception 1 (failure simulation) or exception 2 (interaction protocols) ([audit])
- ALWAYS: `/operate-herdr` owns all bundled-script access; composing skills invoke the capability through the skill surface rather than manufacturing a cross-skill filesystem path ([audit])
- NEVER: framework mocks or monkeypatching replace herdr behavior or the command-runner boundary ([audit])
- NEVER: the adapter owns another workflow's retry, checkpoint, persistence, result interpretation, or continuation decision ([audit])
