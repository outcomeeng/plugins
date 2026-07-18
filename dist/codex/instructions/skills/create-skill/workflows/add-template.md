<required_reading>

Read `/skill-standards` and `/agent-prompt-standards`. Read `spx/local/skills.md` when the target repository provides it. Read every existing template and consuming workflow in the target skill before adding another.

</required_reading>

<process>

<step name="resolve_target">

Use the exact skill path supplied by the operator or established from the repository's authored layout. Never write to a user-home or runtime-cache path.

</step>

<step name="define_template_contract">

Name the artifact the template produces, the workflow that consumes it, the fields that vary, the content that remains invariant, and the validation that proves a rendered instance is usable. Reject a template that duplicates standards or an existing template with renamed placeholders.

</step>

<gate name="pre_write">

STOP before creating the template unless its exact target path, produced artifact, consuming workflows, variable fields, invariant content, and representative render validation are resolved.

</gate>

<step name="write_template">

Create `templates/{descriptive-name}.md` under the resolved skill. Use semantic XML for a skill or prompt template, with output-shaped `<objective>` and `<success_criteria>` sections when the rendered artifact is a `SKILL.md`. Keep placeholders explicit and avoid hidden repository-specific defaults.

</step>

<gate name="post_write">

STOP before registration unless a representative render contains no unintended placeholder, its required XML structure is valid, and every repository-specific value is an explicit input rather than a hidden default.

</gate>

<step name="register_template">

Add the template to the target skill's template index and cite it from every consuming workflow. Use the target skill's runtime directory token for bundled paths and remove any superseded inline scaffold.

</step>

<step name="validate">

Render one representative instance, verify that no unresolved placeholder remains, run the target repository's canonical skill checks, and obtain a fresh skill audit over the complete bundle.

</step>

</process>

<success_criteria>

- The template has one producing artifact and at least one cited consumer.
- Variable placeholders and invariant content are distinguishable, with no repository-specific default hidden in the scaffold.
- A representative render contains no unresolved placeholder and passes its artifact validation.
- Repository checks pass and an independent skill audit approves the complete bundle.

</success_criteria>
