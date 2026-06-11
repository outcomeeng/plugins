# Direct-push Transport

PROVIDES the direct-push merge transport — publishing a verified changeset straight to the remote trunk without a pull request
SO THAT a project that selects it in `spx/local/merging.md`, and any coordination-note-only changeset
CAN integrate under the same merging gates with the review predicate bound to the local review, per `spx/15-merging.pdr.md`

## Assertions

### Compliance

- ALWAYS: the direct-push transport publishes the changeset to the remote trunk only once `REVIEW_READINESS` holds — deterministic verification passes and the local `changes-reviewer` review has converged — per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: the direct-push transport binds the `MERGE_READINESS` review predicate to the local `changes-reviewer` review, since no CI review exists, and applies `PRODUCTION_READINESS` unchanged, per `spx/15-merging.pdr.md` ([audit])
- NEVER: the direct-push transport opens a pull request or waits on a CI review — the local review is the review predicate, per `spx/15-merging.pdr.md` ([audit])
