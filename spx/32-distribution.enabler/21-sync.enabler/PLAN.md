# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

`sync.md` carries its full assertion set, and every assertion keeps its linked evidence. The
node is passing. The `codex_cache_preserve` prohibition cites the governing decision directly,
replacing its citation to the pruned node decision.

Pending alignment — remove only what the decision directly supersedes: Codex cache-topology
inspection, user-scope marketplace-registration reconciliation, canonical
default-branch-worktree source resolution, and the file-backed single-flight lock coordination
that exists to serialize user-scope cache repair.

Preserve the assertions the decision does not govern:

- The change probe compares `base_ref` against the working tree rather than `HEAD`.
- No validation step is skipped when plugin distribution paths change.
- Tool availability is checked before any orchestration step. The rule survives; its tool list
  narrows, because `ps` exists only for the lock's zombie-owner check.

Declare the decision's new truth as assertion text, then route each assertion through `/test`
for its verification type and assertion type.

Pending implementation (production cutover of `just sync-marketplace`):

- Rewrite the sync implementation to the checkout-bounded model, dropping user-scope
  marketplace-registration reconciliation, plugin-cache reconciliation, and
  compatibility-symlink handling.
- Resolve the release-path contradiction: the post-merge "Release marketplace sync" in
  `spx/local/merging.md` invokes `just sync-marketplace`, which under the superseded model
  refreshes the maintainer's live user-scope installation. Move the release path to the
  checkout-bounded model and establish install completeness through the isolated harness. This
  touches `spx/15-merging.pdr.md`'s `RELEASE_READINESS` instantiation.
