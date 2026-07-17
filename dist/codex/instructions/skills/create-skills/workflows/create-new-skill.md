<required_reading>

Read `/skill-standards` and `/agent-prompt-standards` before authoring. Read `spx/local/skills.md` when the target repository provides it. Read the matching template and any authoring references selected below before writing the skill.

</required_reading>

<process>

<step name="resolve_requirements">

Extract the requested capability, target repository or plugin, activation trigger, output, side effects, and constraints from the caller's instruction. Ask only for operator-owned gaps that materially change the skill's behavior or location.

Classify the skill as builder, guide, automation, analyzer, validator, or reference using `/skill-standards`. Determine whether it is reached by description matching, exact-name composition, or an auditor agent preload before writing its description.

</step>

<step name="research_domain">

Research domain concepts, current official guidance, failure modes, security constraints, and ecosystem conventions when the skill's subject requires knowledge unavailable in the repository. Prefer primary documentation. Ask the operator only for proprietary product context that research cannot establish.

</step>

<step name="choose_structure">

Use a single `SKILL.md` for one cohesive workflow whose complete instructions satisfy `/skill-standards`'s progressive-disclosure rule. Use the router pattern when the capability has distinct user intents, conditional workflows, or reusable references.

Select the matching template:

| Skill shape | Template                        |
| ----------- | ------------------------------- |
| Simple      | `templates/simple-skill.md`     |
| Router      | `templates/router-skill.md`     |
| Builder     | `templates/builder-skill.md`    |
| Guide       | `templates/guide-skill.md`      |
| Automation  | `templates/automation-skill.md` |
| Analyzer    | `templates/analyzer-skill.md`   |
| Validator   | `templates/validator-skill.md`  |

</step>

<step name="resolve_target_path">

Write to the exact target path supplied by the caller or established by the repository's plugin layout. Inspect the repository's authored plugin source layout or request the destination. Never assume a runtime-specific home-directory path or a marketplace-specific source directory.

Create only the directories the selected structure needs: `workflows/`, `references/`, `templates/`, or `scripts/`.

</step>

<step name="author_skill">

Write YAML frontmatter and the required `<objective>` and `<success_criteria>` sections. A non-router procedure uses `<workflow>` in `SKILL.md`; a router uses `<essential_principles>`, `<intake>`, `<routing>`, `<reference_index>`, and `<workflows_index>` as applicable.

Add `<quick_start>` only when `/skill-standards` permits an abbreviated on-demand path. Foundation, gate, validator, reference, and auditor skills omit it.

Use `<context>` for runtime inputs the workflow actually consumes. Keep domain detail in cited references one level below `SKILL.md`, and keep each workflow self-contained without nested reference chains.

When adding scripts, follow `/skill-standards`'s script rules, use the repository's required implementation language, and test every script with success and failure inputs before inclusion.

</step>

<step name="validate">

Run the bundled structural validator:

```bash
python3 "${SKILL_DIR}/scripts/quick_validate.py" <skill-path>
```

Identify the target repository's canonical skill build and deterministic-check commands and return them to the caller's repository workflow. Continue after that workflow reports success. When the runtime exposes the `skill-auditor` role, dispatch it over the complete skill bundle. Otherwise invoke `/audit-skills` over that bundle. Repair every must-fix item from the resulting verdict before publication.

</step>

</process>

<success_criteria>

- The skill lives at the repository-resolved authored source path and renders for every supported runtime.
- Frontmatter matches the invocation path, and the body has valid pure-XML structure with output-shaped `<objective>` and `<success_criteria>` sections.
- The selected structure follows the canonical progressive-disclosure rule, with every bundled file cited and no nested or orphaned references.
- Tool permissions, arguments, dynamic context, and bundled paths match the runtime capability contract.
- Bundled scripts pass their success and failure tests, repository checks pass, and the exposed typed audit or `/audit-skills` fallback is APPROVED.

</success_criteria>
