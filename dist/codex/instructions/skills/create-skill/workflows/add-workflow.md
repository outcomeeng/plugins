<required_reading>

Read `/skill-standards`' `references/runtime-variables.md`. Read `${SKILL_DIR}/references/test-patterns.md` for activation, routing, and fresh-context validation. Read `${SKILL_DIR}/references/reusability-patterns.md` when the new route introduces variable request shapes or tool choices.

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

Add the trigger and exact `${SKILL_DIR}/workflows/{descriptive-name}.md` path to `<routing>`. Add the file and purpose to `<workflows_index>`. Keep common principles in the router and route-specific procedure in the workflow.

</step>

<step name="validate">

Exercise the new trigger and its nearest adjacent trigger. Confirm each selects exactly one intended route, every bundled link resolves, repository checks pass, and every catalog rule holds for each changed file; return the bundle ready for independent verification.

</step>

</process>

<success_criteria>

- The new route represents a distinct intent and produces an output named by its success criteria.
- The workflow conforms to `/skill-standards` and loads only required references.
- Routing selects the new workflow for representative input without displacing adjacent routes.
- Repository checks pass, every catalog rule holds for each changed file, and the bundle returns ready for independent verification.

</success_criteria>
