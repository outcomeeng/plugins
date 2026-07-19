<required_reading>

Read `/skill-standards` and `/agent-prompt-standards`. Read `spx/local/skills.md` when the target repository provides it.

</required_reading>

<process>

<step name="resolve_target">

Use the exact skill path supplied by the operator or established from the repository's authored layout. Read the complete target bundle and confirm that the skill is a router or that the requested change justifies converting it to one. Never assume a user-home or runtime-cache destination.

</step>

<step name="define_route">

Name the distinct user intent, trigger phrases, observable output, required references, and success evidence. Reject a route that duplicates an existing workflow or differs only by wording.

</step>

<step name="write_workflow">

Create `workflows/{descriptive-name}.md` by applying `/skill-standards`'s workflow-file schema and XML rules. Load only references required by this route.

</step>

<step name="register_route">

Add the trigger and exact `${CLAUDE_SKILL_DIR}/workflows/{descriptive-name}.md` path to `<routing>`. Add the file and purpose to `<workflows_index>`. Keep common principles in the router and route-specific procedure in the workflow.

</step>

<step name="validate">

Exercise the new trigger and its nearest adjacent trigger. Confirm each selects exactly one intended route, every bundled link resolves, repository checks pass, and a fresh typed `skill-auditor` verdict approves the complete bundle.

</step>

</process>

<success_criteria>

- The new route represents a distinct intent and produces an output named by its success criteria.
- The workflow conforms to `/skill-standards` and loads only required references.
- Routing selects the new workflow for representative input without displacing adjacent routes.
- Repository checks pass and a typed `skill-auditor` verdict approves the complete bundle.

</success_criteria>
