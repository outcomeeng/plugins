<contents>

- `<catalog_contract>` — identifier, severity, and finding-key rules
- `<frontmatter_rules>` — frontmatter fields, visibility, and grants
- `<naming_and_description_rules>` — skill names and descriptions
- `<structure_rules>` — XML structure, tags, and the auditor skeleton
- `<disclosure_rules>` — line limits, the eager payload, and reference files
- `<organization_rules>` — composition, caller independence, skill types, and conciseness
- `<command_capability_rules>` — arguments, dynamic context, tool grants, and file references
- `<platform_and_script_rules>` — code fences and bundled scripts
- `<harness_rules>` — rules only this harness's standards state
- `<path_boundary_rules>` — scratch storage, external writes, and declines

</contents>

<catalog_contract>

Every rule `SKILL.md` and its references state carries exactly one row below: one stable identifier, one severity, and the section that states the rule. The stating section is authoritative for what the rule requires; the row names the rule and fixes its identifier and severity.

- **Identifier.** Lowercase snake_case, unique across this catalog and the `/agent-prompt-standards` rule catalog. An identifier is never renamed and never reassigned; a retired rule's row is removed, and its identifier stays unused.
- **Severity.** `blocking` marks a defect that must be fixed before the skill ships; `debt` marks any other valid defect. A rule's severity is the one its row declares, never one chosen per finding.
- **Finding key.** A finding against these standards is keyed `<unit>:<rule-id>`: the unit that covers the file it names, and the identifier of the one rule it violates.
- **Closed vocabulary.** A finding names an identifier from this catalog or from the `/agent-prompt-standards` rule catalog. A defect no row covers is a gap in the standard: the rule enters the stating section and this catalog before any finding cites it.

</catalog_contract>

<frontmatter_rules>

| Identifier                      | Severity | Rule                                                                                                                                             | Stated in                                                          |
| ------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `frontmatter_malformed`         | blocking | The file opens with parseable YAML frontmatter.                                                                                                  | `SKILL.md` `<frontmatter>`                                         |
| `name_directory_mismatch`       | blocking | A set `name` equals the skill directory name.                                                                                                    | `SKILL.md` `<frontmatter>`                                         |
| `model_or_effort_override`      | blocking | Frontmatter declares no `model` or `effort` field.                                                                                               | `SKILL.md` `<frontmatter>`                                         |
| `unsupported_frontmatter_field` | blocking | Frontmatter carries only fields the target harness accepts for a skill.                                                                          | `SKILL.md` `<frontmatter>`                                         |
| `reference_skill_frontmatter`   | debt     | A reference skill is hidden from user selection, carries a passive description, and grants only read capability.                                 | `SKILL.md` `<reference_skills>`                                    |
| `audit_skill_grants`            | blocking | An `audit-*` skill grants read tools, the specific Bash verbs its workflow runs, and skill composition only when it composes, never bare `Bash`. | `references/command-capabilities.md` `<tool_restriction_security>` |

</frontmatter_rules>

<naming_and_description_rules>

| Identifier                     | Severity | Rule                                                                                                                                                           | Stated in                         |
| ------------------------------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `workflow_name_form`           | debt     | An invoked workflow skill is named with an imperative verb phrase.                                                                                             | `SKILL.md` `<naming_conventions>` |
| `reference_name_form`          | debt     | A reference skill is a noun phrase ending in the domain it standardizes.                                                                                       | `SKILL.md` `<naming_conventions>` |
| `name_not_user_speech`         | debt     | A name uses the terms and acronyms users say.                                                                                                                  | `SKILL.md` `<naming_conventions>` |
| `vocabulary_precedence`        | debt     | A name that also belongs to a declared methodology taxonomy is judged against that taxonomy and its history before it is called defective.                     | `SKILL.md` `<naming_conventions>` |
| `description_invocation_style` | blocking | A description-match entry point carries a directive description; a reference, protocol, loop-body, or audit skill invoked by exact name carries a passive one. | `SKILL.md` `<descriptions>`       |
| `description_overlap`          | debt     | Adjacent skills' descriptions carry distinct trigger terms.                                                                                                    | `SKILL.md` `<descriptions>`       |

</naming_and_description_rules>

<structure_rules>

