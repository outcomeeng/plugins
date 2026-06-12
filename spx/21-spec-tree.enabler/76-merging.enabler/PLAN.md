# Plan: Merging Enabler

## Eval recalibration (out-of-band)

The `production-readiness` eval (`ISSUES.md`) and the `merge-readiness` eval data-model change (`32-github-pr.enabler/54-managing-pr.enabler/ISSUES.md` item 5, now also carrying the bounded-vs-deferrable disposition dimension) require live eval re-runs; they ride the next eval-coverage sweep, not a mechanical edit.

## Direct-push transport: remaining work

The `/merge` dispatcher and the direct-push variant-1 execution path (direct to `origin/main`) are built. The remaining direct-push work — variant 2 (direct to a local trunk checkout) and the `[audit]`→`[eval]` upgrade once a consumer needs the execution evidence — is tracked in `32-direct-push.enabler/PLAN.md`.
