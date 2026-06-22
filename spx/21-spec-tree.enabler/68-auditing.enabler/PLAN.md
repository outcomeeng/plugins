# PLAN — Auditor-skeleton sweep: audit-specs, audit-tests

**Status:** queued in the marketplace-wide auditor-skeleton sweep (concern B session). Delete this file when the work lands.

## What

`audit-specs` and `audit-tests` (this node's audit skills) deviate from the canonical auditor structure in `src/plugins/develop/skills/skill-standards/references/auditor-skeleton.md`: an activity-shaped `<objective>` (should name the verdict and its finding categories), a `<success_criteria>` that lists workflow steps (should state verdict soundness), and a missing `<constraints>` block. Bring each to the skeleton; `develop:audit-skills` is the reference-conformant exemplar to model.

## Notes

- **No commands dependency.** These skills do not touch `audit-skills` / `create-skills`, so they are independent of the command-removal effort (`spx/43-develop.enabler/PLAN.md`) and can proceed regardless of its order.
- Part of one marketplace-wide sweep; coordinate via the concern-B session and `spx/43-develop.enabler/ISSUES.md` §0/§1.
- Per `spx/14-verification.pdr.md` property 7, fix the deviation as a defect class across the audit family, not site-by-site.

## Gate

`develop:skill-auditor` on each changed skill, `just build-skills`, bump spec-tree, `just check`, `/merge`.
