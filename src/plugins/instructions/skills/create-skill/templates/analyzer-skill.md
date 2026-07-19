---
name: "{{skill-name}}"
description: >-
  ALWAYS invoke this skill when analyzing {{triggers}}.
---

<objective>
A {{subject}} analysis report that covers {{scope}} against {{criteria}} in the declared output shape.
</objective>

<quick_start>
{{Include only when an abbreviated analysis remains representative; otherwise remove this section.}}
</quick_start>

<analysis_scope>

<included>

- {{Item 1}}
- {{Item 2}}

</included>

<excluded>

- {{Exclusion 1}}
- {{Exclusion 2}}

</excluded>

</analysis_scope>

<evaluation_criteria>

| Criterion       | Evidence              | Priority rule |
| --------------- | --------------------- | ------------- |
| {{Criterion 1}} | {{Required evidence}} | {{Rule}}      |
| {{Criterion 2}} | {{Required evidence}} | {{Rule}}      |

</evaluation_criteria>

<output_format>

<summary>{{Overall conclusion and scope coverage.}}</summary>
<findings>{{Each finding with evidence, impact, and priority.}}</findings>
<recommendations>{{Include only when the analysis contract requires recommendations; otherwise remove this row.}}</recommendations>
<unresolved>{{Include only when evidence gaps are a declared output; otherwise remove this row.}}</unresolved>

</output_format>

<workflow>

<step name="collect_evidence">{{Read every in-scope source and record coverage.}}</step>
<step name="evaluate">{{Apply each criterion consistently to the evidence.}}</step>
<step name="synthesize">{{Group related findings and prioritize by the declared rule.}}</step>
<step name="render_report">{{Produce the exact output format without unsupported conclusions.}}</step>

</workflow>

<success_criteria>

- Every included scope item is covered or listed as unresolved with the missing evidence.
- Every finding cites evidence and follows the declared priority rule.
- Every included recommendation maps to a valid finding.

</success_criteria>
