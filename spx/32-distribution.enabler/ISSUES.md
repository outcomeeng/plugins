# ISSUES -- distribution enabler

Coordination note; not spec truth.

## DEBT [structure]: split distribution workflow boundaries

Implementation audit `019f2777-97ab-7a03-89d3-30e61c4c820e` raised a decomposition finding: `spx/32-distribution.enabler/distribution.md` carries more than roughly seven assertions and mixes independently validated concerns:

- skill collection and metadata extraction
- target cleanup and copy behavior
- workflow compliance for distribution triggers and interpreter selection

The audit cited `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md`, whose decomposition rule treats more than roughly seven assertions as a signal for analysis and separates independent concerns when each concern has a meaningful validation boundary.

Revisit condition: when structural work on `spx/32-distribution.enabler` is scheduled, invoke `/decompose` on the distribution node. Split the skill-copying behavior and workflow-compliance concerns into focused child nodes when the ordering-evidence matrix supports the split.

Chosen handling: this branch records the structure debt and continues the generated Codex-agent config enforcement change. The branch does not move or rewrite the existing distribution assertions.

## DEBT [predicate-ownership]: the distribution harness decides verdicts its linked tests should own

Defect class: `predicate-ownership`.

Finding: `outcomeeng_testing/harnesses/distribution.py` returns pass or fail as a bare `bool` from `skill_collection_returns_complete_metadata`, `plugin_without_skills_is_skipped`, `skill_without_manifest_is_skipped`, `directive_description_is_cleaned`, `target_cleanup_preserves_only_git_metadata`, `skill_copy_skips_broken_symlinks`, `distribution_workflow_uses_runtime_and_source_paths`, and `distribution_workflow_uses_project_python`, and `_generated_skill_collection_union_holds` calls `assert` itself. The predicate-seam rule of `/test-evidence-standards` reserves every pass-or-fail decision for the linked test; infrastructure returns observations.

Evidence: `spec-tree:test-evidence-auditor` finding f-004, severity `REJECT`, raised against `spx/18-plugin-build.enabler/43-target-emission.enabler` at head `c2d6ad239f6e60a90a2c172eafb80d0cba83477b` during Change #200, because that node's harness imports this module. Change #200 does not change the module.

Impact: a failing distribution test reports a bare `False` instead of the observed value, and every node whose evidence chain imports this harness carries the finding into its own test-evidence audit.

Settlement condition: each helper returns the observation its comparison consumes, the comparison moves into the linked test under `spx/32-distribution.enabler/tests/`, and a test-evidence audit of this node raises no `predicate-ownership` finding.

## Plugin changelog titles use two forms

Most plugin changelogs open with "# Changelog — {plugin} plugin", and a minority open with the dash-free "# {Plugin} plugin changelog", the form the prose canon's em dash rule requires. `head -1` over every `src/plugins/*/CHANGELOG.md` derives which titles stand in which form, so this entry names that relation and no count: a count falsified twice, once when a plugin was added and once when a changeset renamed a single title, and neither edit was in view of the sentence holding the figure.

**Settlement condition.** One sweep renames every title still carrying the dash, and the entry closes when that derivation yields the dash-free form for every plugin. The sweep touches every plugin whose title still carries the dash, so it stands outside any one plugin's changeset.

## DEBT [evidence]: the linked test asserts a bare boolean from skill_collection_returns_complete_metadata (f-001) `outcomeeng_testing/harnesses/distribution.py`, `skill_collection_returns_complete_metadata`, `predicate ownership`

Nine findings (all REJECT, assertion-seam, predicate ownership) on the tests under `spx/32-distribution.enabler/tests`, each against `outcomeeng_testing/harnesses/distribution.py`. Each linked test only runs `assert <bool>`; the harness builds the expected value, compares, and returns a bare boolean, so a failure reports `False` with no observation. The entry "the distribution harness decides verdicts its linked tests should own" above records the same defect class; this entry adds the per-test findings of the later audit and repeats no resolution text from it.

- f-001 `test_distribute_skills.scenario.l1.py:12` `skill_collection_returns_complete_metadata`.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness returns observations and handles, and each linked test owns its predicate and expected value.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited tests or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness `outcomeeng_testing/harnesses/distribution.py` drives `outcomeeng/distribution/distribute.py` and `outcomeeng/distribution/orchestration.py`, which the changeset does not change.

**Settlement condition**: every cited test owns its predicate and expected value over an observation the harness returns, and a test-evidence audit of this node raises none of f-001 to f-009.

## DEBT [evidence]: the linked test asserts a bare boolean from plugin_without_skills_is_skipped (f-002) `outcomeeng_testing/harnesses/distribution.py`, `plugin_without_skills_is_skipped`, `predicate ownership`

Nine findings (all REJECT, assertion-seam, predicate ownership) on the tests under `spx/32-distribution.enabler/tests`, each against `outcomeeng_testing/harnesses/distribution.py`. Each linked test only runs `assert <bool>`; the harness builds the expected value, compares, and returns a bare boolean, so a failure reports `False` with no observation. The entry "the distribution harness decides verdicts its linked tests should own" above records the same defect class; this entry adds the per-test findings of the later audit and repeats no resolution text from it.

