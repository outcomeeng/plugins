<contents>

- `<catalog_contract>` — what a rule ID binds and how a finding uses it
- `<structure_rules>` — organization, frontmatter, naming, descriptions, XML structure
- `<disclosure_rules>` — progressive disclosure, conciseness, skill types, reference skills
- `<capability_rules>` — arguments, dynamic context, tool restriction, payload commands, file references
- `<boundary_rules>` — path boundary, scripts, hooks, platform constraints
- `<auditor_rules>` — the auditor skeleton

</contents>

<catalog_contract>

Each row names one rule this skill states and gives it a stable ID. The section column names where the rule is stated; the rule column identifies the rule, and the stated section is its authority. An ID never changes meaning: a rule that changes meaning takes a new ID, and a retired ID is never reused.

A skill-audit finding names exactly one rule ID from this catalog or from the `/agent-prompt-standards` `<rule_catalog>`, carries that rule's severity, and lists every location in the file that breaks the rule. No finding names a rule outside the two catalogs.

</catalog_contract>

<structure_rules>

| Rule ID                           | Severity | Section                | Rule                                                                                                                                                         |
| --------------------------------- | -------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `composition-explicit`            | blocking | `<skill_organization>` | A composing parent grants skill invocation, names the exact skill, owns sequencing and result validation, and invokes nothing speculatively                  |
| `caller-independence`             | blocking | `<skill_organization>` | A skill never names, describes, detects, constrains, refuses, branches on, or depends on its caller or invocation context                                    |
| `composed-dependency-form`        | blocking | `<skill_organization>` | Each dependency is the ``Use skill `{plugin}:{skill}`.`` instruction, and multi-harness source spells no harness's skill-tool name                           |
| `foundation-reference-pattern`    | debt     | `<skill_organization>` | A language-specific skill references its foundational skill and carries only its language-specific implementation                                            |
| `foundation-unqualified-name`     | debt     | `<skill_organization>` | Language-specific prose names a foundational skill by its unqualified invocation name                                                                        |
| `composition-target-reachable`    | blocking | `<skill_organization>` | A composed or reference skill stays callable through the runtime's skill-invocation surface, and no setting blocks that call                                 |
| `frontmatter-valid`               | blocking | `<frontmatter>`        | Frontmatter is well-formed YAML carrying only fields the harness accepts                                                                                     |
| `no-claude-semantics-on-codex`    | blocking | `<frontmatter>`        | Codex frontmatter projects no Claude-only visibility, preload, heartbeat, hook, or invocation semantics, and omits a field with no documented Codex contract |
| `name-matches-directory`          | blocking | `<frontmatter>`        | `name` equals the skill directory name                                                                                                                       |
| `model-effort-forbidden`          | blocking | `<frontmatter>`        | Frontmatter declares no `model` or `effort`                                                                                                                  |
| `invocation-gate-by-role`         | blocking | `<frontmatter>`        | `disable-model-invocation` and `user-invocable` follow the role table, and an automation re-entry target stays user-invocable                                |
| `audit-allowed-tools`             | blocking | `<frontmatter>`        | An `audit-*` skill grants read tools and only the specific Bash verbs its workflow runs, never bare `Bash`                                                   |
| `skills-field-unsupported`        | blocking | `<frontmatter>`        | A SKILL.md carries no `skills:` field                                                                                                                        |
| `description-listing-cap`         | debt     | `<frontmatter>`        | `description` with `when_to_use` stays within the 1,536-character listing cap, with the key trigger first                                                    |
| `name-user-speech`                | debt     | `<naming_conventions>` | The name uses the terms and acronyms users say                                                                                                               |
| `naming-form`                     | debt     | `<naming_conventions>` | Workflow skills use imperative verbs; reference skills use a noun phrase ending in their domain                                                              |
| `vocabulary-precedence`           | debt     | `<naming_conventions>` | Declared methodology vocabulary outranks skill-name grammar                                                                                                  |
| `description-invocation-style`    | blocking | `<descriptions>`       | A description-match entry point is directive; a reference, protocol, or loop body reached by exact name is passive                                           |
| `description-never-disambiguates` | debt     | `<descriptions>`       | A NEVER clause appears only where it disambiguates                                                                                                           |
| `description-user-speech`         | debt     | `<descriptions>`       | Language follows the artifact and the description uses user speech over jargon                                                                               |
| `audit-description-content`       | blocking | `<descriptions>`       | An audit description states its subject, judgment, and criteria, with no routing, dispatch, preload, agent, or context statement                             |
| `audit-model-invocable`           | blocking | `<descriptions>`       | An audit skill stays model-invocable and never sets `disable-model-invocation`                                                                               |
| `description-distinct`            | debt     | `<descriptions>`       | Trigger terms distinguish the skill from adjacent skills                                                                                                     |
| `pure-xml-body`                   | blocking | `<xml_structure>`      | The body carries no markdown heading                                                                                                                         |
| `required-tags`                   | blocking | `<xml_structure>`      | `<objective>` and `<success_criteria>` are present                                                                                                           |
| `success-criteria-properties`     | debt     | `<xml_structure>`      | `<success_criteria>` states the properties that prove the output sound, never a re-list of the workflow steps                                                |
| `router-tags`                     | debt     | `<xml_structure>`      | A router carries its router-pattern tags, and a workflow file carries its workflow-file tags                                                                 |
| `quick-start-omitted`             | debt     | `<xml_structure>`      | A foundation, gate, validator, reference, or auditor skill carries no `<quick_start>`                                                                        |
| `tags-closed`                     | blocking | `<xml_structure>`      | Every opened tag closes                                                                                                                                      |
| `semantic-tag-names`              | debt     | `<xml_structure>`      | Tags carry semantic names, and prose refers to sections by tag name                                                                                          |
| `structure-matches-complexity`    | debt     | `<xml_structure>`      | The tag set matches the skill class row of the intelligence rules                                                                                            |
| `closing-tag-blank-line`          | debt     | `<xml_tag_formatting>` | A closing tag after an unordered list follows a blank line                                                                                                   |

