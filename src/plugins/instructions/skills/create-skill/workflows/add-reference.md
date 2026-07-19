<required_reading>

Read `/skill-standards` and `/agent-prompt-standards`, including `/skill-standards`'s `references/runtime-variables.md`. Read `spx/local/skills.md` when the target repository provides it.

</required_reading>

<process>

<step name="resolve_target">

Use the exact skill path supplied by the operator or established from the repository's authored layout. Read its `SKILL.md`, existing `references/`, and every workflow that may consume the new reference. Never assume a user-home or runtime-cache destination.

</step>

<step name="classify_content">

Name the reference's purpose, owning workflows, required load condition, and source of truth. Keep shared standards in a `{domain}-standards` reference skill; use the target skill's `references/` only for workflow-specific domain knowledge.

Choose one source:

- Primary documentation or repository truth researched for the task.
- Operator-provided content.
- Domain knowledge extracted from the target `SKILL.md` to improve progressive disclosure.

</step>

<step name="write_reference">

Create `references/{descriptive-name}.md` under the resolved target skill by applying `/skill-standards`'s reference-file and XML rules. Include only knowledge the consuming workflow needs, and keep any examples inside the section that owns them.

</step>

<step name="register_reference">

Add the file to the target skill's `<reference_index>`. Add it to `<required_reading>` only in workflows that require it. Cite the path exactly once per consuming surface and remove any duplicated content the extraction supersedes.

</step>

<step name="validate">

Run the target repository's canonical skill build and deterministic checks. Confirm the file exists, every citation resolves, no bundled file is orphaned, the body passes the reference-file checks in `/skill-standards`, and a fresh typed `skill-auditor` verdict approves the complete bundle.

</step>

</process>

<success_criteria>

- The reference lives under the resolved authored skill path and has one documented purpose.
- Every required consumer cites it, every citation resolves, and no unrelated workflow loads it.
- Shared standards remain in their owning reference skill, with no duplicated rule catalog in the new file.
- Repository checks pass and a typed `skill-auditor` verdict approves the complete bundle.

</success_criteria>
