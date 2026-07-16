# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Spec aligned: sync.md now declares the checkout-bounded model at design level (`[audit]`) —
sync reconciles only the invocation checkout's committed runtime marketplace configuration and
never mutates a developer's user-scope registrations, plugin caches, or agent directories. The
superseded user-scope orchestration assertions are removed from the spec. The node's existing
user-scope tests and implementation are retained — no longer linked to any declared assertion
— until the production cutover reconciles them.

Pending implementation (production cutover of `just sync-marketplace`):

- Rewrite the sync implementation to the checkout-bounded model, dropping user-scope
  marketplace-registration reconciliation, plugin-cache reconciliation, and
  compatibility-symlink handling.
- Materialize the design-level assertions as concrete `[test]`-lane assertions with co-located
  tests once the bounded implementation exists.
- Resolve the release-path contradiction: the post-merge "Release marketplace sync" in
  `spx/local/merging.md` invokes `just sync-marketplace`, which under the superseded model
  refreshes the maintainer's live user-scope installation. Move the release path to the
  checkout-bounded model and establish install completeness through the isolated harness. This
  touches `spx/15-merging.pdr.md`'s `RELEASE_READINESS` instantiation.

Until the cutover lands, the live `just sync-marketplace` implementation runs the superseded
user-scope model and is not covered by node tests.
