# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Spec alignment applied: `sync.md` now declares the checkout-bounded model. The superseded
assertions are removed — Codex cache-topology inspection, user-scope marketplace-registration
reconciliation, canonical default-branch-worktree source resolution, and the file-backed
single-flight lock coordination that serialized user-scope cache repair. The surviving guards are
preserved: the change probe compares `base_ref` against the working tree rather than `HEAD`; no
validation step is skipped when plugin distribution paths change; tool availability is checked
before any orchestration step, with the tool list narrowed to drop `ps` (which served only the
removed lock's zombie-owner check). The `codex_cache_preserve` prohibition cites the governing
decision directly.

Pending implementation (production cutover of `just sync-marketplace`):

- Rewrite the sync implementation to the checkout-bounded model, dropping user-scope
  marketplace-registration reconciliation, plugin-cache reconciliation, and
  compatibility-symlink handling, and updating `tests/test_sync.scenario.l1.py` and
  `tests/test_sync.compliance.l1.py` to the reduced orchestration.
- Resolve the release-path contradiction: the post-merge "Release marketplace sync" in
  `spx/local/merging.md` invokes `just sync-marketplace`, which under the superseded model
  refreshes the maintainer's live user-scope installation. Move the release path to the
  checkout-bounded model and establish install completeness through the isolated harness. This
  touches `spx/15-merging.pdr.md`'s `RELEASE_READINESS` instantiation.
