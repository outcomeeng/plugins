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

## Most compliance evidence keeps its predicate in the harness

`tests/test_source_and_templating.compliance.l1.py` states most of its assertions as `assert <harness_call>()`, where the harness function in `outcomeeng_testing/harnesses/source_and_templating.py` embeds the comparison and returns a bare `bool`. `well_formed_source_tree_builds`, `malformed_source_tree_is_rejected`, `ordinary_plugin_root_file_is_accepted`, `unrecognized_plugin_subdirectories_are_rejected`, `shared_topic_without_fragment_is_rejected`, `shared_topic_references_travel_with_fragment`, `include_uses_fragment_file_contract`, `jinja_environment_uses_custom_delimiters`, the five `require_skill_*` predicates, `bare_conditional_renders_per_target`, and `skill_dir_escape_survives_jinja_pass` each decide the verdict inside the harness. A reader of the linked test cannot see which condition failed, and the harness owns evidence the test file is supposed to own.

These back the assertions at `source-and-templating.md` lines 21 and 24 through 29 and 31. The one assertion at line 30 is the counter-example already in the file: `test_build_comment_is_stripped_without_other_jinja_tokens` holds three named predicates and consumes `observe_build_comment_outputs`, which returns each target's rendered body and the comment it carried rather than a verdict.

**Resolution shape**: convert each harness predicate to an observation function returning the values its comparison consumes, and move the comparison into the linked test, one assertion at a time. The line-30 pair is the shape to copy. Re-run the test-evidence audit per assertion rather than per file, because the conversions are independent.

**Evidence**: raised as ten `REJECT` findings by the test-evidence auditor against the path-boundary changeset. That changeset is purely additive here — it added the line-30 assertion, its test, and `observe_build_comment_outputs`, and modified no existing test or harness function — so the defect predates it and spans eight assertions it does not govern. Recorded rather than carried because converting another node's evidence architecture is its own slice with its own audit gate. An earlier run of the same auditor over the same content returned `APPROVED`, so treat the verdict as a prompt to inspect the predicate seam rather than as a settled count.

## The no-single-plugin rule is proved only against conforming bodies

`test_per_plugin_template_body_names_no_single_plugin` scans the real committed template bodies under `CANONICAL_SOURCE_ROOT` and asserts its forbidden-identity regex matches none of them. No case constructs a body that does hardcode a plugin slug, so the regex's detection capability is never exercised: a pattern that matched nothing would pass the same way. A compliance assertion earns its evidence from a violating case.

**Resolution shape**: add a violating body to the parametrized domain and assert the regex reports it, keeping the conforming scan as the second half. This also gives the entry above — the one recording that the same test matches path-shaped and skill-identity-shaped occurrences but not a quoted value in a condition — a place to prove which shapes are detected.

**Evidence**: raised as a `REJECT` finding by the test-evidence auditor against the path-boundary changeset, which neither authored this assertion nor edited this test.

## Linked tests delegate their predicates to boolean-returning harnesses

Twenty-three test-evidence findings on this node's seven linked test files, its
harness, and one generator share one class with the entry "Property predicates
are hidden in boolean-returning harnesses" in
`spx/18-plugin-build.enabler/ISSUES.md`:

- `test_parse_directives.scenario.l1.py`, `test_render_text.scenario.l1.py`,
  `test_parse_directives.property.l1.py`, `test_expand_include.property.l1.py`,
  `test_render_text.property.l1.py`, and most assertions of
  `test_source_and_templating.compliance.l1.py` assert only a boolean returned by
  `outcomeeng_testing/harnesses/source_and_templating.py`, which owns the
  equality, membership, and exception predicates (findings `f-001` through
  `f-017`, `f-019`, `f-020`).
- `test_per_plugin_template_body_names_no_single_plugin` scans the committed
  conforming body only and constructs no violating template (finding `f-021`).
- `outcomeeng_testing/generators/fragments.py` restates the standard Jinja
  delimiters, and the harness restates the frontmatter delimiter, the skill-name
  field, and `dist` in place of the constants `outcomeeng/distribution/contracts.py`
  owns (findings `f-022` through `f-024`).

The repair is a rewrite of the node's evidence seam — observation-returning
harnesses, test-owned predicates, one violating template fixture, and imported
constants — across the seven test files, the harness, and the generator; Change
#85 owns the deterministic-evidence hardening of this subtree.

**Settlement condition**: every linked test carries its own predicate over a
harness observation, the generator and harness import the owned constants, and a
passing test-evidence audit of this node.

**Evidence**: `spec-tree:test-evidence-auditor` verdict `REJECTED` on head
`a65659114b99767b90b4d920550fff5dc0824794` during Change #76; the one finding that changeset caused (`f-018`, a
restated spec literal in the `require_skill` test) was fixed in the changeset.

## The authored-source predicate admits stray workspace artifacts

`_is_authored_source_file` in `outcomeeng/distribution/build.py` rejects a file only for an ignored directory name or an ignored file suffix, so a stray workspace artifact with neither — a macOS metadata file, a Spotlight index marker — counts as authored source. Two consequences follow. A skill directory a rebase leaves holding only such a file fails validation for a missing manifest, which is the situation the absence rule removes for cache-only directories. The same file is also projected as a copy emission into both generated trees, where the source-to-output parity step then reports it.

The root harness guides name that artifact class together with the Python cache in one cleanup rule, so the build-side declaration is narrower than the class the guides describe.

**Resolution shape**: give the predicate a third input beside its ignored directory names and file suffixes — a set of ignored file names — and restate the absence assertion in terms of the whole class. No file of the class exists under `src/` today, so the generated trees do not change when it lands.

**Why separate**: Change #119's Frame settles the absence rule on the predicate the emission walk already applies, keyed on the declared ignored directory names and file suffixes. Adding a class of ignored artifact widens that predicate beyond the attested Frame, so it is a Change of its own rather than work for the changeset that surfaced it.

**Evidence**: `spec-tree:changes-reviewer` run `2026-09-21_16-03-29-169-c48d77290660`, debt finding on `source-and-templating.md`, raised against head `39f60328b985a254743073f95c6d134cc56e0adc`.

## The custom-delimiter assertion's evidence compares the source to itself

`source-and-templating.md` declares the Jinja2 environment's custom delimiters as literals and links `tests/test_source_and_templating.compliance.l1.py` for them. The linked evidence compares the environment's configured delimiters against the same constants `outcomeeng/distribution/build.py` declares, so mutating those constants leaves the test passing. A value the spec tree declares and a source complies with is audit evidence, because every oracle for that agreement is a second declaration.

**Resolution shape**: split the declared delimiter literals onto an `[audit]` assertion and leave the behavior the delimiters govern — a body carrying standard Jinja syntax passing through unchanged, a custom block rendering per target — on its test links. The clean node's spec carries the same split as its worked example.

**Why separate**: the repair deletes `jinja_environment_uses_custom_delimiters`, one of the boolean-returning harness predicates the entry "Linked tests delegate their predicates to boolean-returning harnesses" records, whose settlement condition assigns this node's evidence-seam rewrite to Change #85. Removing that predicate ahead of the rewrite splits one seam repair across two changesets.

**Evidence**: found by the same-class scan over both governed nodes' specs during Change #119 round 3, prompted by the implementation audit's blocking finding on the clean node's parallel assertion in run `2026-09-21_16-03-52-930-bb909cac6a0a`.
