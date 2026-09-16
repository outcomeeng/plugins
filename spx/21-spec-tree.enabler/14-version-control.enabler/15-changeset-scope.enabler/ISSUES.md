# Issues: Changeset Scope

## Changeset-primitive extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/scope-changeset/scripts/changeset_scope.py` exceeds
fifty lines — branch identity, the on-disk addressing slug, base-ref
resolution, committed selector resolution, the remote-tracking ref form, and merge-base diff scope. Past fifty
lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic
moves into the SPX CLI once the script proves its value; these primitives have
proven their value in use, so extraction is what they owe.

This module is the single home the audit, review-changes, sync-base, merge, and
coherence-audit skills all import rather than re-deriving, so its extraction
also removes the shipped-script debt those consumers inherit through it.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository.

**Resolution shape**: port the derivation primitives into the SPX CLI as a
consumable command surface, publish it, advance the floor, and repoint every
consuming skill at the published capability. Keep the one-derivation invariant
across the move — no consumer re-implements base-ref resolution or diff scope.
Revisit when the capability publishes.

## An explicit range with a local-ref base bypasses the currency refusal

`require_current_base` fetches and compares only when the base is an `origin/` remote-tracking ref. An explicit range whose base is a bare local ref or a commit id — `main...HEAD`, `<sha>...HEAD` — is accepted by `resolve_committed_scope`, skips the fetch, and compares the head against the unfetched local ref, so on a checkout whose local `main` lags `origin/main` the head passes as current. Every relay accepts a caller-supplied explicit range through `SPX_VERIFY_BASE_REF` or the selector, and `spx/21-spec-tree.enabler/14-version-control.enabler/15-changeset-scope.enabler/13-changeset-derivation.adr.md` states the refusal for a committed selector without narrowing it to `origin/` bases.

**Resolution shape**: decide explicit-range semantics — either resolve a local-ref base to its remote-tracking counterpart and fetch that, or narrow the decision and its NEVER rule to git-derived and `origin/` bases — then add the scenario that states which holds. The first choice reaches the reviewing-changes node, whose runner scenarios all drive `review_run.py` with `SPX_VERIFY_BASE_REF=main` on a repository that has no origin, so those tests move to the bare-origin topology in the same change.

**Settlement condition**: the decision names the base forms the refusal covers, a linked scenario exercises a local-ref explicit range, and the reviewing-changes runner scenarios pass on the chosen topology.

**Evidence**: local review run `2026-09-16_13-15-03-548-baeb88a84744` on head `39849613a20c94cc3a0ec58cb20c391dc8d92ddc`, finding F-001.
