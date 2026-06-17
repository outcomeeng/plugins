# Hook Behavior Delegation

A converted spec-tree hook event contributes exactly one artifact to the plugin: the runtime hook-wiring entry (`hooks.json` for Claude Code, the equivalent Codex registration) mapping that event to `spx hooks <event>`. The plugin ships no script for a converted event. Every behavior of a converted event — spec-tree detection, git base-staleness inspection, `.spx/` and transcript I/O, the `$CLAUDE_ENV_FILE` write, worktree-occupancy claim and refresh, directive assembly, and the load-gate verdict — is performed by the `spx hooks <event>` subcommand the runtime invokes directly. The SessionStart and PreToolUse events are converted; the PreCompact, PostCompact, and PostToolUse events converge to the same contract as their nodes are decomposed to isolate the hook behavior (`spx/21-spec-tree.enabler/13-agent-environment.enabler/PLAN.md`).

The integration contract between the runtime and `spx` is the process exit signal plus one JSON document on stdout, in the runtime's native hook-output schema, optionally carrying a `specTree` descriptor the runtime ignores. The runtime consumes its native envelope; this product's tests parse the document and read key values. No consumer scans stdout for a substring. `spx hooks <event>` detects the runtime from the environment — `$CLAUDE_SESSION_ID` for Claude Code, `$CODEX_THREAD_ID` for Codex — and emits that runtime's native envelope, writing `$CLAUDE_ENV_FILE` directly because, invoked as the hook command itself, it inherits that path from the hook environment.

`spx` is a precondition for spec-tree operation: an agent cannot claim a worktree, hand off a session, or run validation without it. A converted hook command therefore does not degrade to a no-op when `spx` is absent — an absent `spx` is a broken installation surfaced by the runtime's hook-execution error, never silently swallowed.

## Rationale

Concentrating a hook's whole behavior in the `spx` CLI gives one owner and one implementation, verified against the multi-worktree harness no hook script can reach. Splitting a hook between a script that assembles directives and shapes stdout and a CLI that owns `.spx/` state would carry two contracts to hold in sync and a string-coupled test surface — a test asserting hand-written marker literals against subprocess stdout. A single `spx`-owned behavior leaves the plugin one contribution per event, the wiring entry, and one cross-boundary coupling, a JSON schema.

A JSON-document contract is stable where stdout string assembly is brittle. A consumer that scans stdout for a substring couples to prose wording and fails when the wording changes; a consumer that parses a `specTree` descriptor and reads typed key values holds across rewording, which is what both the runtime and the tests do. `spx` emits the descriptor alongside the native envelope so the runtime renders the prose while tests assert structure.

A degrade-to-no-op path for an absent CLI protects nothing, because `spx` is required for the worktree, session, and validation flows; such a path only lets a broken installation run with methodology gating silently disabled, so an absent `spx` is better surfaced as a visible failure. `spx` owns the `$CLAUDE_ENV_FILE` write because, invoked as the hook command itself, it inherits that path from the hook environment and writes it like any other process; no separate carve-out is needed for a script to export session identity into its parent session.

Conversion is staged by node because `spx/EXCLUDE` is node-granular: a node whose entire test surface is the hook behavior excludes cleanly while its `spx hooks` dependency is unpublished, while a node that mixes the hook behavior with already-published behavior (the `76-sessions.enabler` handoff flow, the `65-applying.enabler` TDD flow) requires the hook behavior decomposed into its own excludable child node first. Converting such a node before that decomposition would drop the gate's coverage of its working behavior.

## Invariants

- A converted hook event's only plugin artifact is the wiring entry mapping it to `spx hooks <event>`; the plugin ships no script for that event.
- Every behavior of a converted hook event — detection, git inspection, `.spx/` and transcript I/O, the `$CLAUDE_ENV_FILE` write, worktree claim and refresh, directive assembly, and the gate verdict — is performed by `spx hooks <event>`, invoked directly by the runtime.
- The hook integration contract is the process exit signal plus one stdout JSON document in the runtime's native hook-output schema, optionally carrying a `specTree` descriptor; every consumer validates JSON and reads key values and never scans stdout for a substring.
- `spx hooks <event>` detects the runtime from `$CLAUDE_SESSION_ID` or `$CODEX_THREAD_ID` and emits that runtime's native envelope.
- An absent `spx` is a broken installation surfaced by the runtime's hook error; no converted hook command degrades to a no-op to mask it.

## Verification

### Audit

- ALWAYS: a converted hook event's plugin contribution is the wiring entry alone, mapping it to `spx hooks <event>`, with no script shipped for that event ([audit])
- ALWAYS: `spx hooks <event>` is the single owner of a converted event's behavior — detection, git inspection, `.spx/` and transcript I/O, the `$CLAUDE_ENV_FILE` write, worktree claim and refresh, directive assembly, and the gate verdict — so hook-produced state never diverges from the CLI's `.spx/` model ([audit])
- ALWAYS: the runtime–`spx` hook contract is the exit signal plus one stdout JSON document in the native hook-output schema, optionally extended with a `specTree` descriptor; no consumer parses stdout by substring scan ([audit])
- ALWAYS: `spx hooks <event>` detects the runtime from the environment and emits that runtime's native envelope, writing `$CLAUDE_ENV_FILE` directly when present ([audit])
- NEVER: a converted hook command degrades to a no-op when `spx` is absent — `spx` is a precondition for spec-tree operation, so its absence surfaces as a runtime hook error rather than silent continuation ([audit])
- NEVER: reintroduce a script for a converted hook event to assemble directives, shape stdout, or write state — a new hook need is met by extending `spx hooks <event>`, never by shipping a script beside the wiring entry ([audit])
