# PLAN — align reviewer framing with the validity+phase gate

Deferred to a fresh session, alongside the merge-gate cascade in `spx/21-spec-tree.enabler/76-merging.enabler/PLAN.md`. `spx/15-agent-pr-authority.pdr.md` now decides that the consumer of a review acts on findings by validity and phase, never by severity; the reviewer reports findings and never gates.

## Change

- `reviewing.md` and `21-reviewing-changes.enabler/references/review-prompt.md` (authored under `src/plugins/spec-tree/skills/reviewing-changes/`) state "each consumer applies its own policy by severity". That overstates: the consumer (the merge gate, the author) applies its policy by **validity and phase** per `spx/15-agent-pr-authority.pdr.md`, not "by severity". Reframe to "each consumer applies its own policy"; severity stays the reviewer's reporting label.
- Confirm the reviewer emits findings in one uniform channel with severity as a label and no decision/verdict — already true after the decision-field removal (PR #78); this pass is a framing alignment only, not a behavior change.

## After

- `just build-skills`; `just check`.
