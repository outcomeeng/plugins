# Finding Severity and Disposition

A review classifies each finding by one of two severities — `blocking` for a merge-safety defect, or `debt` for a real defect that does not jeopardize merge safety. The reviewer judges finding validity and severity; the author of the change judges disposition — fixing each `debt` finding within the pull request, or tracking it out of scope in the owning node's `ISSUES.md`/`PLAN.md` with a recorded reason. The reviewer carries no scope or disposition axis.

## Rationale

Severity is a property of the code and the rules, which the reviewer judges from the diff; disposition is a property of the changeset's intended scope, which only the author holds. A third scope-shaped severity makes the reviewer decide what belongs in the pull request — a call it is not positioned to make and one that contradicts a reviewer that emits findings and never decides.

## Product properties

1. A review carries exactly two severities, `blocking` and `debt`, and no severity encodes scope or disposition.
2. The reviewer emits findings with severity only; the author maps each `debt` finding to fixed-in-PR or tracked-out-of-scope with a recorded reason.
3. A `debt` finding the author tracks out of scope with a recorded reason does not block the merge; the merge-blocking judgment reads finding validity and the gate phase, never the severity label.

## Verification

### Audit

- ALWAYS: a review classifies each finding by one of exactly two severities — `blocking` for a merge-safety defect, `debt` for a real defect that does not jeopardize merge safety ([audit])
- ALWAYS: the reviewer judges finding validity and severity only, and the author of the change judges disposition — fix within the pull request, or track in the owning node's `ISSUES.md`/`PLAN.md` with a recorded reason ([audit])
- ALWAYS: a `debt` finding tracked out of scope with a recorded reason is non-blocking, and the merge gate reads finding validity and phase rather than the severity label, per `spx/15-agent-pr-authority.pdr.md` ([audit])
- ALWAYS: the reviewer's rendered review surface carries no disposition axis — the fixed-in-PR versus tracked-out-of-scope distinction lives in the author's `ISSUES.md`/`PLAN.md`, never in the reviewer's render ([audit])
- NEVER: a review carries a `follow_up` severity or any scope or disposition axis — scope is the author's judgment ([audit])
- NEVER: a review classifies a finding by a severity rank (`P0`–`P3`, `critical`/`high`/`medium`/`low`/`minor`/`nit`) or a legacy class label (`NEEDS-ANSWER`, `NOTE`) — the taxonomy is the two severities only ([audit])
