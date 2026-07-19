---
name: "{{skill-name}}"
description: >-
  ALWAYS invoke this skill when automating {{trigger conditions}}.
allowed-tools: "{{least-privilege tool list required by this workflow}}"
---

<objective>
A completed {{process}} run that produces {{output}} with deterministic validation and cleanup.
</objective>

<quick_start>
{{Include only when one command performs the complete safe path; otherwise remove this section.}}
</quick_start>

<available_scripts>

| Script                                  | Purpose     | Usage                                                                                          |
| --------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------- |
| `scripts/{{script-name}}.{{extension}}` | {{Purpose}} | `{{interpreter-command}} "${CLAUDE_SKILL_DIR}/scripts/{{script-name}}.{{extension}}" {{args}}` |

</available_scripts>

<dependencies>

- {{Runtime and supported-version contract.}}
- {{Vendored or standard-library dependency boundary.}}
- NEVER install dependencies during normal skill execution.

</dependencies>

<input_output>

| Direction | Format     | Location     | Constraint or validation |
| --------- | ---------- | ------------ | ------------------------ |
| Input     | {{Format}} | {{Location}} | {{Constraint}}           |
| Output    | {{Format}} | {{Location}} | {{Validation}}           |

</input_output>

<error_handling>

| Error       | Detection  | Terminal action                    |
| ----------- | ---------- | ---------------------------------- |
| {{Error 1}} | {{Signal}} | {{Recovery or actionable failure}} |
| {{Error 2}} | {{Signal}} | {{Recovery or actionable failure}} |

</error_handling>

<workflow>

<step name="validate_input">{{Reject invalid input before mutation.}}</step>
<step name="execute">{{Run the declared automation through its bundled path.}}</step>
<step name="validate_output">{{Check the output through the declared deterministic contract.}}</step>
<step name="clean_up">{{Remove invocation-owned temporary state on every exit path.}}</step>

</workflow>

<failure_modes>

{{Include only automation failures observed in actual use, each with what happened, why it failed, and how to avoid it. Remove this section when no observed failure exists.}}

</failure_modes>

<success_criteria>

- Valid input produces the declared output and invalid input fails actionably before mutation.
- Output validation passes.
- Invocation-owned temporary state is absent after success and failure.

</success_criteria>