- f-002 `test_distribute_skills.scenario.l1.py:16` `plugin_without_skills_is_skipped`.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness returns observations and handles, and each linked test owns its predicate and expected value.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited tests or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness `outcomeeng_testing/harnesses/distribution.py` drives `outcomeeng/distribution/distribute.py` and `outcomeeng/distribution/orchestration.py`, which the changeset does not change.

**Settlement condition**: every cited test owns its predicate and expected value over an observation the harness returns, and a test-evidence audit of this node raises none of f-001 to f-009.

## DEBT [evidence]: the linked test asserts a bare boolean from skill_without_manifest_is_skipped (f-003) `outcomeeng_testing/harnesses/distribution.py`, `skill_without_manifest_is_skipped`, `predicate ownership`

Nine findings (all REJECT, assertion-seam, predicate ownership) on the tests under `spx/32-distribution.enabler/tests`, each against `outcomeeng_testing/harnesses/distribution.py`. Each linked test only runs `assert <bool>`; the harness builds the expected value, compares, and returns a bare boolean, so a failure reports `False` with no observation. The entry "the distribution harness decides verdicts its linked tests should own" above records the same defect class; this entry adds the per-test findings of the later audit and repeats no resolution text from it.

- f-003 `test_distribute_skills.scenario.l1.py:20` `skill_without_manifest_is_skipped`.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness returns observations and handles, and each linked test owns its predicate and expected value.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited tests or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness `outcomeeng_testing/harnesses/distribution.py` drives `outcomeeng/distribution/distribute.py` and `outcomeeng/distribution/orchestration.py`, which the changeset does not change.

**Settlement condition**: every cited test owns its predicate and expected value over an observation the harness returns, and a test-evidence audit of this node raises none of f-001 to f-009.

## DEBT [evidence]: the linked test asserts a bare boolean from directive_description_is_cleaned (f-004) `outcomeeng_testing/harnesses/distribution.py`, `directive_description_is_cleaned`, `predicate ownership`

Nine findings (all REJECT, assertion-seam, predicate ownership) on the tests under `spx/32-distribution.enabler/tests`, each against `outcomeeng_testing/harnesses/distribution.py`. Each linked test only runs `assert <bool>`; the harness builds the expected value, compares, and returns a bare boolean, so a failure reports `False` with no observation. The entry "the distribution harness decides verdicts its linked tests should own" above records the same defect class; this entry adds the per-test findings of the later audit and repeats no resolution text from it.

- f-004 `test_distribute_skills.scenario.l1.py:24` `directive_description_is_cleaned`.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness returns observations and handles, and each linked test owns its predicate and expected value.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited tests or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness `outcomeeng_testing/harnesses/distribution.py` drives `outcomeeng/distribution/distribute.py` and `outcomeeng/distribution/orchestration.py`, which the changeset does not change.

**Settlement condition**: every cited test owns its predicate and expected value over an observation the harness returns, and a test-evidence audit of this node raises none of f-001 to f-009.

## DEBT [evidence]: the linked test asserts a bare boolean from target_cleanup_preserves_only_git_metadata (f-005) `outcomeeng_testing/harnesses/distribution.py`, `target_cleanup_preserves_only_git_metadata`, `predicate ownership`

Nine findings (all REJECT, assertion-seam, predicate ownership) on the tests under `spx/32-distribution.enabler/tests`, each against `outcomeeng_testing/harnesses/distribution.py`. Each linked test only runs `assert <bool>`; the harness builds the expected value, compares, and returns a bare boolean, so a failure reports `False` with no observation. The entry "the distribution harness decides verdicts its linked tests should own" above records the same defect class; this entry adds the per-test findings of the later audit and repeats no resolution text from it.

- f-005 `test_distribute_skills.scenario.l1.py:28` `target_cleanup_preserves_only_git_metadata`.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness returns observations and handles, and each linked test owns its predicate and expected value.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited tests or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness `outcomeeng_testing/harnesses/distribution.py` drives `outcomeeng/distribution/distribute.py` and `outcomeeng/distribution/orchestration.py`, which the changeset does not change.

**Settlement condition**: every cited test owns its predicate and expected value over an observation the harness returns, and a test-evidence audit of this node raises none of f-001 to f-009.

## DEBT [evidence]: the linked test asserts a bare boolean from skill_copy_skips_broken_symlinks (f-006) `outcomeeng_testing/harnesses/distribution.py`, `skill_copy_skips_broken_symlinks`, `predicate ownership`

Nine findings (all REJECT, assertion-seam, predicate ownership) on the tests under `spx/32-distribution.enabler/tests`, each against `outcomeeng_testing/harnesses/distribution.py`. Each linked test only runs `assert <bool>`; the harness builds the expected value, compares, and returns a bare boolean, so a failure reports `False` with no observation. The entry "the distribution harness decides verdicts its linked tests should own" above records the same defect class; this entry adds the per-test findings of the later audit and repeats no resolution text from it.

