# Repository Marketplace Installation Architecture

Marketplace installation uses a Python ports-and-adapters boundary with persistent and isolated modes. Committed agent-harness declarations and selected state boundaries parse into immutable installation plans, orchestration executes those plans through agent-specific adapters implementing shared Protocols, and the CLI entry point binds the real subprocess runner. Persistent planning validates Claude Code's user/project scope boundary before mutation and derives Codex source state from the selected `CODEX_HOME` through the Codex CLI. Isolated planning redirects every agent state root beneath caller-selected disposable state and registers the invocation checkout. Checkout materialization — the skill-co-located checkout placement `spx/12-marketplace-state.adr.md` declares — receives the invocation checkout explicitly and remains bounded to each plugin's owned agent namespace.

## Rationale

Separating declaration parsing, preflight inspection, plan construction, and external CLI execution makes the selected plugin set and mutation boundary inspectable before the first write. Persistent mode uses each agent's supported ownership model: Claude Code project scope and Codex's selected home. Isolated mode establishes end-to-end behavior at the real CLI boundary without contaminating persistent state. Controlled runners used under `/test` Stage 5 Failure simulation expose first-failure behavior that a successful real install cannot produce reliably, while recording collaborators used under `/test` Stage 5 Interaction protocols expose command order and shape.

## Invariants

- Installation operations preserve their declaration-derived order.
- The first failed operation is terminal for one installation run.
- A persistent plan exists only after Claude Code user-scope collision detection and canonical project-source validation complete.
- Persistent Codex commands carry the selected `CODEX_HOME` explicitly and never consult repository `.codex/config.toml`.
- Every agent state path used by isolated mode resolves beneath its disposable home.
- Every checkout-materialization placement destination resolves beneath the invocation checkout.

## Verification

### Testing

- ALWAYS: committed Claude Code and Codex declarations plus selected installation mode are validated at the boundary and converted into frozen typed records before orchestration consumes them ([conformance])
- ALWAYS: command execution avoids shell interpretation and preserves stdout, stderr, and the exit code in a structured result ([compliance])
- ALWAYS: orchestration reports a failed operation with its agent, plugin when applicable, operation name, and structured command result, then executes no later operation ([compliance])
- ALWAYS: persistent planning rejects a user-scoped Claude Code `outcomeeng` registration before emitting a state-changing command and reports the colliding settings path ([compliance])
- ALWAYS: the isolated harness redirects `HOME`, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, and `CODEX_SQLITE_HOME` beneath its disposable home for every agent invocation ([compliance])
- ALWAYS: checkout materialization invokes the selected plugin's shipped placement entry point with the invocation checkout and may create, replace, or prune only files carrying that plugin's owned prefix ([compliance])
- NEVER: persistent planning infers Codex plugin state from repository `.codex/config.toml`; the selected `CODEX_HOME` and Codex CLI are its state boundary ([compliance])

### Audit

- ALWAYS: external agent and lifecycle commands execute through an injected Protocol using array arguments, an explicit working directory, and an explicit environment; the real subprocess implementation is bound only at the CLI composition edge ([audit])
- ALWAYS: the real-agent installation harness owns disposable-home creation, mirrored-checkout setup, environment redirection, dependency checks, and cleanup while exposing observations for linked tests to judge ([audit])
- ALWAYS: controlled runners are used only under `/test` Stage 5 Failure simulation to expose otherwise unreliable command failures, and recording collaborators are used only under `/test` Stage 5 Interaction protocols to expose command order and shape; both preserve the real Protocol boundary and leave every predicate to the linked test ([audit])
- NEVER: a real-agent harness, Failure simulation controlled runner, or Interaction protocols recording collaborator accepts an expected result, calls an assertion API, or returns a verdict ([audit])
- NEVER: framework mocks or process-global monkeypatching replace an agent CLI, lifecycle command, declaration reader, or subprocess boundary ([audit])
