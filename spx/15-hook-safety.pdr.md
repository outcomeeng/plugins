# Hook Safety Contract

Every hook any marketplace plugin ships, on every runtime surface, observes or injects context on a non-blocking event only — it can never deny, block, or stall an agent's forward progress. A hook command is a self-contained inline guard whose reachable floor is a valid empty result, depends on no shipped script file resolving at a substituted path, treats any external command it uses as an optional dependency it probes before use, and carries an explicit short timeout and an environment kill switch. The guarantee binds at build time: every version the product builds — authored source rendered into both generated runtime trees — carries only hooks that satisfy this contract, so no version the product ships can trap a session.

## Rationale

A hook the runtime consults before an action can deny that action, so a hook on a blocking-capable event turns any hook failure into a wall the agent cannot pass — and the failure that matters happens beyond the hook script's reach. A command that invokes a script by its resolved path fails the instant that path drifts: a pinned plugin cache, a changed plugin root, or a missing scripts directory leaves the script absent, and on a blocking event that absence denies the action before any in-script fail-open can run. Only two properties together make a hook structurally unable to trap a session: it fires on a non-blocking event, where the runtime treats any failure as advisory and continues; and its command carries its own inline floor, so the worst case it can produce is a valid empty result rather than an error. Methodology enforcement belongs in skills and the spx CLI — surfaces the agent invokes explicitly and the operator can decline — never in a hook the runtime runs implicitly. An external CLI a hook consults is therefore optional: probed for existence and executability and resolved from the environment or PATH, never a version-pinned cache path, with every failure wrapped to the floor. The contract binds each version at the moment it is built: a shipped version is immutable, so the product never reaches back to alter, collapse, or withdraw a version already distributed — the runtime owns the lifecycle of the versions it has cached or pinned. Forward enforcement is sufficient, because the gate blocks any version that violates the contract from shipping at all, and a version that satisfies it cannot later become unsafe.

## Product properties

1. Every shipped hook is observe-or-inject-only on a non-blocking event; on no runtime surface can a hook deny, block, defer, or stall an action.
2. Every shipped hook command degrades to a valid empty result with no error under every dependency failure — a missing script, an absent or non-executable CLI, a drifted plugin root, a pinned-cache mismatch — and carries an explicit short timeout and an environment variable that disables it without editing configuration or leaving the session.
3. The guarantee binds at build time: authored source and both generated runtime trees ship only hooks that satisfy this contract. A shipped version is immutable — the product enforces the contract forward on every version it builds, never by altering or collapsing a version already distributed.

## Verification

### Testing

- NEVER: a shipped hook registers on a blocking-capable event — PreToolUse, UserPromptSubmit, UserPromptExpansion, PermissionRequest, PostToolBatch, Stop, SubagentStop, PreCompact, or any other event on which exit 2, a deny or block decision, or a timeout denies the agent's action ([compliance])
- ALWAYS: every shipped hook entry declares an explicit timeout, never inheriting the runtime's multi-minute default ([compliance])
- NEVER: a shipped hook command is a bare invocation of a script file at a substituted path with no inline fallback — the command's reachable floor is a successful exit emitting a well-formed empty result ([compliance])
- NEVER: a shipped hook command names a version-pinned plugin cache path for its script or its dependency ([compliance])
- ALWAYS: the hook-configuration rules hold identically across the generated Claude Code (`dist/claude`) and Codex (`dist/codex`) trees for every plugin ([compliance])

### Audit

- ALWAYS: a plugin ships a hook only when the hook's effect is otherwise unreachable by a skill or the spx CLI — exporting the agent session identity into the harness env file at session start, which a child process cannot do for its parent, is the canonical case ([audit])
- ALWAYS: a hook command is a self-contained inline guard whose every branch and every dependency failure resolves to the valid-empty-result floor, so a missing script, an absent or non-executable CLI, or a drifted plugin root degrades to a no-op rather than an error ([audit])
- ALWAYS: a hook treats any external command it uses as an optional dependency — resolved by environment override then PATH, probed for existence and executability before invocation, never assumed present ([audit])
- ALWAYS: every shipped hook exposes an environment kill switch that disables it without editing configuration or leaving the session ([audit])
- NEVER: methodology enforcement, gate logic, `.spx/` or git inspection, transcript parsing, or subprocess-bearing work runs in a hook — that behavior lives in a skill or the spx CLI ([audit])
