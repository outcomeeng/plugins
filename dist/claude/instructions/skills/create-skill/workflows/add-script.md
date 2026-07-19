<required_reading>

Read `/skill-standards` and `/agent-prompt-standards`, including `/skill-standards`'s `references/runtime-variables.md` and the script-standards reference named by `<script_standards>`. Read `${CLAUDE_SKILL_DIR}/references/technical-patterns.md` for executable-automation security, dependencies, failure handling, side effects, and cleanup. Read `spx/local/skills.md` when the target repository provides it. Load the target repository's implementation and test skills for the selected script language before writing code or tests.

</required_reading>

<process>

<step name="resolve_target">

Use the exact skill path supplied by the operator or established from the repository's authored layout. Determine the target repository's required shipped-script language, supported runtime window, dependency boundary, and test command. Never assume Python or a marketplace-specific source path.

</step>

<step name="define_contract">

Specify arguments, input format, output format, exit statuses, side effects, resource ceilings, cleanup ownership, and actionable validation failures. Confirm that executable code is necessary; keep a purely procedural operation in the workflow when a script adds no deterministic capability.

</step>

<step name="author_and_test">

Create `scripts/{descriptive-name}.{extension}` through the target language's implementation workflow. Add tests through its test workflow for valid input, invalid input, missing resources, deterministic output, and cleanup on success and failure. Never retain an untested placeholder script.

</step>

<step name="register_script">

Cite the script from each consuming workflow through the target skill's runtime directory token. Document its complete invocation, arguments, outputs, terminal failures, and tested success and failure cases. Grant only the tool capability required to invoke it.

</step>

<step name="validate">

Run the script tests and the target repository's canonical skill build and deterministic checks, then obtain a fresh typed `skill-auditor` verdict over the complete bundle. Remove the script when it cannot meet the declared test or portability contract.

</step>

</process>

<success_criteria>

- The script provides a deterministic capability that workflow prose alone cannot supply.
- Its invocation, inputs, outputs, exit statuses, side effects, ceilings, and cleanup owner are explicit.
- Success, failure, and cleanup tests pass through the target repository's declared test workflow.
- Every bundled citation resolves, repository checks pass, and a typed `skill-auditor` verdict approves the complete bundle.

</success_criteria>