| Identifier                      | Severity | Rule                                                                                                                                         | Stated in                                                   |
| ------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `markdown_heading_in_body`      | blocking | The body uses pure XML structure, with no markdown heading.                                                                                  | `SKILL.md` `<xml_structure>`                                |
| `required_tag_missing`          | blocking | Every skill carries `<objective>` and `<success_criteria>`.                                                                                  | `SKILL.md` `<xml_structure>`                                |
| `unclosed_tag`                  | blocking | Every opened tag closes.                                                                                                                     | `SKILL.md` `<xml_structure>`                                |
| `router_tags_incomplete`        | debt     | A router skill carries the router-pattern tags its routing uses.                                                                             | `SKILL.md` `<xml_structure>`                                |
| `workflow_file_tags`            | debt     | A workflow file carries `<required_reading>`, `<process>`, and `<success_criteria>`.                                                         | `SKILL.md` `<xml_structure>`                                |
| `quick_start_on_complete_skill` | debt     | A foundation, gate, validator, reference, or auditor skill carries no `<quick_start>`.                                                       | `SKILL.md` `<xml_structure>`                                |
| `non_semantic_tag_name`         | debt     | Tags carry semantic names and prose cites them by name.                                                                                      | `SKILL.md` `<xml_structure>`                                |
| `structure_complexity_mismatch` | debt     | The tag set matches the skill class in the intelligence-rules table.                                                                         | `SKILL.md` `<xml_structure>`                                |
| `closing_tag_after_list`        | debt     | A blank line separates an unordered list from the closing tag after it.                                                                      | `SKILL.md` `<xml_tag_formatting>`                           |
| `auditor_skeleton_violation`    | debt     | An `audit-*` skill carries the auditor skeleton's sections, names, and order, with no `<quick_start>`.                                       | `references/auditor-skeleton.md` `<skeleton>`               |
| `verdict_shaped_objective`      | debt     | An auditor's objective names the verdict, its scope, its standard, and its finding categories.                                               | `references/auditor-skeleton.md` `<objective_examples>`     |
| `finding_key_outside_catalog`   | blocking | An auditor keys each finding by its unit and the governing standard's catalog rule identifier, and names no identifier outside that catalog. | `references/auditor-skeleton.md` `<skeleton>`               |
| `verdict_soundness_criteria`    | debt     | An auditor's `<success_criteria>` states verdict soundness, never the workflow steps.                                                        | `references/auditor-skeleton.md` `<success_criteria_shape>` |

</structure_rules>

<disclosure_rules>

| Identifier               | Severity | Rule                                                                                                                                                  | Stated in                                 |
| ------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `skill_md_line_limit`    | blocking | `SKILL.md` stays under 500 lines unless the eager-foundation exception applies.                                                                       | `SKILL.md` `<progressive_disclosure>`     |
| `eager_payload_ceiling`  | blocking | A skill under the eager-foundation exception renders to at most 40,000 Unicode code points on every target.                                           | `SKILL.md` `<eager_foundation_exception>` |
| `eager_exception_misuse` | debt     | The exception inlines only material every invocation needs, keeps conditional detail in references, and its justification names only inline material. | `SKILL.md` `<eager_foundation_exception>` |
| `nested_reference`       | debt     | References sit one level below `SKILL.md`, and no reference routes a read to another reference.                                                       | `SKILL.md` `<progressive_disclosure>`     |
| `reference_file_name`    | debt     | A reference file carries a descriptive name.                                                                                                          | `SKILL.md` `<progressive_disclosure>`     |
| `orphaned_reference`     | debt     | `SKILL.md` or a workflow cites every bundled reference file.                                                                                          | `SKILL.md` `<progressive_disclosure>`     |

</disclosure_rules>

<organization_rules>

