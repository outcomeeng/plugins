# Hook Safety Contract

Every hook any marketplace plugin ships, on every agent surface, observes or injects context on a non-blocking event only — it can never deny, block, or stall an agent's forward progress through its own failure — with the one exception stated below. A hook command is a self-contained inline guard whose reachable floor is a valid empty result, depends on no shipped script file resolving at a substituted path, treats any external command it uses as an optional dependency it probes before use, and carries an explicit short timeout and an environment kill switch. The guarantee binds at build time: every version the product builds — authored source rendered into both generated runtime trees — carries only hooks that satisfy this contract, so no version the product ships can trap a session.

One shipped hook is the exception to the non-blocking rule: the spec-tree plugin's pre-write check, a `PreToolUse` hook whose matcher names exactly the Write and Edit tools, which denies a call whose destination lies outside the session's granted roots. Every failure of that hook, a timeout included, allows the call, so the hook denies only a destination its own deterministic check resolves outside every granted root; it carries an explicit timeout of at most five seconds and an environment kill switch, like every shipped hook.

## Rationale

A hook the agent consults before an action can deny that action, so a hook on a blocking-capable event turns any hook failure into a wall the agent cannot pass — and the failure that matters happens beyond the hook script's reach. A command that invokes a script by its resolved path fails the instant that path drifts: a pinned plugin cache, a changed plugin root, or a missing scripts directory leaves the script absent, and on a blocking event that absence denies the action before any in-script fail-open can run. Only two properties together make a hook structurally unable to trap a session: it fires on a non-blocking event, where the agent treats any failure as advisory and continues; and its command carries its own inline floor, so the worst case it can produce is a valid empty result rather than an error. Methodology enforcement belongs in skills and the spx CLI — surfaces the agent invokes explicitly and the operator can decline — never in a hook the agent runs implicitly. An external CLI a hook consults is therefore optional: probed for existence and executability and resolved from the environment or PATH, never a version-pinned cache path, with every failure wrapped to the floor. No skill and no `spx` command sees a Write or Edit call before it runs, so rejecting a destination outside the session's granted roots is reachable only from a hook on a blocking-capable event. Allowing the call on every failure keeps the guarantee that a hook failure never traps a session: only the check's own verdict denies, and a denied call leaves the agent free to write inside its granted roots.

The contract binds each version at the moment it is built: a shipped version is immutable, so the product never reaches back to alter, collapse, or withdraw a version already distributed — the agent owns the lifecycle of the versions it has cached or pinned. Forward enforcement is sufficient, because the gate blocks any version that violates the contract from shipping at all, and a version that satisfies it cannot later become unsafe.

## Product properties

1. Every shipped hook except the pre-write check is observe-or-inject-only on a non-blocking event; the pre-write check denies only a Write or Edit call whose destination it resolves outside the session's granted roots; on no agent surface can a hook deny, block, defer, or stall an action through its own failure.
2. Every shipped hook command degrades to a valid empty result with no error under every dependency failure — a missing script, an absent or non-executable CLI, a drifted plugin root, a pinned-cache mismatch — and carries an explicit short timeout and an environment variable that disables it without editing configuration or leaving the session.
3. The guarantee binds at build time: authored source and both generated runtime trees ship only hooks that satisfy this contract. A shipped version is immutable — the product enforces the contract forward on every version it builds, never by altering or collapsing a version already distributed.

## Verification

- ALWAYS: the pre-write check allows the call, exiting zero with a valid empty result, on every failure: an absent, unreadable, or malformed payload, a missing script, an absent interpreter, an exception, and a timeout

### Testing

- NEVER: a shipped hook registers on a blocking-capable event — PreToolUse, UserPromptSubmit, UserPromptExpansion, PermissionRequest, PostToolBatch, Stop, SubagentStop, PreCompact, or any other event on which exit 2, a deny or block decision, or a timeout denies the agent's action — except the spec-tree plugin's pre-write check, a `PreToolUse` entry whose matcher names exactly the Write and Edit tools and whose command runs the write-boundary adapter inside the inline guard ([compliance])
- ALWAYS: every shipped hook entry declares an explicit timeout, never inheriting the agent's multi-minute default ([compliance])
- NEVER: a shipped hook command is a bare invocation of a script file at a substituted path with no inline fallback — the command's reachable floor is a successful exit emitting a well-formed empty result ([compliance])
- NEVER: a shipped hook command names a version-pinned plugin cache path for its script or its dependency ([compliance])
- ALWAYS: the hook-configuration rules hold identically across the generated Claude Code (`dist/claude`) and Codex (`dist/codex`) trees for every plugin ([compliance])

### Audit

- ALWAYS: a plugin ships a hook only when the hook's effect is otherwise unreachable by a skill or the spx CLI — exporting the agent session identity into the harness env file at session start, which a child process cannot do for its parent, is the canonical case, and rejecting a Write or Edit destination before the call runs is the one case on a blocking-capable event ([audit])
- ALWAYS: a hook command is a self-contained inline guard whose every branch and every dependency failure resolves to the valid-empty-result floor, so a missing script, an absent or non-executable CLI, or a drifted plugin root degrades to a no-op rather than an error ([audit])
- ALWAYS: a hook treats any external command it uses as an optional dependency — resolved by environment override then PATH, probed for existence and executability before invocation, never assumed present ([audit])
- ALWAYS: every shipped hook exposes an environment kill switch that disables it without editing configuration or leaving the session ([audit])
- NEVER: methodology enforcement, gate logic, `.spx/` or git inspection, transcript parsing, or subprocess-bearing work runs in a hook — that behavior lives in a skill or the spx CLI ([audit])
