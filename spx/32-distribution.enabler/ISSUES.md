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
