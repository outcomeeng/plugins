# Hook State Delegation

The spec-tree plugin ships exactly one runtime hook: a `SessionStart` hook that delegates to the `spx` CLI hook runner — `spx hook run <hook-name-kebab-case>`, here `spx hook run session-start` — through a hook-safety-compliant inline guard. The `spx` CLI, not a plugin-shipped script, performs the hook's effects: it writes the agent session identity and project directories into the harness-provided `$CLAUDE_ENV_FILE` and records the worktree-occupancy claim under the project's `.spx/`. The hook command embeds no `.spx/`, git, transcript, or session logic of its own; on the disabled-or-absent path the inline guard exits with a valid empty result and writes nothing — the Hook Safety Contract's degrade-to-no-op path. The hook exists because `SessionStart` is the only lifecycle point at which the harness supplies `$CLAUDE_ENV_FILE` and sources it into every later Bash tool call of the session; the `spx` CLI cannot reach that lifecycle on its own. Delegation hands the lifecycle to `spx hook run session-start`, so the CLI that owns the `.spx/` model performs the session-environment work rather than a plugin script reimplementing it.

## Rationale

A plugin-shipped hook script is the wrong place to reimplement `.spx/` state, git inspection, or session and worktree logic. It would run stdlib-only and portable, duplicating the multi-worktree `.spx/` model the `spx` CLI owns and tests against a harness the script cannot reach, and drifting from that model over time. Concentrating every `.spx/` operation in one owner — the `spx` CLI — keeps a single implementation of the on-disk model whether a skill invokes it or the `SessionStart` hook does. `spx` resolves on `PATH` and spec-tree is non-functional without it, so delegating to it from the hook introduces no failure mode the methodology does not already carry; the hook-safety inline guard degrades to a no-op when `spx` is absent, so a missing CLI never traps the session.

## Invariants

- The spec-tree plugin ships exactly one runtime hook, on `SessionStart`.
- The `SessionStart` hook delegates to `spx hook run session-start`; the `spx` CLI performs the `$CLAUDE_ENV_FILE` identity and project-dir writes and the worktree-occupancy claim. The hook embeds no `.spx/`, git, transcript, or session logic of its own.
- `.spx/` state logic is owned by the `spx` CLI — invoked by skills and by the `SessionStart` hook — and is never reimplemented in a plugin-shipped script.
- The `SessionStart` hook conforms to `spx/15-hook-safety.pdr.md`: a non-blocking event, an inline-guard command with a valid-empty-result floor, an explicit timeout, an environment kill switch, and `spx` resolved as a PATH-probed optional dependency.

## Verification

### Audit

- ALWAYS: the spec-tree plugin ships exactly one runtime hook — a `SessionStart` hook that delegates to `spx hook run session-start`, and which on the disabled-or-absent path exits with a valid empty result and writes nothing ([audit])
- ALWAYS: the `SessionStart` hook satisfies `spx/15-hook-safety.pdr.md` — non-blocking event, inline-guard command with a valid-empty-result floor, explicit timeout, environment kill switch, and `spx` resolved as a PATH-probed optional dependency ([audit])
- NEVER: a plugin-shipped hook script reimplements `.spx/` state, git inspection, transcript parsing, or session and worktree logic the `spx` CLI owns — the hook delegates to the CLI ([audit])
