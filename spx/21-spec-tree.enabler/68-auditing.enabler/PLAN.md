# Plan: tighten the audit-orchestrator objective

The `spec-tree/audit` orchestrator `<objective>` narrates its phase sequence
inside the objective:

> One wrapper verdict over a code scope: three orchestrator-owned rows … and one
> dispatched child verdict per language partition … assembled via
> `aggregate_verdicts.py`, recorded on the `spx journal` … rendered … through
> `journal_emit.py`. The run advances deterministically through prepare (Phase 0)
> … emit (Phase 6) …

The phase walk (prepare → gates → tests → review → evidence → compliance → emit)
is `<audit_workflow>` content, not output shape. Per the `develop`
`<objective_shape>` one-sentence rule shipped in PR #317, tighten the objective
to the verdict output and its row/child structure (the wrapper verdict + the
orchestrator-owned rows + one child verdict per language partition), leaving the
phase sequence to `<audit_workflow>`.

This file was outside #319's diff (the orchestrator skill was not edited there),
so it was deferred to this follow-up rather than swept mid-PR.
