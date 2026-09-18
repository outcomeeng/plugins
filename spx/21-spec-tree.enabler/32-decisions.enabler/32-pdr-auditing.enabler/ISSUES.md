# Issues

## Eval run history is stale for all three suites

The newest full-suite rows for `evals/structure`, `evals/voice`, and
`evals/tag-validity` are from 2026-06-29 (abbreviated SHA `2100c466`, case
counts one below the current sets); the 2026-07-20 rows are single-case runs on
`82aa90306503a9b61e2b15c3d8613cb7c981879d` and
`a34d6384b1036622b29e392795bd4ea6c7b6efb1`, neither an ancestor of the current
head. The producer `src/plugins/spec-tree/skills/audit-pdr/SKILL.md` was rewritten
between 2026-09-15 and 2026-09-17 (Step 5 tag validity, new rules), the reference
changed, and `prompt.md` was rematerialized, so no committed run proves the current
producer, prompt, and case set. Rows before 2026-07-20 carry abbreviated SHAs and
no model, budget, or timeout fields, so their provenance cannot be tied to an exact
producer.

**Settlement condition**: one passing `just eval-node` run over the three suites
on a head that carries the current producer, with its rows committed to each
`history.jsonl`.

**Evidence**: `spec-tree:eval-evidence-auditor` findings `f-005` through `f-008`
on head `a65659114b99767b90b4d920550fff5dc0824794` during Change #76, whose prototype boundary runs no eval.
