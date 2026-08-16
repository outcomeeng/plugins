# Repository Marketplace Installation Architecture

Marketplace installation uses a Python ports-and-adapters boundary with persistent and isolated modes. Committed agent-harness declarations and read-only installed-plugin observations parse into immutable installation plans, orchestration executes those plans through agent-specific adapters implementing shared Protocols, and the CLI entry point binds the real subprocess runner. Persistent preflight inspects each selected agent state before mutation, validates a nonempty installed subset contains `spec-tree`, derives empty state as the `spec-tree` bootstrap selection with a warning, and orders selected names through that agent's committed catalog. Persistent source reconciliation begins only after every selection validates. Isolated planning redirects every agent state root beneath caller-selected disposable state, registers the invocation checkout, and accepts catalog-bounded selections for full-catalog and subset verification. Checkout materialization — the skill-co-located checkout placement `spx/12-marketplace-state.adr.md` declares — receives the invocation checkout explicitly and remains bounded to each plugin's owned agent namespace. Orchestration recognizes one non-terminal failure: a persistent-mode selected plugin install or enable whose agent CLI reports the plugin absent from the marketplace, which orchestration records as pending publication and passes over.

## Rationale

Separating declaration parsing, installed-state inspection, validation, plan construction, and external CLI execution makes the exact selected plugin set and mutation boundary inspectable before the first write. Persistent mode uses each agent's supported ownership model: Claude Code project scope and Codex's selected home. Catalog ordering gives stable command plans without turning catalog membership into automatic installation. Isolated mode establishes full and subset behavior at the real CLI boundary without contaminating persistent state. Controlled runners used under `/test` Stage 5 Failure simulation expose first-failure behavior that a successful real install cannot produce reliably, while recording collaborators used under `/test` Stage 5 Interaction protocols expose command order and shape.

## Invariants

- Installation operations preserve their declaration-derived order.
- Every persistent installed-plugin inspection completes and every selected subset validates before source reconciliation or plugin mutation begins.
- An empty persistent installed set maps to `spec-tree` plus one warning; every nonempty set maps to itself only when it contains `spec-tree`.
- Catalog ordering never adds an unselected plugin to a persistent plan.
- The first failed operation is terminal for one installation run, other than a persistent-mode plugin operation reporting the plugin absent from the marketplace, which the run records as pending publication and continues past.
- Only a persistent plan admits that pending-publication carve-out; an isolated plan registers the checkout as the marketplace, so the same absence there is terminal.
- A persistent plan exists only after Claude Code user-scope collision detection and canonical project-source validation complete.
- Persistent Codex commands carry the selected `CODEX_HOME` explicitly and never consult repository `.codex/config.toml`.
- Every agent state path used by isolated mode resolves beneath its disposable home.
- Every checkout-materialization placement destination resolves beneath the invocation checkout.

## Verification

### Testing

- ALWAYS: committed Claude Code and Codex declarations plus selected installation mode are validated at the boundary and converted into frozen typed records before orchestration consumes them ([conformance])
- ALWAYS: persistent preflight parses each agent's read-only plugin listing into a catalog-bounded installed subset before emitting any state-changing command ([conformance])
- ALWAYS: selection validation maps empty state to `spec-tree` plus a warning, accepts nonempty subsets containing `spec-tree`, and rejects nonempty subsets omitting `spec-tree` ([mapping])
- NEVER: persistent plan construction adds a catalog plugin absent from that agent's installed-plugin observation ([compliance])
- ALWAYS: command execution avoids shell interpretation and preserves stdout, stderr, and the exit code in a structured result ([compliance])
- ALWAYS: orchestration reports a failed operation with its agent, plugin when applicable, operation name, and structured command result, then executes no later operation ([compliance])
- ALWAYS: a persistent-mode plugin install or enable whose result reports the plugin absent from the marketplace is recorded as pending publication in the installation report, and every later operation still executes ([compliance])
- NEVER: the pending-publication carve-out applies to an isolated plan, to a non-plugin operation, or to a failure whose result does not report the plugin absent from the marketplace ([compliance])
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
