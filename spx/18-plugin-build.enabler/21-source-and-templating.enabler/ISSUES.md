# ISSUES — source and templating

Known defects and contradictions in the per-plugin template surface. Each entry names the artifact, the rule it violates, and the smallest unit of work that resolves it.

## `agent` names two different things in the plugin lifecycle template

`src/templates/plugin/SKILL.md` uses `agent` for the running harness — `on the running agent` in the description, `authoritative for the agent this copy was rendered for`, `Placement does not apply on this agent` — and for a subagent configuration file — `agent definitions`, `agent directory`. One sentence in the namespace section carries both senses. The body renders into twenty plugin trees across two harnesses, so the ambiguity ships everywhere. `harness` is this product's established term for the Claude Code versus Codex distinction and reads unambiguously in every position the platform sense occupies.

**Resolution shape**: replace the platform sense with `harness` throughout the template body, leaving `agent definitions` and `agent directory` for the file sense, then rebuild both runtime trees and re-audit the skill surface. The sections carrying the platform sense — placement, commit, namespace, and the failure modes — are untouched by changelog work, so this is a terminology pass over the lifecycle mechanism rather than a change to what any verb does.

**Evidence**: raised as `worth-improving` by the skill auditor against the methodology-versioning changeset, whose own edits to this file are confined to the frontmatter grant, `<verbs>`, `<changelogs>`, and `<success_criteria>`.

## The no-single-plugin rule forbids in text what its enforcement permits in fact

`source-and-templating.md` states that a per-plugin template body names no single plugin. `src/templates/plugin/SKILL.md` selects its `<changelogs>` and `<success_criteria>` variants on `{!% if plugin_name == 'spec-tree' %!}`, which is a literal single-plugin identifier in the body's control flow, so the rule's text forbids it. `test_per_plugin_template_body_names_no_single_plugin` does not flag it, because that test matches path-shaped and skill-identity-shaped occurrences rather than a quoted value in a condition.

The rule's purpose is satisfied and its text is not. A build-time predicate never reaches a rendered body: no generated non-spec-tree copy contains the identifier, so no consumer reads a name belonging to a plugin it does not have. What the rule protects against is a rendered body naming one plugin, and the enforcement matches that narrower reading while the assertion states the broader one.

**Resolution shape**: pick one of two. Bind a capability-scoped render variable — `carries_marketplace_changelog` or similar — in `outcomeeng/distribution/build.py` beside the existing `plugin_name` and `target`, so the branch reads as a capability check and the identifier leaves the template entirely; this needs test coverage for the new variable. Or narrow the assertion in `source-and-templating.md` to the rendered body and record the conditional-predicate pattern as sanctioned, matching what the test already enforces; this is a spec change and needs a spec audit. The first removes the construct, the second legitimizes it.

**Evidence**: raised as `worth-improving` by the skill auditor against the marketplace-changelog relocation, which introduced the conditional in both sections. The same audit confirmed empirically that no rendered non-spec-tree copy contains the identifier.

## A fixed cross-plugin composition target has no way to satisfy both governing rules

`/skill-standards` `<skill_organization>` requires a composing skill to name the exact installed skill it invokes. `spx/18-plugin-build.enabler/21-source-and-templating.enabler/source-and-templating.md` requires a per-plugin template body to name no single plugin, because one body renders into every plugin, and `test_per_plugin_template_body_names_no_single_plugin` enforces it against skill-identity and path positions.

The `<changelogs>` section of `src/templates/plugin/SKILL.md` needs both at once: its composition target is permanently one plugin, so the exact identifier is a single-plugin name by construction and going generic is impossible. Writing the literal identifier fails the compliance test; describing the target passes it and leaves the identifier derivable from the `{{! plugin_name !}}-plugin` convention the same file demonstrates. Neither rule records this case, so the next author meeting it repeats the failed attempt.

**Resolution shape**: record the exception in `/skill-standards` `<skill_organization>` — a composition target fixed to one plugin, inside a body that fans out to every plugin, is named descriptively when the exact identifier is deterministically derivable from a documented naming convention. The fix lives in the `instructions` plugin's standards skill, outside the templating surface this node owns.

**Evidence**: raised as `worth-improving` by the skill auditor, which judged the conflict genuine and the descriptive form the correct practical answer.