</structure_rules>

<disclosure_rules>

| Rule ID                               | Severity | Section                        | Rule                                                                                                                            |
| ------------------------------------- | -------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `skill-length`                        | debt     | `<progressive_disclosure>`     | SKILL.md stays under 500 lines unless the eager-foundation exception applies                                                    |
| `eager-payload-ceiling`               | blocking | `<eager_foundation_exception>` | A skill using the exception meets its conditions and renders at most 40,000 code points for every target                        |
| `references-one-level`                | debt     | `<progressive_disclosure>`     | References sit one level below SKILL.md and read no further reference                                                           |
| `reference-toc`                       | debt     | `<progressive_disclosure>`     | A reference file over 100 lines opens with a table of contents                                                                  |
| `forward-slash-paths`                 | debt     | `<progressive_disclosure>`     | Every path uses forward slashes                                                                                                 |
| `reference-descriptive-name`          | debt     | `<progressive_disclosure>`     | A reference file name describes its content                                                                                     |
| `reference-exists`                    | blocking | `<progressive_disclosure>`     | Every cited bundled file exists                                                                                                 |
| `reference-cited`                     | debt     | `<progressive_disclosure>`     | Every bundled file is cited by SKILL.md or a workflow file                                                                      |
| `conciseness`                         | debt     | `<conciseness>`                | Every sentence improves the skill's effectiveness, and none restates what the executing runtime already knows                   |
| `concrete-over-abstract`              | debt     | `<conciseness>`                | A requirement names its concrete threshold or command                                                                           |
| `skill-type-shape`                    | debt     | `<skill_types>`                | The skill carries the key sections of its type                                                                                  |
| `reference-skill-frontmatter`         | blocking | `<reference_skills>`           | A reference skill is `user-invocable: false` with a passive description and read-only tools                                     |
| `reference-skill-loaded-explicitly`   | blocking | `<reference_skills>`           | A consumer loads a reference skill through the `Use skill` instruction, never through a bare mention                            |
| `standards-extraction-complete`       | blocking | `<reference_skills>`           | An auditor reads standards only from the standards skill, never from a creator's `references/`                                  |
| `shared-standards-in-reference-skill` | debt     | `<reference_skills>`           | Knowledge two or more skills need lives in one reference skill, never in one skill's `references/` or duplicated across several |

