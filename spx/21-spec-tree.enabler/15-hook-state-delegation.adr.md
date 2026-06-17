# Hook State Delegation

The spec-tree plugin ships exactly one runtime hook: a `SessionStart` hook that writes the agent session identity into the harness-provided `$CLAUDE_ENV_FILE` and does nothing else. It reads or writes no `.spx/` state, inspects no git state, parses no transcript, and runs no subprocess. The `$CLAUDE_ENV_FILE` write is the hook's sole effect — and the one channel the `spx` CLI cannot supply, because a child process cannot export a variable into its parent session. Every `.spx/` operation is performed by the `spx` CLI, invoked explicitly by skills, never by a runtime hook.

## Rationale

A runtime hook is the wrong place for `.spx/` state, git inspection, or methodology enforcement. A hook runs stdlib-only and portable, cannot reach the multi-worktree `.spx/` model the `spx` CLI owns and tests against a harness no hook can reach, and any behavior it shapes for the agent competes with the harness for priority. Concentrating every `.spx/` operation in the `spx` CLI — invoked explicitly by skills, not implicitly by hooks — keeps one owner of the on-disk model. The single surviving hook exists only because session identity must reach every later Bash tool call in the conversation, and the harness env file is the sole channel that delivers it; anything else a hook might do belongs in a skill or the `spx` CLI.

## Invariants

- The spec-tree plugin ships exactly one runtime hook, on `SessionStart`.
- The `SessionStart` hook's only effect is writing the agent session identity to `$CLAUDE_ENV_FILE`; it performs no `.spx/` or git I/O, parses no transcript, and runs no subprocess.
- `.spx/` state is read and written only by the `spx` CLI, invoked by skills — never by a runtime hook.

## Verification

### Audit

- ALWAYS: the spec-tree plugin ships exactly one runtime hook — a `SessionStart` hook whose only effect is the `$CLAUDE_ENV_FILE` session-identity write ([audit])
- NEVER: a runtime hook reads or writes `.spx/` state, inspects git, parses the transcript, or runs a subprocess — such behavior belongs in a skill or the `spx` CLI ([audit])
