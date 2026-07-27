# Repository Marketplace Installation Architecture

Repository marketplace installation uses a Python ports-and-adapters boundary: committed agent-harness declarations parse into an immutable installation plan, orchestration executes that plan through agent-specific adapters implementing shared Protocols, and the CLI entry point binds the real subprocess runner. The isolated installation harness provisions real agent binaries with a disposable home and mirrored checkout, while plugin lifecycle placement receives the invocation checkout explicitly and remains bounded to each plugin's owned agent namespace.

## Rationale

Separating deterministic declaration parsing and plan construction from external CLI execution makes the selected plugin set inspectable before any mutation and keeps agent-specific command contracts behind typed adapters. Real Claude Code and Codex invocations in disposable homes establish install behavior at the product boundary, while controlled runner implementations cover first-failure and interaction-order behavior that a successful real install cannot expose reliably. Explicit checkout and environment roots make the state-ownership boundary structural: no fallback resolves a maintainer's ambient agent home, cache, marketplace registration, or agent directory.

## Invariants

- Installation operations preserve their declaration-derived order.
- The first failed operation is terminal for one installation run.
- Every agent state path used by the isolated harness resolves beneath its disposable home.
- Every lifecycle placement destination resolves beneath the invocation checkout.

## Verification

### Testing

- ALWAYS: committed Claude Code and Codex declarations are validated at the file boundary and converted into frozen typed records before orchestration consumes them ([conformance])
- ALWAYS: command execution avoids shell interpretation and preserves stdout, stderr, and the exit code in a structured result ([compliance])
- ALWAYS: orchestration reports a failed operation with its agent, plugin when applicable, operation name, and structured command result, then executes no later operation ([compliance])
- ALWAYS: the isolated harness redirects `HOME`, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, and `CODEX_SQLITE_HOME` beneath its disposable home for every agent invocation ([compliance])
- ALWAYS: lifecycle placement invokes the selected plugin's shipped placement entry point with the invocation checkout and may create, replace, or prune only files carrying that plugin's owned prefix ([compliance])
- NEVER: declaration parsing or orchestration resolves an implicit ambient agent home, marketplace source, cache directory, or agent directory ([compliance])

### Audit

- ALWAYS: external agent and lifecycle commands execute through an injected Protocol using array arguments, an explicit working directory, and an explicit environment; the real subprocess implementation is bound only at the CLI composition edge ([audit])
- ALWAYS: the real-agent installation harness owns disposable-home creation, mirrored-checkout setup, environment redirection, dependency checks, and cleanup while exposing observations for linked tests to judge ([audit])
- NEVER: a harness, controlled runner, or recording collaborator accepts an expected result, calls an assertion API, or returns a verdict ([audit])
- NEVER: framework mocks or process-global monkeypatching replace an agent CLI, lifecycle command, declaration reader, or subprocess boundary ([audit])
