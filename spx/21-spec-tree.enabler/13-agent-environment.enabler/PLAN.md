# PLAN: Conditional SessionStart context injection

## Intent

Improve how agents start a session. The `SessionStart` hook (`src/plugins/spec-tree/scripts/session-start.py`) injects, via stdout, the guidance an agent needs at the start of a spec-tree session — mirroring the register of the already-shipped `PostCompact` re-anchor directive (`spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md`): the hook stdout may be imperative and name skills; only summary text must stay non-imperative.

Three behaviors were scoped. One is shipped; two remain.

## Shipped

1. **Base-staleness directive** (merged, PR #201). When the worktree's HEAD trails the git-resolved default (`origin/HEAD`), the hook emits a `<SPEC-TREE_SESSION_START …/>` directive naming the behind-count and instructing fetch-and-rebase, never reset. Read-only (no fetch, no mutation); silent when current, non-git, or the default is unresolvable. Specified by `agent-environment.md`.

## Remaining

2. **`/understanding` directive.** In a spec-tree repo, inject a directive to invoke `/spec-tree:understanding` (and `/spec-tree:contextualizing <node>` once the target is known), reversing the hook's historical no-stdout stance. Plugin-only — no CLI dependency. Sanctioned by `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md` ("stdout for context injection"). Relates to `spx/21-spec-tree.enabler/18-context-loading.enabler` and the `/understanding` governance in `spx/21-spec-tree.enabler/spec-tree.md`; the hook home is this node.

3. **Queued-work discoverability.** Surface claimable `/pickup` sessions at start so handoff work is not invisible to a fresh agent. Surface `id + goal + next_step` (the `next_step` field already carries the re-anchor directive); **surface-only, never auto-pickup** — a fresh session may be deliberately unrelated. Relates to `spx/21-spec-tree.enabler/76-sessions.enabler`.

   **Dependency (cross-repo):** requires the `spx` CLI to gain machine-readable session output — `spx session list --format json` exposing at least `id, priority, goal, next_step, git_ref`. Today `spx session list` is human-readable text only and omits `git_ref` (verified 2026-06-14). Parsing the text in the hook couples the plugin to a display format (a `changes-reviewer`-class finding). Do the CLI change in `~/Code/outcomeeng/spx/` first, then consume the JSON.

## Design decisions (cannot be re-derived from the tree)

- **Conditional trigger = one `spx` CLI call.** Gate all injection on a single `spx` invocation that degrades to a silent no-op on `OSError` / non-zero / empty — this covers non-spec-tree repos and an absent CLI for free, matching the `post-compact.py` precedent. No filesystem probe. (`spx/` the durable tree is distinct from `.spx/` state; `15-hook-state-delegation.adr.md` restricts only `.spx/`.)
- **A session is worktree-independent.** The handoff queue is pool-global; `/pickup` happens in whatever worktree the agent occupies. Do not scope the discoverability queue to the current worktree's branch; `git_ref` identifies which branch/PR a session involves, not a filter.
- **Honesty caveat for discoverability:** a queued session whose branch is unpushed can point at unrecoverable work (`spx/21-spec-tree.enabler/76-sessions.enabler/ISSUES.md`); wording must not over-promise.

## Open consideration

`agent-environment.md` now carries ~13 assertions across two concerns (identity + base-currency), past the `/decomposing` >7 trigger. Consider splitting into identity + base-currency child enablers before adding behavior 2 here, or relocating behaviors 2–3 to their related nodes. Decide via `/decomposing`.
