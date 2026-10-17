---
name: "{{skill-name}}"
description: >-
  ALWAYS invoke this skill when {{trigger conditions}}.
allowed-tools: "{{least-privilege tool list required by this workflow}}"
---

<objective>
{{The observable output, in one sentence with no actor or activity framing.}}
</objective>

<quick_start>
{{Include only for an on-demand skill with a complete, safe fast path; otherwise remove this section.}}
</quick_start>

<workflow>

<step name="{{first_step_name}}">
{{Specific input, action, and decision boundary.}}
</step>

<step name="{{second_step_name}}">
{{Specific input, action, and decision boundary.}}
</step>

<step name="{{validate_output}}">
{{Exact checks that establish the output.}}
</step>

</workflow>

<success_criteria>

- {{Observable output property.}}
- {{Required validation result.}}
- {{Required failure or boundary behavior.}}

</success_criteria>
