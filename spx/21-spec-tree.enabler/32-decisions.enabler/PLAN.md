# PLAN — Auditor-skeleton sweep: audit-pdr, audit-adr

**Status:** queued in the marketplace-wide auditor-skeleton sweep (concern B session). Delete this file when the work lands.

## What

`audit-pdr` and `audit-adr` deviate from the canonical auditor structure in `src/plugins/develop/skills/skill-standards/references/auditor-skeleton.md`: an activity-shaped `<objective>` (should name the verdict and its finding categories) and a workflow-step `<success_criteria>` (should state verdict soundness), with no `<constraints>` block. They already use `<verdict_format>`. Bring each to the skeleton, modeling the reference-conformant `develop:audit-skills`.

The `ISSUES.md` entry "audit-skill family carries codebase-wide standards deviations" in this node tracks the same defect class.

## Notes

- **No commands dependency.** These skills do not touch `audit-skills` / `create-skills`, so they are independent of the command-removal effort (`spx/43-develop.enabler/PLAN.md`).
- Part of one marketplace-wide sweep; coordinate via the concern-B session and `spx/43-develop.enabler/ISSUES.md` §0/§1.

## Gate

`develop:skill-auditor` on each changed skill, `just build-skills`, bump spec-tree, `just check`, `/merge`.
