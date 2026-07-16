# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Spec aligned: installation.md now declares the checkout-bounded model at design level
(`[audit]`) — installation reconciles only the invocation checkout's committed runtime
marketplace configuration and verifies install completeness through an isolated real-runtime
harness, never preserving or mutating a developer's user-scope caches, registrations, or agent
directories. The superseded user-scope cache-preservation assertions are removed from the
spec, and the superseded `21-codex-cache-preservation.adr.md` is pruned. The node's existing
user-scope tests and implementation are retained — no longer linked to any declared assertion
— until the production cutover reconciles them.

Pending implementation:

- Build the isolated real-runtime installation harness (l2, real `claude`/`codex` binaries in
  disposable runtime homes) that verifies every catalog plugin installs and enables while
  mutating no user-scope state. No unpublished-dependency gate.
- Remove the superseded user-scope installation implementation (Codex cache symlink
  retargeting, user-scope marketplace-registration repair, user-scope plugin-selection
  restore) in the production cutover of `just sync-marketplace`.
- Materialize the design-level assertions as concrete `[test]`-lane assertions with co-located
  tests once the harness and bounded implementation exist.

Until the cutover lands, the live installation implementation runs the superseded user-scope
model and is not covered by node tests.
