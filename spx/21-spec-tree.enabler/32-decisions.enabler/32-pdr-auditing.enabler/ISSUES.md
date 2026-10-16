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

## The shipped PDR audit loads context through `/contextualize`

The compliance rule that loads the PDR's context read-only never invokes `/contextualize` or `/sync-base`. `src/plugins/spec-tree/skills/audit-pdr/SKILL.md` Step 1 still reads "use skill `spec-tree:contextualize` on the directory containing the PDR", and `/contextualize` runs `/sync-base`, which rebases the audited branch, so the skill contradicts the rule.

**Settlement condition.** The skill loads the PDR context through the read-only procedure the rule states, without `/contextualize` or `/sync-base`, matching the settlement of the entry in `spx/21-spec-tree.enabler/18-context-loading.enabler/ISSUES.md`; outcomeeng/changes#513 carries the rewrite.

**Evidence**: current-head CI review of pull request 671, `src/plugins/spec-tree/skills/audit-pdr/SKILL.md:51`. The same gap for the test-evidence audit is recorded in `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/ISSUES.md`.

## `pdr-auditor` description reads as a launch trigger

The description is directive task-pattern wording that reads as a launch trigger on user phrasing, while a launch belongs to an active skill's explicit instruction.

**Settlement condition.** A description states the role and the calling-skill condition without turning a task pattern into a launch request ([`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md): NEVER infer a launch instruction from a subagent description).

**Evidence**: `instructions:subagent-auditor` finding `inferred_launch` (filed) at `src/plugins/spec-tree/agents/pdr-auditor.md:3-4`. Observed: description: ALWAYS invoke when auditing PDR evidence quality after writing a PDR or before implementing outcomes governed by the PDR. The description lines are unchanged by the changeset. Base range `184cc92eae6e896050a7cc991f63ce953b236ccd..018c692aac828896934db650cd5fa26ce008acee`, sealed run `2026-10-16_16-31-35-473-4df53d56d8ee`.

## `pdr-auditor` carries no retained release-acceptance evidence

The governing decision declares per-harness, per-profile release acceptance, and the tree retains no acceptance artifact for the Claude or Codex Standard row this definition selects.

**Settlement condition.** Retained passing Standard-profile acceptance (native loading and one minimal isolated execution) for each of the Claude and Codex harnesses.

**Evidence**: `instructions:subagent-auditor` finding `release_acceptance_evidence` (filed) at `src/plugins/spec-tree/agents/pdr-auditor.md:6` (profile: standard). Observed: declaration read in [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) (Audit: ALWAYS establish release acceptance separately for each supported harness). No acceptance artifact for the pdr-auditor Standard profile exists under `spx/` or the release record; the profile line is unchanged by the changeset. Base range `184cc92eae6e896050a7cc991f63ce953b236ccd..018c692aac828896934db650cd5fa26ce008acee`, sealed run `2026-10-16_16-31-35-473-4df53d56d8ee`.
