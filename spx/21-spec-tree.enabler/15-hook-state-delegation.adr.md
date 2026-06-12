# Hook State Delegation

Spec-tree runtime hooks own no `.spx/` state. Every read, write, or mutation of the `.spx/` state store is performed by the `spx` CLI, which a hook reaches only by running it as a subprocess and to which a hook adds only the harness-facing output it shapes — stdout for context injection. A hook forwards input locators — the session id and the transcript path — to the CLI and reads or parses neither the conversation transcript nor any `.spx/` file itself; the CLI performs that I/O. One filesystem path is written directly by a hook: the harness-provided `$CLAUDE_ENV_FILE`, written solely by the SessionStart hook to place session identity into the agent's environment, a channel the `spx` CLI cannot supply because a child process cannot export a variable into its parent session.

## Rationale

Concentrating `.spx/` access in the `spx` CLI keeps one owner of the on-disk model and one implementation of `.spx/` resolution, which holds across both a single working tree and a bare-repository worktree pool and is verified by the CLI against a multi-worktree harness no hook can reach. Hooks stay thin and portable — stdlib-only, carrying no `.spx/` path logic — and degrade to a silent no-op when the CLI is absent, so an absent or older CLI weakens continuity instead of corrupting state. The `$CLAUDE_ENV_FILE` write is the one exception because session identity must reach every later Bash tool call in the conversation, and the harness env file is the sole channel that delivers it; a hook writing `.spx/` directly is the failure this decision exists to prevent.

## Invariants

- For every hook and every `.spx/` path, the hook performs no direct read or write of that path; all access is mediated by an `spx` subprocess invocation.
- A hook forwards input locators — the session id and the transcript path — to the `spx` CLI and performs no read or parse of the transcript or any `.spx/` file; the CLI performs that I/O.
- The only filesystem path any hook writes directly is `$CLAUDE_ENV_FILE`, and only the SessionStart hook writes it.

## Verification

### Testing

- ALWAYS: each hook reaches `.spx/` state only through an `spx` subprocess invocation and performs no direct `.spx/` filesystem read or write ([compliance])
- NEVER: a hook reads or parses the conversation transcript itself — it forwards the transcript path to the `spx` CLI, which performs the read ([compliance])
- ALWAYS: the SessionStart hook's only direct filesystem write is `$CLAUDE_ENV_FILE`, and it creates no `.spx/` state — per-runtime session directories are created lazily by `spx session pickup` ([conformance])
- ALWAYS: when the `spx` CLI is absent or exits non-zero, the invoking hook degrades to a silent no-op and writes no `.spx/` state itself ([compliance])
- NEVER: a hook other than SessionStart writes any filesystem path directly ([compliance])

### Audit

- ALWAYS: the `spx` CLI is the single owner of `.spx/` resolution and state placement, so hook-produced state never diverges from the CLI's `.spx/` model ([audit])
- NEVER: extend the direct-write carve-out beyond the SessionStart hook's `$CLAUDE_ENV_FILE` write — a new hook state need is met by adding an `spx` CLI state-store command, never by writing files from the hook ([audit])
