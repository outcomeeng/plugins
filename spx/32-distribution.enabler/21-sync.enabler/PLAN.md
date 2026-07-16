# Plan

Governing decision: `spx/12-marketplace-state.adr.md` (marketplace state ownership).

Pending re-declaration: re-declare sync as repository-root bounded — reconcile only the
invocation checkout's committed runtime configuration. Remove user-scope marketplace
registration reconciliation, user plugin-cache reconciliation, and compatibility-symlink
handling from this node's declared behavior; those belong to the superseded user-scope model.

Release-path contradiction to resolve in the same cutover: the post-merge "Release
marketplace sync" in `spx/local/merging.md` invokes `just sync-marketplace`, which under the
current model runs `claude plugin marketplace update outcomeeng` and refreshes the
maintainer's live user-scope installation. Under `spx/12-marketplace-state.adr.md` that
live-install refresh is superseded; the post-merge release path must move to the
checkout-bounded model and establish install completeness through the isolated harness. This
touches `spx/15-merging.pdr.md`'s `RELEASE_READINESS` instantiation and is part of the
production cutover, not this declaration slice.

Downstream: the production cutover of `just sync-marketplace` to the bounded model is a
separate implementation slice.