| Identifier                     | Severity | Rule                                                                                                                              | Stated in                                               |
| ------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `caller_coupling`              | blocking | A skill never names, describes, detects, constrains, refuses, branches on, or depends on its caller or invocation context.        | `SKILL.md` `<skill_organization>`                       |
| `composed_dependency_form`     | blocking | A composing skill states each dependency as the `Use skill` instruction naming the exact installed skill, never a bare mention.   | `SKILL.md` `<skill_organization>`, `<reference_skills>` |
| `foundation_invocation_name`   | debt     | Language-specific prose that references a foundational skill uses its unqualified invocation name.                                | `SKILL.md` `<skill_organization>`                       |
| `composition_result_ownership` | debt     | A composing skill owns sequencing, validates the returned shape, and merges the child result into its own output contract.        | `SKILL.md` `<skill_organization>`                       |
| `composition_grant`            | blocking | A composing skill grants the harness's skill-composition tool as one complete `allowed-tools` item where the harness exposes one. | `SKILL.md` `<skill_organization>`                       |
| `harness_tool_name_in_source`  | debt     | Source authored for more than one harness never spells one harness's skill tool name.                                             | `SKILL.md` `<skill_organization>`                       |
| `speculative_composition`      | debt     | A composition step invokes only the capabilities its workflow requires.                                                           | `SKILL.md` `<skill_organization>`                       |
| `skill_type_sections`          | debt     | A skill carries the key sections its skill type requires.                                                                         | `SKILL.md` `<skill_types>`                              |
| `partial_standards_extraction` | debt     | Standards a creator and an auditor share live in a reference skill, never in one skill's `references/`.                           | `SKILL.md` `<reference_skills>`                         |
| `duplicated_standards`         | debt     | One home holds each standard; no skill restates another skill's rules.                                                            | `SKILL.md` `<reference_skills>`                         |
| `known_content`                | debt     | A skill omits knowledge the executing harness already has.                                                                        | `SKILL.md` `<conciseness>`                              |
| `abstract_guidance`            | debt     | Guidance states concrete commands and thresholds rather than abstractions.                                                        | `SKILL.md` `<conciseness>`                              |

</organization_rules>

<command_capability_rules>

| Identifier                          | Severity | Rule                                                                                                                                                                                             | Stated in                                                                                                             |
| ----------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `missing_argument_hint`             | debt     | A skill that takes arguments declares `argument-hint`.                                                                                                                                           | `references/command-capabilities.md` `<arguments>`                                                                    |
| `orphaned_argument`                 | blocking | Every declared named argument is substituted in the body, and every substituted `$name` is declared.                                                                                             | `references/command-capabilities.md` `<arguments>`                                                                    |
| `argument_capture_regression`       | blocking | Whole-string `$ARGUMENTS` capture is preserved wherever positional tokens would change behavior.                                                                                                 | `references/command-capabilities.md` `<arguments>`                                                                    |
| `empty_argument_behavior`           | debt     | A skill that takes input states what it does when the input is absent.                                                                                                                           | `references/command-capabilities.md` `<arguments>`                                                                    |
| `codex_rendering_assumption`        | debt     | Authored source keeps supported syntax rather than avoiding it for one target's generated output.                                                                                                | `references/command-capabilities.md` `<arguments>`                                                                    |
| `irrelevant_dynamic_context`        | debt     | `<context>` `!` commands load only state the skill consumes, and move workflow inputs to the workflow that reads them.                                                                           | `references/command-capabilities.md` `<dynamic_context>`                                                              |
| `unbounded_dynamic_context`         | debt     | Every `<context>` `!` command is filtered to bounded output that does not grow per load.                                                                                                         | `references/command-capabilities.md` `<dynamic_context>`                                                              |
| `overbroad_allowed_tools`           | blocking | `allowed-tools` grants the narrowest tools and Bash verb patterns the task needs, and no destructive or network tool it does not need.                                                           | `references/command-capabilities.md` `<tool_restriction_security>`                                                    |
| `bundled_file_reference`            | blocking | A bundled file is reached through the authored skill-directory token, never a repository-local, generated, or legacy plugin-root path, and authored source never spells another harness's token. | `references/command-capabilities.md` `<file_references>`, `references/runtime-variables.md` `<skill_file_references>` |
| `product_file_reference`            | debt     | A product file in the consumer's tree is injected with the `@` prefix.                                                                                                                           | `references/command-capabilities.md` `<file_references>`                                                              |
| `skill_directory_token_explanation` | debt     | Skill-directory guidance defines no alias, troubleshooting section, or compatibility-token explanation.                                                                                          | `references/runtime-variables.md` `<skill_file_references>`                                                           |
| `cross_skill_file_path`             | blocking | A file another skill or plugin owns is reached by naming its owning capability, never a manufactured filesystem path.                                                                            | `references/command-capabilities.md` `<file_references>`                                                              |

</command_capability_rules>

<platform_and_script_rules>

| Identifier                  | Severity | Rule                                                                                     | Stated in                                                   |
| --------------------------- | -------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `nested_fence_breakage`     | blocking | No fence nests more than one inner fence of one fewer backtick.                          | `references/platform-constraints.md` `<nested_code_fences>` |
| `script_validation_message` | debt     | A bundled script's errors are verbose, specific, located, actionable, and deterministic. | `references/script-standards.md` `<validation_rule>`        |
| `untested_script`           | blocking | A bundled script is tested before inclusion, error cases and cleanup included.           | `references/script-standards.md` `<script_testing_rule>`    |
| `script_test_record`        | debt     | The skill records what each bundled script was tested with.                              | `references/script-standards.md` `<script_testing_rule>`    |