</disclosure_rules>

<capability_rules>

| Rule ID                         | Severity | Section                                                            | Rule                                                                                                                                                       |
| ------------------------------- | -------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `argument-hint-declared`        | debt     | `references/command-capabilities.md` `<arguments>`                 | A skill that takes arguments declares `argument-hint`                                                                                                      |
| `arguments-whole-capture`       | blocking | `references/command-capabilities.md` `<arguments>`                 | Free-form input keeps `$ARGUMENTS` whole-string capture                                                                                                    |
| `arguments-integrated`          | blocking | `references/command-capabilities.md` `<arguments>`                 | Every declared argument is substituted, and every substituted argument is declared                                                                         |
| `empty-arguments-stated`        | debt     | `references/command-capabilities.md` `<arguments>`                 | The skill states what it does when its input is absent                                                                                                     |
| `claude-syntax-in-source`       | debt     | `references/command-capabilities.md` `<overview>`                  | Authored source uses Claude Code's supported syntax, and a Codex difference is fixed in rendering, never by weakening the source                           |
| `dynamic-context-scoped`        | debt     | `references/command-capabilities.md` `<dynamic_context>`           | Each `<context>` command runs on every load, so it injects only state the skill reads, filtered to bounded output, for trigger-time orientation            |
| `allowed-tools-narrowest`       | blocking | `references/command-capabilities.md` `<tool_restriction_security>` | `allowed-tools` grants the narrowest set the task needs, with Bash restricted to specific verbs                                                            |
| `no-unneeded-destructive-tools` | blocking | `references/command-capabilities.md` `<tool_restriction_security>` | No destructive or network tool the task does not need is granted                                                                                           |
| `payload-command-forms`         | blocking | `references/command-capabilities.md` `<payload_commands>`          | A payload-bearing command states its stdin form for each supported harness environment, never a form a caller selects                                      |
| `product-file-reference`        | debt     | `references/command-capabilities.md` `<file_references>`           | A product file is referenced with `@`                                                                                                                      |
| `skill-dir-token`               | blocking | `references/runtime-variables.md` `<skill_file_references>`        | A bundled file is reached through the skill-directory token, never a repository, generated, or legacy plugin path, and source never spells the Codex token |
| `no-token-compatibility-prose`  | debt     | `references/runtime-variables.md` `<skill_file_references>`        | No alias, troubleshooting section, or compatibility-token explanation accompanies the skill-directory token                                                |

</capability_rules>

<boundary_rules>

