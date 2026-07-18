---
name: "{{skill-name}}"
description: >-
  ALWAYS invoke this skill when following {{trigger conditions}}.
---

<objective>
A completed {{procedure}} with {{observable result}} and reproducible verification.
</objective>

<quick_start>
{{Include only when the abbreviated path remains complete and safe; otherwise remove this section.}}
</quick_start>

<workflow>

<step name="{{first_step_name}}">
{{Inputs, procedure, and expected intermediate result.}}
</step>

<step name="{{second_step_name}}">
{{Inputs, procedure, and expected intermediate result.}}
</step>

<step name="{{verify_result}}">
{{Exact verification and failure handling.}}
</step>

</workflow>

<examples>

<example name="{{scenario_one}}">
<input>{{Input description.}}</input>
<output>{{Expected output.}}</output>
</example>

<example name="{{scenario_two}}">
<input>{{Input description.}}</input>
<output>{{Expected output.}}</output>
</example>

</examples>

<official_documentation>

{{Include only when current external documentation governs the procedure; otherwise remove this section.}}

| Resource       | URL     | Governing use |
| -------------- | ------- | ------------- |
| {{Resource 1}} | {{URL}} | {{Purpose}}   |
| {{Resource 2}} | {{URL}} | {{Purpose}}   |

</official_documentation>

<success_criteria>

- Every required step reaches its expected intermediate result.
- The final output matches the declared shape.
- The exact verification passes or reports an actionable terminal failure.

</success_criteria>
