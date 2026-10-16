# Issues

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