| Rule ID                      | Severity | Section                                                              | Rule                                                                                                            |
| ---------------------------- | -------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `scratch-unique-source`      | blocking | `<path_boundary>`                                                    | Scratch storage comes from a unique-per-invocation source, never a fixed or appended path                       |
| `scratch-removed-by-creator` | blocking | `<path_boundary>`                                                    | Code that creates a scratch directory removes it on every exit path, including failure                          |
| `scratch-not-deleted`        | blocking | `<path_boundary>`                                                    | No instruction directs Claude to run a deleting command on scratch it created                                   |
| `outside-checkout-confirmed` | blocking | `<path_boundary>`                                                    | A write outside the invocation checkout is confirmed with its absolute destination first                        |
| `no-permission-evasion`      | blocking | `<path_boundary>`                                                    | No content documents a route around a permission prompt, sandbox refusal, or tool-layer decline                 |
| `classifier-retry-bound`     | blocking | `<path_boundary>`                                                    | Only a classifier refusal of an authorized request admits one retrace-bound retry                               |
| `script-validation-messages` | debt     | `references/script-standards.md` `<validation_rule>`                 | A bundled script's errors are verbose, specific, actionable, and deterministic                                  |
| `script-tested`              | blocking | `references/script-standards.md` `<script_testing_rule>`             | A bundled script is tested before inclusion, with its tested inputs recorded                                    |
| `hook-non-blocking-event`    | blocking | `references/plugin-hooks.md` `<overview>`                            | A hook registers only on a non-blocking event                                                                   |
| `hook-inline-guard`          | blocking | `references/plugin-hooks.md` `<anti_patterns>`                       | A hook command carries a clean-exit floor, an explicit timeout, a kill switch, and probed optional dependencies |
| `hook-plugin-root-path`      | blocking | `references/plugin-hooks.md` `<hooks_directory>`                     | A hook reaches plugin files through the plugin-root variable, never a version-pinned cache path                 |
| `hook-layout`                | debt     | `references/plugin-hooks.md` `<hooks_directory>`                     | Hook declarations live in `hooks/hooks.json` at the plugin root, never inside `.claude-plugin/`                 |
| `hook-idempotent`            | blocking | `references/plugin-hooks.md` `<session_identity>`                    | A `SessionStart` hook script is idempotent across startup, resume, clear, and compact                           |
| `hook-cli-delegation`        | debt     | `references/plugin-hooks.md` `<session_identity>`                    | A hook needing richer session state delegates to a probed CLI and never inspects what that CLI wrote            |
| `session-identity-direct`    | debt     | `references/plugin-hooks.md` `<session_identity>`                    | A skill reads the agent-published session identity directly, and no hook synthesizes a second identity          |
| `codex-no-hooks`             | blocking | `references/plugin-hooks.md` `<overview>`                            | Codex output authors no hook, `$CLAUDE_ENV_FILE`, plugin-root, or plugin-data behavior                          |
| `nested-code-fences`         | blocking | `references/platform-constraints.md` `<nested_code_fences>`          | No outer fence nests more than one inner fence                                                                  |
| `bang-expansion-quoting`     | debt     | `references/platform-constraints.md` `<bash_expansion_restrictions>` | A `!` command avoids the forms the bash safety checker rejects                                                  |

</boundary_rules>

<auditor_rules>

| Rule ID                              | Severity | Section                                                     | Rule                                                                                                                                                                    |
| ------------------------------------ | -------- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `auditor-skeleton-sections`          | blocking | `references/auditor-skeleton.md` `<skeleton>`               | An `audit-*` skill carries the skeleton's ordered sections and no `<quick_start>`                                                                                       |
| `auditor-read-only`                  | blocking | `references/auditor-skeleton.md` `<skeleton>`               | An `audit-*` skill changes no subject or product file, produces no fix or commit, and writes only its own run journal                                                   |
| `auditor-verdict-format`             | blocking | `references/auditor-skeleton.md` `<skeleton>`               | `<verdict_format>` carries the full output schema, and a run-recording auditor returns the run token with the unmodified rendered projection, or the blocked diagnostic |
| `auditor-objective-verdict`          | blocking | `references/auditor-skeleton.md` `<objective_examples>`     | The objective names the verdict, never the activity                                                                                                                     |
| `auditor-run-keys`                   | blocking | `references/auditor-skeleton.md` `<run_keys>`               | A run-recording auditor keys each unit by subject and concern and each finding by its unit key and rule ID, never by ordinal                                            |
| `auditor-catalog-rules`              | blocking | `references/auditor-skeleton.md` `<run_keys>`               | Every rule a run-recording auditor records comes from the catalog of the standard it enforces                                                                           |
| `auditor-success-criteria-soundness` | debt     | `references/auditor-skeleton.md` `<success_criteria_shape>` | Success criteria state verdict soundness, never a re-list of steps                                                                                                      |

</auditor_rules>