</platform_and_script_rules>

{!% if target == 'claude' %!}
<harness_rules>

| Identifier                                 | Severity | Rule                                                                                                                                                                                 | Stated in                                                            |
| ------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| `name_format`                              | blocking | `name` uses lowercase letters, numbers, and hyphens, at most 64 characters.                                                                                                          | `SKILL.md` `<frontmatter>`                                           |
| `description_listing_cap`                  | debt     | `description` with `when_to_use` stays within the listing cap, key trigger first.                                                                                                    | `SKILL.md` `<frontmatter>`                                           |
| `disable_model_invocation_on_loaded_skill` | blocking | A skill another skill or a subagent loads never sets `disable-model-invocation: true`.                                                                                               | `SKILL.md` `<frontmatter>`, `<descriptions>`                         |
| `automation_target_not_user_invocable`     | blocking | A skill an automation loop re-enters stays user-invocable.                                                                                                                           | `SKILL.md` `<frontmatter>`                                           |
| `redundant_never_clause`                   | debt     | A description carries a NEVER clause only where it disambiguates.                                                                                                                    | `SKILL.md` `<descriptions>`                                          |
| `artifact_language_order`                  | debt     | A description names the artifact before the language.                                                                                                                                | `SKILL.md` `<descriptions>`                                          |
| `audit_description_routing`                | debt     | An audit skill's description states its subject, judgment, and criteria, and no routing, dispatch, preload, agent, or execution-context statement.                                   | `SKILL.md` `<descriptions>`                                          |
| `reference_toc_missing`                    | debt     | A reference file over 100 lines opens with a table of contents.                                                                                                                      | `SKILL.md` `<progressive_disclosure>`                                |
| `backslash_path`                           | debt     | Every path uses forward slashes.                                                                                                                                                     | `SKILL.md` `<progressive_disclosure>`                                |
| `bang_expansion_syntax`                    | blocking | A `!` command avoids the quoting, globbing, substitution, and loop forms the bash safety checker rejects.                                                                            | `references/platform-constraints.md` `<bash_expansion_restrictions>` |
| `hook_layout`                              | debt     | Hook declarations live in the plugin-root `hooks/` directory, reach scripts through the plugin-root variable, and keep surviving data in the plugin-data directory.                  | `references/plugin-hooks.md` `<hooks_directory>`                     |
| `hook_safety`                              | blocking | Hook guidance registers only on a non-blocking event, through an inline guard with a floor, a timeout, and a kill switch, runs an idempotent script, and names no pinned cache path. | `references/plugin-hooks.md` `<session_identity>`, `<anti_patterns>` |

</harness_rules>
{!% else %!}
<harness_rules>

| Identifier               | Severity | Rule                                                                                               | Stated in                                                             |
| ------------------------ | -------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `codex_claude_semantics` | blocking | Codex skill content projects no Claude-only frontmatter, hook, or plugin-root behavior onto Codex. | `SKILL.md` `<frontmatter>`, `references/plugin-hooks.md` `<overview>` |

</harness_rules>
{!% endif %!}

<path_boundary_rules>

| Identifier                     | Severity | Rule                                                                                                                        | Stated in                    |
| ------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `fixed_scratch_path`           | blocking | Scratch storage comes from a unique-per-invocation source, never a fixed or root-appended path.                             | `SKILL.md` `<path_boundary>` |
| `scratch_not_removed`          | blocking | Code that creates a scratch directory removes it on every exit path.                                                        | `SKILL.md` `<path_boundary>` |
| `scratch_deletion_instruction` | blocking | No skill directs Claude to delete scratch it created through a shell command.                                               | `SKILL.md` `<path_boundary>` |
| `unconfirmed_external_write`   | blocking | A write outside the invocation checkout is confirmed, naming the absolute destination, before it happens.                   | `SKILL.md` `<path_boundary>` |
| `permission_bypass`            | blocking | No skill frames a permission prompt, sandbox refusal, or tool-layer decline as an obstacle or documents a route around it.  | `SKILL.md` `<path_boundary>` |
| `unbounded_classifier_retry`   | blocking | Only an authorized request's classifier refusal admits one retry, after the retrace, carrying only the correction it found. | `SKILL.md` `<path_boundary>` |

</path_boundary_rules>
