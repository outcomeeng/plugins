# Hook State Delegation

The product-tree plugin ships exactly one runtime hook event, `SessionStart`, with two entries.

The delegating entry runs on every source. It delegates to the `spx` CLI hook runner — `spx hook run <hook-name-kebab-case>`, here `spx hook run session-start` — through a hook-safety-compliant inline guard. The `spx` CLI, not a plugin-shipped script, performs the entry's effects: it writes the agent session identity and project directories into the harness-provided `$CLAUDE_ENV_FILE` and records the worktree-occupancy claim under the project's `.spx/`. On the disabled-or-absent path the inline guard exits with a valid empty result and writes nothing — the Hook Safety Contract's degrade-to-no-op path.

The compact entry runs on the `SessionStart` source `compact`, selected by the matcher `compact`. It is an inline command that prints the post-compaction reminder resource named by the `compact_recovery` entry of the foundation-resource manifest governed by [`spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/15-foundation-manifest.adr.md), found under the plugin root the harness substitutes, through the shell's own read of that file. It runs no script, no `spx` CLI, and no external command. When the resource is unreadable or the kill switch is set, it exits with a valid empty result and prints nothing. The text of the reminder is governed by [`spx/21-product-tree.enabler/16-compact-continuity.pdr.md`](spx/21-product-tree.enabler/16-compact-continuity.pdr.md); the entry carries a path and no prose.

Neither entry embeds `.spx/`, git, transcript, or session logic of its own. `.spx/` state logic stays with the `spx` CLI.

Each entry exists because its effect is reachable at no other lifecycle point. `SessionStart` is the only point at which the harness supplies `$CLAUDE_ENV_FILE` and sources it into every later Bash tool call of the session; the `spx` CLI cannot reach that lifecycle on its own. `SessionStart` with the source `compact` is the only point that follows a compaction, where no skill is live to state what the resumed session must do first.

## Rationale

A plugin-shipped hook script is the wrong place to reimplement `.spx/` state, git inspection, or session and worktree logic. It would run stdlib-only and portable, duplicating the multi-worktree `.spx/` model the `spx` CLI owns and tests against a harness the script cannot reach, and drifting from that model over time. Concentrating every `.spx/` operation in one owner — the `spx` CLI — keeps a single implementation of the on-disk model whether a skill invokes it or the delegating entry does. `spx` resolves on `PATH` and product-tree is non-functional without it, so delegating to it from the hook introduces no failure mode the methodology does not already carry; the hook-safety inline guard degrades to a no-op when `spx` is absent, so a missing CLI never traps the session.

The compact entry carries no `.spx/` state, so it needs no CLI. Its work is to place one static text in the resumed session's context, and the shell's own read of a shipped file does that with no process beyond the shell, which leaves the entry no dependency whose absence could fail it. The reminder lives in a resource the manifest names, not in the command, because the manifest is the package's resource surface the `spx` CLI consumes, package checks keep the named file shipped in every generated tree, and the command then carries a path in place of prose that would need quoting inside a configuration string. A single kill switch, `PRODUCT_TREE_SESSION_HOOK_DISABLED`, disables both entries, because one switch per plugin disables its hook without editing configuration or leaving the session.

Two entries on one event do not widen the hook's reach. The delegating entry is unchanged, and the compact entry's effect is reachable by no skill and no CLI, which is the condition [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md) sets for shipping a hook. A reminder that states facts and instructs no step keeps the hook on the observe-or-inject side of that contract.

## Invariants

- The product-tree plugin ships exactly one runtime hook event, `SessionStart`, with two entries: the delegating entry on every source and the compact entry matched on `compact`.
- The delegating entry delegates to `spx hook run session-start`; the `spx` CLI performs the `$CLAUDE_ENV_FILE` identity and project-dir writes and the worktree-occupancy claim.
- The compact entry prints the resource the manifest's `compact_recovery` entry names, through the shell's own read, and prints nothing else; it runs no script, no `spx` CLI, and no external command.
- Neither entry embeds `.spx/`, git, transcript, or session logic of its own.
- `.spx/` state logic is owned by the `spx` CLI — invoked by skills and by the delegating entry — and is never reimplemented in a plugin-shipped script or an inline entry.
- Both entries conform to [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md): a non-blocking event, an inline-guard command with a valid-empty-result floor, an explicit timeout, the environment kill switch `PRODUCT_TREE_SESSION_HOOK_DISABLED`, and `spx` resolved as a PATH-probed optional dependency where an entry uses it.
- The `SessionStart` hook is limited to session-environment, worktree-occupancy, and post-compaction reminder behavior and carries no compact-summary behavior, per [`spx/21-product-tree.enabler/16-compact-continuity.pdr.md`](spx/21-product-tree.enabler/16-compact-continuity.pdr.md).

## Verification

- ALWAYS: the compact entry declares an explicit timeout of its own, and the kill switch `PRODUCT_TREE_SESSION_HOOK_DISABLED` disables the compact entry as it disables the delegating entry
- NEVER: the compact entry runs a script, the `spx` CLI, or an external command, embeds `.spx/`, git, transcript, or session logic, or prints anything other than the reminder resource the manifest names

### Audit

- ALWAYS: the product-tree plugin ships exactly one runtime hook event — `SessionStart` — with two entries: a delegating entry on every source that delegates to `spx hook run session-start` and on the disabled-or-absent path exits with a valid empty result and writes nothing, and a compact entry matched on `compact` that prints the reminder resource the foundation-resource manifest names and on the unreadable-or-disabled path exits with a valid empty result and prints nothing ([audit])
- ALWAYS: each `SessionStart` entry satisfies [`spx/15-hook-safety.pdr.md`](spx/15-hook-safety.pdr.md) — non-blocking event, inline-guard command with a valid-empty-result floor, explicit timeout, environment kill switch, and `spx` resolved as a PATH-probed optional dependency where the entry uses it ([audit])
- ALWAYS: each entry's existence is justified by an effect reachable at no other lifecycle point — the delegating entry by `$CLAUDE_ENV_FILE`, which only `SessionStart` supplies and sources into every later Bash tool call, and the compact entry by the point that follows a compaction, where no skill is live ([audit])
- NEVER: a plugin-shipped hook script reimplements `.spx/` state, git inspection, transcript parsing, or session and worktree logic the `spx` CLI owns — the delegating entry delegates to the CLI, and the compact entry holds no such logic ([audit])
