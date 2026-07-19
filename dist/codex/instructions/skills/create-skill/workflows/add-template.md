<required_reading>

Read `/skill-standards` and `/agent-prompt-standards`, including `/skill-standards`'s `references/runtime-variables.md`. Read `spx/local/skills.md` when the target repository provides it. Read every existing template and consuming workflow in the target skill before adding another.

</required_reading>

<process>

<step name="resolve_target">

Use the exact skill path supplied by the operator or established from the repository's authored layout. Never write to a user-home or runtime-cache path.

</step>

<step name="define_template_contract">

Name the artifact the template produces, the workflow that consumes it, the fields that vary, the content that remains invariant, and the validation that proves a rendered instance is usable. Reject a template that duplicates standards or an existing template with renamed placeholders.

</step>

<step name="write_template">

Create `templates/{descriptive-name}.md` under the resolved skill by applying the template and output-shape rules in `/skill-standards` and `/agent-prompt-standards`. Keep placeholders explicit and avoid hidden repository-specific defaults.

</step>

<step name="register_template">

Add the template to the target skill's template index and cite it from every consuming workflow. Use the target skill's runtime directory token for bundled paths and remove any superseded inline scaffold.

</step>

<step name="validate">

Render one representative instance, verify that no unresolved placeholder remains, run the target repository's canonical skill checks, and obtain a fresh typed `skill-auditor` verdict over the complete bundle.

</step>

</process>

<success_criteria>

- The template has one producing artifact and at least one cited consumer.
- Variable placeholders and invariant content are distinguishable, with no repository-specific default hidden in the scaffold.
- A representative render contains no unresolved placeholder and passes its artifact validation.
- Repository checks pass and a typed `skill-auditor` verdict approves the complete bundle.

</success_criteria>
