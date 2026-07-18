<required_reading>

Read `/skill-standards` and `/agent-prompt-standards` before authoring. Read `spx/local/skills.md` when the target repository provides it. Read the matching template and any authoring references selected below before writing the skill.

</required_reading>

<process>

<step name="resolve_requirements">

Extract the requested capability, target repository or plugin, activation trigger, observable output, side effects, and constraints from the operator's instruction. Ask only for operator-owned gaps that materially change the skill's behavior or location.

Classify the skill as builder, guide, automation, analyzer, validator, or reference using `/skill-standards`. Determine whether description matching, exact-name composition, or an auditor preload reaches it before writing its description. Confirm the output the `<objective>` will name and the evidence the `<success_criteria>` will require.

</step>

<step name="classify_name">

Apply `/skill-standards` `<naming_conventions>` and the repository's skill-authoring overlay. When the target plugin already contains skills and repository policy requires plugin-wide naming review, produce this matrix before writing or renaming any skill:

| Current name | Skill type | Governing naming form | Proposed name or keep | Reason |
| ------------ | ---------- | --------------------- | --------------------- | ------ |

Read the source that declares any overlapping methodology vocabulary and inspect relevant file history before classifying a name as defective. Never infer a batch rename from a shared lexical token, suffix, or grammatical number.

</step>

<step name="research_domain">

Research domain concepts, current official guidance, observed failure modes, security constraints, and ecosystem conventions when the skill's subject requires knowledge unavailable in the repository. Prefer primary documentation. Ask the operator only for proprietary product context that research cannot establish.

</step>

<step name="select_authoring_references">

Load `${CLAUDE_SKILL_DIR}/references/reusability-patterns.md` when the capability must support variable requests or tool choices. Load `${CLAUDE_SKILL_DIR}/references/technical-patterns.md` when the skill handles files, data, external services, state mutation, or executable automation. Load `${CLAUDE_SKILL_DIR}/references/test-patterns.md` when creating behavior or materially changing activation, routing, output, or failure handling. Skip a reference only when its load condition does not apply.

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
| Validator   | `${CLAUDE_SKILL_DIR}/templates/validator-skill.md`  |

</step>

<step name="resolve_target_path">

Write to the exact target path supplied by the operator or established by the repository's authored plugin layout. Inspect that layout when the destination is absent. Never assume a runtime-specific home directory or a marketplace-specific source path.

Create only the directories the selected structure needs: `workflows/`, `references/`, `templates/`, `assets/`, or `scripts/`.

</step>

<gate name="pre_write">

STOP before creating files unless the skill type, classified name, exact authored target path, selected template, required references, side-effect boundary, and success evidence are resolved. Confirm every selected bundled path exists and every operator-owned choice that changes the artifact is settled.

</gate>

<step name="author_skill">

Write YAML frontmatter and the required `<objective>` and `<success_criteria>` sections. A non-router procedure uses `<workflow>` in `SKILL.md`; a router adds the router tags required by `/skill-standards`. Files under `workflows/` use `<required_reading>`, `<process>`, and `<success_criteria>`.

Add `<quick_start>` only when `/skill-standards` permits an abbreviated on-demand path. Foundation, gate, validator, reference, and auditor skills omit it. Add `<context>` only for state-dependent inputs consumed on every load; ordinary intake and repository reading belong in the workflow.

Keep domain detail in cited references one level below `SKILL.md`, without nested reference chains. When adding scripts, follow `/skill-standards`'s script rules, use the target repository's required implementation language, and test success and failure inputs before inclusion.

</step>

<gate name="post_write">

STOP before repository-wide validation unless frontmatter parses, the directory and `name` agree, XML tags close, every routing and bundled-file citation resolves, no template placeholder remains unintentionally, and every newly bundled script's focused success and failure tests pass. Repair the phase that introduced any failure before continuing.

</gate>

<step name="validate">

Run the target repository's canonical skill build and deterministic checks. When the runtime exposes `skill-auditor`, dispatch it over the complete skill bundle; otherwise invoke `/audit-skills` over that bundle. Repair every must-fix finding before publication. When the target repository declares no deterministic skill check, verify frontmatter parsing, XML tag closure, bundled-link resolution, and directory/name agreement with its available validation surface before dispatching the audit.

</step>

<step name="exercise">

Invoke the skill against representative input. Confirm that it selects the intended workflow, loads only the required references, produces the objective's output shape, and satisfies each success criterion. Iterate on observed failures.

</step>

</process>

<success_criteria>

- The skill lives at the repository-resolved authored source path and renders for every supported runtime.
- Frontmatter matches the classified invocation path, and the body has valid pure-XML structure with output-shaped `<objective>` and `<success_criteria>` sections.
- Every reviewed plugin skill has a naming-classification row, with only proven violations or explicit operator-directed names changed.
- The selected structure follows the canonical progressive-disclosure rule, with every bundled file cited and no nested or orphaned references.
- Tool permissions, arguments, dynamic context, and bundled paths match the runtime capability contract.
- Any bundled scripts pass success and failure tests, repository checks pass, and the typed audit or `/audit-skills` fallback is `APPROVED`.

</success_criteria>
