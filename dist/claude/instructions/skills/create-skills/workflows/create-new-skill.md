<required_reading>
Read `/skill-standards` and `/agent-prompt-standards` before running this workflow. Check for `spx/local/skills.md` at the repository root and read it when present.
</required_reading>

<process>

<step name="gather_requirements">

Infer the skill's domain, requested output, invocation triggers, and constraints from the operator's request. Ask only for operator-owned gaps that materially change the result.

Classify the skill as Builder, Guide, Automation, Analyzer, Validator, or Reference. Confirm the observable output the `<objective>` will name and the evidence the `<success_criteria>` will require.

</step>

<step name="discover_domain">

Research domain knowledge that cannot be inferred safely. Prefer current primary documentation, then official library documentation and source repositories. Cover core concepts, recommended practices, concrete failure modes, security boundaries, and relevant ecosystem constraints. Ask the operator only for proprietary or product-specific information unavailable from those sources.

</step>

<step name="choose_structure">

Use one `SKILL.md` for a single workflow whose complete effective prompt remains concise. Use the router pattern when the skill serves multiple user intents or conditionally loads substantial workflows or domain references.

Keep essential principles and every rule required on all invocations inline. Move conditional detail into descriptively named one-level `references/` or `workflows/` files. Apply the eager-foundation exception only when every inlined reference would otherwise load on every fresh invocation and all exception conditions in `/skill-standards` hold.

</step>

<step name="create_structure">

Create the skill directory with `scripts/`, `references/`, `workflows/`, `templates/`, or `assets/` only when the selected design needs them. Start from the matching template bundled with `/create-skills`.

</step>

<step name="write_skill">

Every `SKILL.md` includes valid YAML frontmatter, `<objective>`, and `<success_criteria>`.

For a simple or medium skill:

- Use `<workflow>` for sequential instructions.
- Add `<quick_start>` only for an on-demand tool with a meaningful fast path.
- Omit `<quick_start>` for foundation, gate, validator, reference, and agent-preloaded auditor skills.

For a router skill, add the router tags required by `/skill-standards` on top of the mandatory tags: `<essential_principles>`, `<intake>`, `<routing>`, `<reference_index>`, and `<workflows_index>`.

Files under `workflows/` use `<required_reading>`, `<process>`, and `<success_criteria>`. Reserve `<process>` for those workflow files; a `SKILL.md` uses `<workflow>`.

</step>

<step name="write_domain_content">

Write only domain-specific knowledge that changes execution quality. Put reusable conditional knowledge in `references/`; keep failure modes concrete and based on observed failures. Automation skills place tested, portable implementations in `scripts/`; builders place reusable artifact material in `templates/` or `assets/`.

Add a `<context>` block only when the skill needs state-dependent context on every load. Keep every injected command bounded and directly consumed by the skill. Put ordinary intake and repository-reading instructions in `<workflow>` rather than creating a markdown "Before Implementation" section.

</step>

<step name="validate">

Run:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/quick_validate.py" {skill-path}
```

Verify:

- frontmatter is valid and the name matches the directory;
- the description matches the invocation path;
- `<objective>` and `<success_criteria>` are present;
- the body uses pure XML structure with closed tags;
- conditional tags match the skill type;
- every declared argument is consumed and carries an `argument-hint`;
- every bundled reference exists, is cited, and uses a portable path;
- `SKILL.md` stays under 500 lines unless the eager-foundation exception applies.

</step>

<step name="exercise">

Invoke the skill against representative input. Confirm that it selects the intended workflow, loads only the required references, produces the objective's output shape, and satisfies each success criterion. Iterate on observed failures rather than hypothetical ones.

</step>

</process>

<success_criteria>

- The skill's frontmatter, XML structure, arguments, tools, and bundled-file references pass the current validation rules.
- The skill contains the mandatory `<objective>` and `<success_criteria>` tags, with conditional tags selected by skill type.
- Conditional detail loads only from cited one-level files; eager foundation content satisfies every exception condition when used.
- A representative invocation reaches the intended workflow and produces output that satisfies the stated success criteria.

</success_criteria>
