# Herdr Environment Adapter

One Python 3.13+ standard-library adapter shipped inside `/operate-herdr` owns the complete public herdr command grammar for inventory, read, wait, prompt, start, relaunch, stop, key, worktree create, and worktree open, its response validation, its error-code projection, and its bound on every wait. It exposes typed importable operations and a versioned JSON CLI; other coding-agents skills invoke `/operate-herdr` as a capability and never construct herdr argument vectors or invoke herdr command help.

## Rationale

One capability keeps herdr command knowledge testable and portable while preserving the skill-directory boundary plugin packaging requires. Herdr reports lifecycle conditions as error codes on a public JSON envelope — a server that is not running, an agent that is not found, not ready, blocked, or stalled after a prompt, and a wait that timed out — so the adapter projects each code the operating workflows act on to a named status and preserves every other code verbatim, which lets a caller branch on the named status without parsing message text. Every wait carries an explicit timeout because herdr waits indefinitely without one and a plugin-local adapter owns no open-ended wait under `spx/12-shipped-scripting.adr.md`. Start, relaunch, stop, key, worktree create, and worktree open change what runs in a pane or which worktrees and panes exist, so they require mutation authorization in the request as the Prowl node's mutating operations do; prompt submits text to an agent already running and stays ungated as the Prowl node's send does. The adapter binds to one environment's command surface, so it stays plugin-local under `spx/12-shipped-scripting.adr.md`, whose extraction rule governs its generic logic.

Create-worktree wraps herdr's native `herdr worktree create`, which creates the Git worktree and its herdr workspace in one step, so a workflow that needs a fresh worktree for an agent session composes no raw Git command with a worktree open. Its result carries the created worktree's path, its workspace, and its root pane, and the root pane is the pane start takes. Creating or opening a worktree names its workspace, so the worktree's workspace is the one the request names rather than one herdr selects. Create-worktree records no worktree-occupancy claim: a claim binds the exact worktree root to the current native agent session, no agent session exists in the worktree when it is created, and the agent session start launches there claims it at its own start.

An agent session herdr hosts can carry evidence that lacks a field the adapter projects — a session started in a pane outside the adapter, for one. Rejecting the whole inventory over one such agent would blind every caller to every other agent, so the projection confines the gap to a named incomplete item for that agent. Read and prompt deliver text to a pane and judge no readiness, so they proceed for such an agent and carry the incomplete item in place of the complete projection. Herdr writes a read as terminal text, which names no agent session, so read follows its own command with one `herdr agent get` lookup for the same target, and that lookup supplies the session or the incomplete item its result carries. Start, relaunch, and wait judge readiness from the projected fields, so when the field readiness needs is missing they return the named incomplete result rather than a readiness verdict the evidence cannot support.

Herdr 0.9.1, the pinned source-tool version, offers no command that ends an agent session and keeps its pane, and `herdr pane close` removes the pane together with the session. Stop therefore submits the agent's own `/exit` command to the pane through `herdr agent prompt`: Claude Code and Codex, the agents start launches, each end their session on `/exit`, and the pane returns to its shell, open for a relaunch into the same pane. Stop still ends what runs in a pane, so it stays gated by mutation authorization although it travels the prompt vector.

## Invariants

