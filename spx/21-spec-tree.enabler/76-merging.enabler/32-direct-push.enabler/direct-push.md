# Direct-push Transport

PROVIDES the direct-push merge transport — publishing a verified changeset straight to the default branch on origin without a pull request
SO THAT a project that selects it in `spx/local/merging.md`, and any coordination-note-only changeset
CAN integrate under the same lifecycle with the verification predicates bound locally and absent preview, deploy, or release declarations skipped, per `spx/15-merging.pdr.md`

## Assertions

### Compliance

- ALWAYS: the direct-push transport publishes the changeset to the default branch on origin only once `VERIFICATION_READINESS` holds — deterministic verification passes and the local `changes-reviewer` review has converged when the project declares local review as a predicate — per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: the direct-push transport binds `MERGE_READINESS` to the same observable state that direct publication controls — the local verification and review state plus the push target state — since no pull-request CI review exists; absent deploy or release declarations skip those phases, per `spx/15-merging.pdr.md` ([audit])
- ALWAYS: after direct publication and any declared deploy/release phase handling, the direct-push transport builds the branch-state closeout record, records release-source worktree state when a release or marketplace refresh used one, runs safe cleanup, and either continues remaining in-scope work or invokes `/handoff` plain for operator-useful closeout and continuation disposition; it never substitutes a push, branch, or sync receipt for the closeout ([audit])
- NEVER: the direct-push transport opens a pull request or waits on a CI review — it has no pull-request preview or integration-review surface unless a project declares one separately, per `spx/15-merging.pdr.md` ([audit])