- f-006 `test_distribute_skills.scenario.l1.py:32` `skill_copy_skips_broken_symlinks`.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness returns observations and handles, and each linked test owns its predicate and expected value.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited tests or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness `outcomeeng_testing/harnesses/distribution.py` drives `outcomeeng/distribution/distribute.py` and `outcomeeng/distribution/orchestration.py`, which the changeset does not change.

**Settlement condition**: every cited test owns its predicate and expected value over an observation the harness returns, and a test-evidence audit of this node raises none of f-001 to f-009.

## DEBT [evidence]: the linked test asserts a bare boolean from _generated_skill_collection_union_holds (f-007) `outcomeeng_testing/harnesses/distribution.py`, `_generated_skill_collection_union_holds`, `predicate ownership`

Nine findings (all REJECT, assertion-seam, predicate ownership) on the tests under `spx/32-distribution.enabler/tests`, each against `outcomeeng_testing/harnesses/distribution.py`. Each linked test only runs `assert <bool>`; the harness builds the expected value, compares, and returns a bare boolean, so a failure reports `False` with no observation. The entry "the distribution harness decides verdicts its linked tests should own" above records the same defect class; this entry adds the per-test findings of the later audit and repeats no resolution text from it.

- f-007 `test_distribute_skills.property.l1.py:5`: the invariant `actual == expected` is asserted inside `_generated_skill_collection_union_holds`, and `skill_collection_union_holds` returns a constant True.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness returns observations and handles, and each linked test owns its predicate and expected value.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited tests or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness `outcomeeng_testing/harnesses/distribution.py` drives `outcomeeng/distribution/distribute.py` and `outcomeeng/distribution/orchestration.py`, which the changeset does not change.

**Settlement condition**: every cited test owns its predicate and expected value over an observation the harness returns, and a test-evidence audit of this node raises none of f-001 to f-009.

## DEBT [evidence]: the linked test asserts a bare boolean from distribution_workflow_uses_runtime_and_source_paths (f-008) `outcomeeng_testing/harnesses/distribution.py`, `distribution_workflow_uses_runtime_and_source_paths`, `predicate ownership`

Nine findings (all REJECT, assertion-seam, predicate ownership) on the tests under `spx/32-distribution.enabler/tests`, each against `outcomeeng_testing/harnesses/distribution.py`. Each linked test only runs `assert <bool>`; the harness builds the expected value, compares, and returns a bare boolean, so a failure reports `False` with no observation. The entry "the distribution harness decides verdicts its linked tests should own" above records the same defect class; this entry adds the per-test findings of the later audit and repeats no resolution text from it.

- f-008 `test_distribution_workflow.compliance.l1.py:8` `distribution_workflow_uses_runtime_and_source_paths` builds the violating variants and evaluates the predicates in the harness.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness returns observations and handles, and each linked test owns its predicate and expected value.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited tests or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness `outcomeeng_testing/harnesses/distribution.py` drives `outcomeeng/distribution/distribute.py` and `outcomeeng/distribution/orchestration.py`, which the changeset does not change.

**Settlement condition**: every cited test owns its predicate and expected value over an observation the harness returns, and a test-evidence audit of this node raises none of f-001 to f-009.

## DEBT [evidence]: the linked test asserts a bare boolean from distribution_workflow_uses_project_python (f-009) `outcomeeng_testing/harnesses/distribution.py`, `distribution_workflow_uses_project_python`, `predicate ownership`

Nine findings (all REJECT, assertion-seam, predicate ownership) on the tests under `spx/32-distribution.enabler/tests`, each against `outcomeeng_testing/harnesses/distribution.py`. Each linked test only runs `assert <bool>`; the harness builds the expected value, compares, and returns a bare boolean, so a failure reports `False` with no observation. The entry "the distribution harness decides verdicts its linked tests should own" above records the same defect class; this entry adds the per-test findings of the later audit and repeats no resolution text from it.

- f-009 `test_distribution_workflow.compliance.l1.py:12` `distribution_workflow_uses_project_python` likewise.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head `6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run token.

**Resolution shape**: the harness returns observations and handles, and each linked test owns its predicate and expected value.

**Evidence that the text lies outside the change.** `git diff -U0 origin/main...HEAD` reports no hunk in the cited tests or harness, against merge base `149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on anything this changeset changed. The changeset adds symbols to `outcomeeng/distribution/profiles.py`, narrows the guard in `outcomeeng/validation/profile_configuration.py`, and adds model-price and profile-binding generators, harnesses, and tests. The cited harness `outcomeeng_testing/harnesses/distribution.py` drives `outcomeeng/distribution/distribute.py` and `outcomeeng/distribution/orchestration.py`, which the changeset does not change.

**Settlement condition**: every cited test owns its predicate and expected value over an observation the harness returns, and a test-evidence audit of this node raises none of f-001 to f-009.
