---
name: inspect-review-run
user-invocable: false
description: >-
  ALWAYS invoke this skill after a changes-reviewer returns a raw review run token. NEVER infer the review result from the token or an agent message; inspect the sealed journal prefix through this workflow.
allowed-tools: Bash(python3 "${SKILL_DIR}/scripts/inspect_review_run.py":*)
---

Invoke the `spec-tree:verification-run-journal-standards` skill before proceeding. If that skill is unavailable, report the missing skill and stop.

<objective>
A compact inspection projection for one sealed review journal run, carrying its full identity, scope coverage, finding counts, and findings.
</objective>

<workflow>

Run the skill-owned inspection entrypoint with the raw token returned by the `changes-reviewer`:

```bash
python3 "${SKILL_DIR}/scripts/inspect_review_run.py" <run-token>
```

The entrypoint reads the sealed prefix through `spx journal render --type review --run <run-token>`. When the token is outside the current branch scope, it resolves the unique matching branch through `spx journal list --type review --sealed sealed --limit 200` and renders again with that branch slug.

Pass an explicit branch slug only when a concrete slug is already known:

```bash
python3 "${SKILL_DIR}/scripts/inspect_review_run.py" <run-token> --branch-slug <slug>
```

Treat the rendered output as an inspection projection of the sealed journal prefix. The sealed prefix remains the only review result.

</workflow>

<success_criteria>

- The raw review token is rendered through the skill-owned entrypoint.
- The output carries terminal status, full head and base identity, scope coverage, blocking and debt counts, and every finding present in the sealed prefix.
- A missing, ambiguous, invalid, unsealed, or unrenderable run remains a blocking diagnostic rather than an inferred verdict.

</success_criteria>
