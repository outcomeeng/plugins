# PR Opening Protocol

PROVIDES the pull-request opening protocol — `REVIEW_READINESS` evaluation, branch push with an explicit destination ref, ready pull-request creation, and the first review-and-check heartbeat
SO THAT the GitHub-PR transport's `/github-pr` orchestration
CAN publish a changeset as a ready-for-review pull request the moment `REVIEW_READINESS` holds, per `spx/15-merging.pdr.md`

## Assertions

### Scenarios

- Given deterministic verification passes and the local `changes-reviewer` review has converged — every finding fixed or split out of the diff and captured in `ISSUES.md` / `PLAN.md` — when `/opening-pr` evaluates `REVIEW_READINESS`, then it creates the pull request `ready_for_review`, never as a draft gating step ([eval](evals/review-readiness/eval.toml))

### Compliance

- ALWAYS: `/opening-pr` re-establishes both `REVIEW_READINESS` predicates — deterministic verification and the local `changes-reviewer` review — on the diff the opening push publishes, per `spx/15-merging.pdr.md` ([review])
- NEVER: open the pull request as a draft as a gating mechanism, or add a separate gated draft-to-ready promotion — the pull request opens ready once `REVIEW_READINESS` holds, per `spx/15-merging.pdr.md` ([review])
