# Hook State Delegation

The spec-tree plugin ships exactly two runtime hooks: a `SessionStart` hook that delegates to the `spx` CLI hook runner, `spx hook run session-start`, and a `PreToolUse` pre-write check whose matcher names exactly the Write and Edit tools and whose command runs the plugin-local write-boundary adapter, `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/write_boundary.py`, each through a hook-safety-compliant inline guard. The `spx` CLI, not a plugin-shipped script, performs the hook's effects: it writes the agent session identity and project directories into the harness-provided `$CLAUDE_ENV_FILE` and records the worktree-occupancy claim under the project's `.spx/`. The hook command embeds no `.spx/`, git, transcript, or session logic of its own; on the disabled-or-absent path the inline guard exits with a valid empty result and writes nothing — the Hook Safety Contract's degrade-to-no-op path. The hook exists because `SessionStart` is the only lifecycle point at which the harness supplies `$CLAUDE_ENV_FILE` and sources it into every later Bash tool call of the session; the `spx` CLI cannot reach that lifecycle on its own. Delegation hands the lifecycle to `spx hook run session-start`, so the CLI that owns the `.spx/` model performs the session-environment work rather than a plugin script reimplementing it.

The write-boundary adapter reads only the harness's hook payload, the harness's environment, and the Claude Code settings files that apply to the project directory; it runs no subprocess and embeds no `.spx/`, git, transcript, or session logic.

## Rationale

A plugin-shipped hook script is the wrong place to reimplement `.spx/` state, git inspection, or session and worktree logic. It would run stdlib-only and portable, duplicating the multi-worktree `.spx/` model the `spx` CLI owns and tests against a harness the script cannot reach, and drifting from that model over time. Concentrating every `.spx/` operation in one owner — the `spx` CLI — keeps a single implementation of the on-disk model whether a skill invokes it or the `SessionStart` hook does. `spx` resolves on `PATH` and spec-tree is non-functional without it, so delegating to it from the hook introduces no failure mode the methodology does not already carry; the hook-safety inline guard degrades to a no-op when `spx` is absent, so a missing CLI never traps the session.

The write-boundary adapter stays in the plugin under [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md), because its whole input is one agent's hook payload, environment, and settings, so moving it into SPX would couple SPX to Claude Code; it is deterministic, bounded, standard-library-only, and independently tested. Codex bounds every write of a workspace-write session through its sandbox's writable roots, so no adapter bounds a Codex write: the build renders the adapter into the Codex tree, where it finds no `CLAUDE_PROJECT_DIR` and allows every call.

## Invariants

- The spec-tree plugin ships exactly two runtime hooks, one on `SessionStart` and one on `PreToolUse`.
- The `SessionStart` hook delegates to `spx hook run session-start`; the `spx` CLI performs the `$CLAUDE_ENV_FILE` identity and project-dir writes and the worktree-occupancy claim. The hook embeds no `.spx/`, git, transcript, or session logic of its own.
- The `PreToolUse` hook runs the plugin-local write-boundary adapter, which reads only the hook payload, the harness environment, and the Claude Code settings files, runs no subprocess, and reimplements no `.spx/`, git, transcript, or session logic.
- `.spx/` state logic is owned by the `spx` CLI — invoked by skills and by the `SessionStart` hook — and is never reimplemented in a plugin-shipped script.
- The `SessionStart` hook conforms to [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md): a non-blocking event, an inline-guard command with a valid-empty-result floor, an explicit timeout, an environment kill switch, and `spx` resolved as a PATH-probed optional dependency.

## Verification

### Audit

- ALWAYS: the spec-tree plugin ships exactly two runtime hooks — a `SessionStart` hook that delegates to `spx hook run session-start`, and which on the disabled-or-absent path exits with a valid empty result and writes nothing, and a `PreToolUse` pre-write check whose matcher names exactly the Write and Edit tools and whose command runs the write-boundary adapter inside the inline guard ([audit])
- ALWAYS: the `SessionStart` hook satisfies [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md) — non-blocking event, inline-guard command with a valid-empty-result floor, explicit timeout, environment kill switch, and `spx` resolved as a PATH-probed optional dependency ([audit])
- NEVER: a plugin-shipped hook script reimplements `.spx/` state, git inspection, transcript parsing, or session and worktree logic the `spx` CLI owns — the hook delegates to the CLI ([audit])
- NEVER: the write-boundary adapter runs a subprocess or reads anything beyond the hook payload, the harness environment, and the Claude Code settings files that apply to the project directory ([audit])
