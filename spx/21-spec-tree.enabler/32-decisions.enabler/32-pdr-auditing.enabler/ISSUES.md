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

## The shipped PDR audit still produces the structured JSON verdict

The assertions state the sealed-run verdict model: the audit run's terminal status is `approved` or `rejected`, and the `pdr-auditor` wrapper relays the run token, the run file and the rendered projection. The shipped `src/plugins/spec-tree/skills/audit-pdr/SKILL.md` and the `pdr-auditor` wrapper still emit the `<verdict_format>` JSON object with an `overall` field and no run token or run file, so the `[eval]` expectations and the `[audit]` run-recording assertion describe behavior the shipped producer does not yet have.

**Settlement condition.** outcomeeng/changes#513 rewrites the skill and wrapper onto one `spx verification run` over the PDR file scope and migrates the producer-coupled eval expectations, under an unchanged semantic verdict model.

**Evidence**: current-head CI review of pull request 671, which reads the skill and finds no run token or run file.

## The shipped PDR audit loads context through `/contextualize`

The compliance rule that loads the PDR's context read-only never invokes `/contextualize` or `/sync-base`. `src/plugins/spec-tree/skills/audit-pdr/SKILL.md` Step 1 still reads "use skill `spec-tree:contextualize` on the directory containing the PDR", and `/contextualize` runs `/sync-base`, which rebases the audited branch, so the skill contradicts the rule.

**Settlement condition.** The skill loads the PDR context through the read-only procedure the rule states, without `/contextualize` or `/sync-base`, matching the settlement of the entry in `spx/21-spec-tree.enabler/18-context-loading.enabler/ISSUES.md`; outcomeeng/changes#513 carries the rewrite.

**Evidence**: current-head CI review of pull request 671, `src/plugins/spec-tree/skills/audit-pdr/SKILL.md:51`. The same gap for the test-evidence audit is recorded in `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/ISSUES.md`.
