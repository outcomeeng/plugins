# Sync Continuation Plan

## Watcher-Safe Marketplace Sync

Build this from the Codex cache topology truth declared by `spx/13-infrastructure.enabler/32-installation.enabler/installation.md` and governed by `spx/13-infrastructure.enabler/32-installation.enabler/21-codex-cache-preservation.adr.md`. Use the shared health predicate exposed by `outcomeeng.distribution.codex_cache.codex_cache_topology_errors` as the implementation contract for the sync probe.

Observable path:

- Invocation: a folder watcher invokes `just sync-marketplace <base-ref>` from the marketplace-source worktree after Codex cache churn.
- Input state: no plugin distribution paths changed since `<base-ref>`, runtime marketplace sources already point at the canonical local source, and Codex cache topology is either valid or invalid.
- Behavior:
  - If distribution paths changed or source reconciliation repaired runtime configuration, sync keeps the full refresh sequence including final strict Codex local refresh.
  - If neither changed and topology is valid, sync exits 0 after source reconciliation and health inspection without running marketplace refresh mutations.
  - If neither changed and topology is invalid, sync runs the full refresh sequence.
  - Concurrent watcher repair invocations are single-flight: one sync owns a no-change invalid-topology repair, later no-change repair invocations observe the active run, record pending state, and exit 0 without launching a second refresh.
  - Distribution-change-driven or configuration-repair-driven sync cannot coalesce behind an active refresh: it exits non-zero rather than reporting success without running the required validation sequence.
- Persistence or side effect: no durable state outside the cache directory except a short-lived lock/pending marker used by the running sync process.
- Inspection surface: sync output states whether it skipped for healthy topology, ran because topology was invalid, exited because another sync owns an active no-change repair, or failed because a change-driven/configuration-repair-driven sync encountered an active refresh.

Failure behavior:

- A stale lock whose owning process is absent is treated as stale and replaced.
- A topology check failure caused by unreadable Codex CLI output fails loudly rather than pruning or assuming health.
- No shell polling loop, background keep-alive, or `sleep` command is introduced.

Acceptance evidence:

- Add sync tests for healthy topology skip, invalid topology refresh, active single-flight exit, and stale-lock replacement.
- Keep the final strict Codex local refresh in the full sequence.
- Run `just test spx/32-distribution.enabler/21-sync.enabler/tests/test_sync.scenario.l1.py`.
