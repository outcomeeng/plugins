# Plan: Merging Enabler

## `/merge` dispatcher skill + `/pr` refocus (declared, implementation pending)

`merging.md` declares the `/merge` transport dispatcher (the transport-dispatch compliance assertions): `/merge` reads `spx/local/merging.md`, selects the transport, and delegates. The `/merge` skill is not yet authored — the specs lead, the implementation follows in the next changeset.

Next changeset:

- Author the `/merge` dispatcher skill: read `spx/local/merging.md`, route a coordination-note-only changeset to the direct-push transport, an overlay-declared transport when present, else the GitHub-PR transport (default), then delegate. Present the proposal-before-mutation pass (mirroring `/pr`).
- Refocus `/pr` to cede transport selection to `/merge` per `32-github-pr.enabler/ISSUES.md` item 2 (PROVIDES, the overlay-route scenarios, the Eval Coverage Model bullet, and the conformance test).
- Extend `spx/local/merging.md` with the `transport:` selector and per-transport config (today's PR merge-command / mention / post-merge content becomes the GitHub-PR transport block).
- Build the direct-push transport execution (`32-direct-push.enabler/PLAN.md`), upgrading its `[audit]` assertions to `[eval]` once the execution path exists.

## Eval recalibration (out-of-band)

The `production-readiness` eval (`ISSUES.md`) and the `merge-readiness` eval data-model change (`32-github-pr.enabler/54-managing-pr.enabler/ISSUES.md` item 5, now also carrying the bounded-vs-deferrable disposition dimension) require live eval re-runs; they ride the next eval-coverage sweep, not a mechanical edit.
