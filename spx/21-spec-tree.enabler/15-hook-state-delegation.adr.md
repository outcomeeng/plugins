# Hook State Delegation

Spec-tree runtime hooks own no `.spx/` state. Every read, write, or mutation of the `.spx/` state store is performed by the `spx` CLI, which a hook reaches only by running it as a subprocess and to which a hook adds only the harness-facing output it shapes — stdout for context injection, model-visible `PreToolUse` context, or a `PreToolUse` allow-or-deny decision. A hook forwards input locators — the session id and the transcript path, and for the `PreToolUse` gate the tool name and the tool's path argument — to the CLI and reads or parses neither the conversation transcript nor any `.spx/` file itself; the CLI performs that I/O and returns the gate verdict the hook emits. The `PreToolUse` hook also refreshes worktree occupancy unless the session environment already records a successful SessionStart claim: it invokes `spx worktree status --format json` and, when the returned status is `stale` or `unclaimed`, `spx worktree claim --session-id <session-id>`; it parses only the CLI's JSON status field and never reads the worktree claim file directly. One filesystem path is written directly by a hook: the harness-provided `$CLAUDE_ENV_FILE`, written solely by the SessionStart hook to place session identity and successful worktree-claim status into the agent's environment, a channel the `spx` CLI cannot supply because a child process cannot export a variable into its parent session.

## Rationale

Concentrating `.spx/` access in the `spx` CLI keeps one owner of the on-disk model and one implementation of `.spx/` resolution, which holds across both a single working tree and a bare-repository worktree pool and is verified by the CLI against a multi-worktree harness no hook can reach. Hooks stay thin and portable — stdlib-only, carrying no `.spx/` path logic — and degrade to a silent no-op when the CLI is absent, so an absent or older CLI weakens continuity instead of corrupting state. The `$CLAUDE_ENV_FILE` write is the one exception because session identity must reach every later Bash tool call in the conversation, and the harness env file is the sole channel that delivers it; a hook writing `.spx/` directly is the failure this decision exists to prevent.

## Invariants

- For every hook and every `.spx/` path, the hook performs no direct read or write of that path; all access is mediated by an `spx` subprocess invocation.
- A hook forwards input locators — the session id and the transcript path, and for the `PreToolUse` gate the tool name and the tool's path argument — to the `spx` CLI and performs no read or parse of the transcript or any `.spx/` file; the CLI performs that I/O.
- The `PreToolUse` hook refreshes worktree occupancy only through the `spx` CLI when no session environment marker records a successful SessionStart claim: it reads `spx worktree status --format json`, claims only statuses the CLI reports as `stale` or `unclaimed`, and performs no direct worktree-claim file access.
- The `PreToolUse` gate hook holds no gate logic: boundary detection, marker scan, path-to-node mapping, and the verdict are the `spx` CLI's, and the hook emits the CLI's verdict as the allow-or-deny decision, degrading to allow when the CLI is absent.
- The only filesystem path any hook writes directly is `$CLAUDE_ENV_FILE`, and only the SessionStart hook writes it.

## Verification

### Testing

- ALWAYS: each hook reaches `.spx/` state only through an `spx` subprocess invocation and performs no direct `.spx/` filesystem read or write ([compliance])
- NEVER: a hook reads or parses the conversation transcript itself — it forwards the transcript path to the `spx` CLI, which performs the read ([compliance])
- ALWAYS: when the `spx` CLI is absent or exits non-zero, the invoking hook degrades to a silent no-op or a non-blocking model-visible context message and writes no `.spx/` state itself ([compliance])
- ALWAYS: the `PreToolUse` gate hook forwards the tool name and the tool's path argument with the transcript path to the `spx` CLI and emits the CLI's allow-or-deny verdict, reading no transcript or `.spx/` file itself and degrading to allowing the call when the CLI is absent or exits non-zero ([compliance])
- NEVER: a hook other than SessionStart writes any filesystem path directly ([compliance])

### Audit

- ALWAYS: the `spx` CLI is the single owner of `.spx/` resolution and state placement, so hook-produced state never diverges from the CLI's `.spx/` model ([audit])
- ALWAYS: the SessionStart hook's only direct filesystem write is `$CLAUDE_ENV_FILE`; any `.spx/` state tied to session start — the worktree-occupancy claim — is created through an `spx` CLI subprocess (`spx worktree claim`), never a direct hook write, and per-runtime session directories stay lazily created by `spx session pickup` ([audit])
- ALWAYS: the `PreToolUse` hook's worktree-occupancy repair is created through `spx worktree status --format json` followed by `spx worktree claim --session-id <session-id>` only when the session environment does not already record a successful SessionStart claim and the CLI reports the running worktree as `stale` or `unclaimed`; the hook emits model-visible context about the repair but never reads or writes the claim file directly ([audit])
- ALWAYS: the `PreToolUse` gate hook holds no gate logic — boundary detection, transcript marker scan, path-to-node mapping, and the allow-or-deny verdict are the `spx` CLI's, reached only as a subprocess ([audit])
- NEVER: extend the direct-write carve-out beyond the SessionStart hook's `$CLAUDE_ENV_FILE` write — a new hook state need is met by adding an `spx` CLI state-store command, never by writing files from the hook ([audit])