- One source-owned operation registry covers inventory, read, wait, prompt, start, relaunch, stop, key, open-worktree, and create-worktree; relaunch shares start's request shape and argument vector and names the case of a pane whose earlier agent session ended.
- Read maps to its `herdr agent read` argument vector plus one `herdr agent get` agent-evidence lookup for the same target, so its result carries the agent session or the named incomplete item; every other operation maps to one herdr argument vector.
- Create-worktree maps a request carrying a workspace, with an optional branch, base, and path, to one `herdr worktree create` argument vector, and its result carries the created worktree's path, its workspace, and its root pane.
- Open-worktree maps a request carrying a workspace and a path to one `herdr worktree open` argument vector naming that workspace.
- A create-worktree or open-worktree request without a workspace is an invalid request before any herdr command runs.
- Create-worktree records no worktree-occupancy claim; the agent session start launches in the created worktree claims it.
- Every wait-bearing request — wait, prompt with wait, start, relaunch — carries an explicit millisecond timeout, and the default runner's subprocess bound exceeds it.
- Herdr agent evidence is projected to the complete source-preserved name, agent kind, pane, tab, workspace, working directory, readiness, and the server's own working, blocked, idle, done, and unknown states.
- An agent whose evidence lacks a projected field is projected to a named incomplete item carrying its pane, every projected field its evidence carries, and the names of the missing fields; the inventory never rejects on that agent and projects every other agent in full.
- The herdr error codes `server_not_running`, `agent_not_found`, `agent_not_ready`, `agent_blocked`, `agent_prompt_stalled`, and `timeout` map to named statuses; every other error preserves its code and message verbatim under the command-failed status.
- A read's public response is terminal text, carried verbatim under the result's output field; every other public response is herdr's JSON envelope, carried as the result's response object.
- A start, relaunch, wait, read, or prompt result carries the one hosted agent session it acted on, projected as an inventory item is: the complete projection, or the named incomplete item in its place when that agent's evidence lacks a projected field.
- A start, relaunch, or wait whose readiness judgment needs a field the agent's evidence lacks returns the named incomplete result rather than a readiness verdict.
- Stop submits the agent's own `/exit` command to the pane through `herdr agent prompt`, ending the agent session and leaving its pane open at its shell; stop never closes its pane.
- Every command execution is bounded, argument-vector based, fully reaped before return, and isolated from the adapter request stream.
- Captured usage and public-response fixtures identify `herdr` 0.9.1 as their source-tool version pin. A change to that pin, or a live probe that reports grammar or response drift, invalidates the affected fixtures and requires recapture before they serve as oracles.
- Start, relaunch, stop, key, open-worktree, and create-worktree cannot construct an argument vector unless the request carries explicit mutation authorization.
- The environment surface carries the launch prompt, prompts, and keystrokes only; no operation produces a pane-borne handback block.

## Verification

### Testing

- ALWAYS: each source-owned operation maps a valid versioned request to the exact herdr argument vector for that operation, and read additionally to exactly one `herdr agent get` agent-evidence lookup for the same target ([mapping])
- ALWAYS: public herdr responses map to versioned source-owned results, the named lifecycle statuses for the projected error codes, or verbatim command failures without value rewriting ([mapping])
- ALWAYS: a public agent inventory maps to complete source-preserved identities and states, with a named incomplete item for each agent whose evidence lacks a projected field and every other agent in full, or to the named unavailable or ambiguous result ([mapping])
- ALWAYS: requests for start, relaunch, stop, key, open-worktree, and create-worktree fail before command execution when mutation authorization is absent ([compliance])
- NEVER: a wait-bearing request is accepted without an explicit timeout, and the default runner never runs a command without a bound ([compliance])
- NEVER: a shipped coding-agents Python script outside `/operate-herdr` constructs a herdr argument vector or invokes herdr command help ([compliance])
- ALWAYS: a create-worktree or open-worktree request without a workspace fails as an invalid request before any herdr command runs ([mapping])
- ALWAYS: create-worktree returns the created worktree's path, its workspace, and its root pane ([mapping])
- NEVER: create-worktree records a worktree-occupancy claim ([compliance])
- NEVER: one agent's incomplete evidence rejects the inventory, or a read or prompt addressed to that agent's pane; the result carries the named incomplete item in place of the complete projection ([mapping])
- ALWAYS: start, relaunch, and wait return the named incomplete result, never a readiness verdict, when the agent's evidence lacks a field their readiness judgment needs ([mapping])
- ALWAYS: stop ends the agent session by submitting the agent's own `/exit` command through `herdr agent prompt` and leaves its pane open at its shell ([mapping])

### Audit

- NEVER: a shipped coding-agents skill outside `/operate-herdr` instructs a workflow to construct herdr commands, invoke herdr command help, or depend on an external environment-control skill ([audit])
- ALWAYS: the herdr subprocess boundary accepts a dependency-injected `CommandRunner` Protocol and the default runner uses null-device stdin, captured output, and a bounded timeout ([audit])
- ALWAYS: tests inject controlled runner implementations only under `/test` Stage 5 exception 1 (failure simulation) or exception 2 (interaction protocols) ([audit])
- ALWAYS: `/operate-herdr` owns all bundled-script access; composing skills invoke the capability through the skill surface rather than manufacturing a cross-skill filesystem path ([audit])
- NEVER: framework mocks or monkeypatching replace herdr behavior or the command-runner boundary ([audit])
- NEVER: the adapter owns another workflow's retry, checkpoint, persistence, result interpretation, or continuation decision ([audit])
