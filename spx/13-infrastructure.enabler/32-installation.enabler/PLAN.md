# Plan

Governing decision: `spx/15-marketplace-state.adr.md` (marketplace state ownership).

Pending re-declaration: this node's assertions declare the superseded user-scope
cache-preservation model — Codex cache symlink retargeting, user-scope marketplace
registration repair, and user-scope plugin-selection restore. Re-declare installation as
repository-checkout-bounded per the ADR: drop the user-scope maintenance and
cache-preservation assertions, and relocate the every-plugin-installs guarantee to the
isolated real-runtime installation harness.

`spx/13-infrastructure.enabler/32-installation.enabler/21-codex-cache-preservation.adr.md`
is superseded by this decision; the pending re-declaration prunes it (not yet pruned in the
current changeset).

Downstream: the isolated real-runtime harness (l2, real `claude`/`codex` binaries in
disposable homes) is a separate implementation slice; no unpublished-dependency gate.
