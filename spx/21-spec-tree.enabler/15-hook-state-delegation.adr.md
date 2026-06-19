# Hook State Delegation

The spec-tree plugin ships exactly one runtime hook: a `SessionStart` hook whose only positive effect is writing the agent session identity into the harness-provided `$CLAUDE_ENV_FILE`. It reads or writes no `.spx/` state, inspects no git state, parses no transcript, and spawns no subprocess of its own — the `session-start.py` script the harness invokes runs no child process, shells out to no tool, and calls neither git nor the `spx` CLI. On the normal path — enabled, script present and succeeding — the `$CLAUDE_ENV_FILE` write is the hook's sole effect, and it is the one channel the `spx` CLI cannot supply, because a child process cannot export a variable into its parent session. When the kill switch disables the hook or the script fails, the inline guard exits with a valid empty result and writes nothing — the Hook Safety Contract's degrade-to-no-op path. Every `.spx/` operation is performed by the `spx` CLI, invoked explicitly by skills, never by a runtime hook. The hook satisfies the product-wide `spx/15-hook-safety.pdr.md`: a non-blocking `SessionStart` event, an inline-guard command whose reachable floor is a valid empty result, an explicit timeout, and an environment kill switch — so a drifted plugin root, an absent script, or a pinned-cache mismatch degrades it to a no-op rather than an error.

## Rationale

A runtime hook is the wrong place for `.spx/` state, git inspection, or methodology enforcement. A hook runs stdlib-only and portable, cannot reach the multi-worktree `.spx/` model the `spx` CLI owns and tests against a harness no hook can reach, and any behavior it shapes for the agent competes with the harness for priority. Concentrating every `.spx/` operation in the `spx` CLI — invoked explicitly by skills, not implicitly by hooks — keeps one owner of the on-disk model. The single surviving hook exists only because session identity must reach every later Bash tool call in the conversation, and the harness env file is the sole channel that delivers it; anything else a hook might do belongs in a skill or the `spx` CLI.

## Invariants

- The spec-tree plugin ships exactly one runtime hook, on `SessionStart`.
- On the normal path (enabled, script present and succeeding) the `SessionStart` hook's only effect is writing the agent session identity to `$CLAUDE_ENV_FILE`; when the kill switch disables it or the script fails, the hook exits with a valid empty result and no write occurs. The `session-start.py` script performs no `.spx/` or git I/O, parses no transcript, and spawns no subprocess of its own.
- The `SessionStart` hook conforms to `spx/15-hook-safety.pdr.md`: a non-blocking event, an inline-guard command with a valid-empty-result floor, an explicit timeout, and an environment kill switch.
- `.spx/` state is read and written only by the `spx` CLI, invoked by skills — never by a runtime hook.

## Verification

### Audit

- ALWAYS: the spec-tree plugin ships exactly one runtime hook — a `SessionStart` hook whose only positive effect is the `$CLAUDE_ENV_FILE` session-identity write, and which otherwise (kill switch set, or script absent or failing) exits with a valid empty result and writes nothing ([audit])
- ALWAYS: the `SessionStart` hook satisfies `spx/15-hook-safety.pdr.md` — non-blocking event, inline-guard command with a valid-empty-result floor, explicit timeout, and environment kill switch ([audit])
- NEVER: a runtime hook's script reads or writes `.spx/` state, inspects git, parses the transcript, or spawns a subprocess of its own — such behavior belongs in a skill or the `spx` CLI ([audit])
