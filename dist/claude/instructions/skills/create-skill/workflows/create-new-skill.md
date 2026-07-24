<required_reading>

Read `/skill-standards` and `/agent-prompt-standards` before authoring. Read `spx/local/skills.md` when the target repository provides it. Read the matching template and any authoring references selected below before writing the skill.

</required_reading>

<process>

<step name="resolve_requirements">

Extract the requested capability, target repository or plugin, activation trigger, observable output, side effects, and constraints from the operator's instruction. Ask only for operator-owned gaps that materially change the skill's behavior or location.

Classify the skill as builder, guide, automation, analyzer, validator, or reference using `/skill-standards`. Treat an `audit-*` skill as a validator-family auditor that requires the canonical auditor structure. Determine whether description matching, exact-name composition, or an auditor preload reaches it before writing its description. Confirm the output the `<objective>` will name and the evidence the `<success_criteria>` will require.

</step>

<step name="complete_name_review">

Complete the router's `<material_change_name_review>` before writing the new skill. Use the proposed name only when its classification conforms to the governing naming form and declared methodology vocabulary.

</step>

<step name="research_domain">

Research domain concepts, current official guidance, observed failure modes, security constraints, and ecosystem conventions when the skill's subject requires knowledge unavailable in the repository. Prefer primary documentation. Ask the operator only for proprietary product context that research cannot establish.

</step>

<step name="select_authoring_references">

Load `${CLAUDE_SKILL_DIR}/references/reusability-patterns.md` when the capability must support variable requests or tool choices. Load `${CLAUDE_SKILL_DIR}/references/technical-patterns.md` when the skill handles files, data, external services, state mutation, or executable automation. Load `${CLAUDE_SKILL_DIR}/references/test-patterns.md` when creating behavior or materially changing activation, routing, output, or failure handling. Skip a reference only when its load condition does not apply.

For an `audit-*` skill, read `/skill-standards`'s `references/auditor-skeleton.md` before choosing sections or writing the verdict contract. Before writing any skill-bundled file reference, read `/skill-standards`'s `references/runtime-variables.md`. Before authoring a bundled script, read `/skill-standards`'s `references/script-standards.md`.

</step>

<step name="choose_structure">

Use a single `SKILL.md` for one cohesive workflow whose complete instructions satisfy `/skill-standards`'s progressive-disclosure rule. Use the router pattern when the capability has distinct user intents, conditional workflows, or reusable references.

Select the matching template:

| Skill shape | Template                                            |
| ----------- | --------------------------------------------------- |
| Simple      | `${CLAUDE_SKILL_DIR}/templates/simple-skill.md`     |
| Router      | `${CLAUDE_SKILL_DIR}/templates/router-skill.md`     |
| Builder     | `${CLAUDE_SKILL_DIR}/templates/builder-skill.md`    |
| Guide       | `${CLAUDE_SKILL_DIR}/templates/guide-skill.md`      |
| Automation  | `${CLAUDE_SKILL_DIR}/templates/automation-skill.md` |
| Analyzer    | `${CLAUDE_SKILL_DIR}/templates/analyzer-skill.md`   |
| Auditor     | `${CLAUDE_SKILL_DIR}/templates/auditor-skill.md`    |
| Validator   | `${CLAUDE_SKILL_DIR}/templates/validator-skill.md`  |
| Reference   | `${CLAUDE_SKILL_DIR}/templates/reference-skill.md`  |

</step>

<step name="resolve_target_path">

Write to the exact target path supplied by the operator or established by the repository's authored plugin layout. Inspect that layout when the destination is absent. Never assume a runtime-specific home directory or a marketplace-specific source path.

Create only the directories the selected structure needs: `workflows/`, `references/`, `templates/`, `assets/`, or `scripts/`.

</step>

<step name="author_skill">

Instantiate the selected template with the resolved requirements. Apply `/skill-standards` `<frontmatter>`, `<xml_structure>`, `<progressive_disclosure>`, `<templates_and_variables>`, and `<script_standards>` directly; do not reproduce those rules in this workflow. Route bundled-script implementation and testing through the target repository's required language workflows.

</step>

<step name="validate">

Run the target repository's canonical skill build and deterministic checks. Dispatch the typed `skill-auditor` over the complete skill bundle. If the role is unavailable or returns no complete structured verdict, return `BLOCKED`; never substitute an in-context `/audit-skill` invocation. Repair every must-fix finding before publication. When the target repository declares no deterministic skill check, apply the closest available validation surface to every applicable `/skill-standards` and `/agent-prompt-standards` check before dispatching the audit.

</step>

<step name="exercise">

Invoke the skill against representative input. Confirm that it selects the intended workflow, loads only the required references, produces the objective's output shape, and satisfies each success criterion. Iterate on observed failures.

</step>

</process>

<success_criteria>

- The skill lives at the repository-resolved authored source path and renders for every supported runtime.
- Frontmatter and body conform to the selected type, template, and applicable `/skill-standards` sections.
- Every reviewed plugin skill has a naming-classification row, with only proven violations or explicit operator-directed names changed.
- The complete bundle passes `/skill-standards` progressive-disclosure and reference-integrity checks.
- The complete bundle passes `/skill-standards` command-capability checks.
- Any bundled scripts pass success and failure tests, repository checks pass, and the typed `skill-auditor` verdict is `APPROVED`.

</success_criteria>
