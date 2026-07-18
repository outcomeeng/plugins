---
name: "{{skill-name}}"
description: >-
  ALWAYS invoke this skill when building {{triggers}}.
---

<objective>
{{Artifact}} that satisfies {{domain contract}} and the resolved requirements.
</objective>

<quick_start>
{{Include only when a complete, safe minimal artifact path exists; otherwise remove this section.}}
</quick_start>

<required_clarifications>

Ask only for unresolved operator-owned choices:

| Choice       | Why it changes the artifact |
| ------------ | --------------------------- |
| {{Choice 1}} | {{Impact}}                  |
| {{Choice 2}} | {{Impact}}                  |

</required_clarifications>

<output_specification>

| Property   | Required shape             |
| ---------- | -------------------------- |
| Location   | {{Resolved authored path}} |
| Structure  | {{Artifact structure}}     |
| Interfaces | {{Observable contracts}}   |
| Validation | {{Exact command or check}} |

</output_specification>

<domain_standards>

<required>

- {{Domain rule 1.}}
- {{Domain rule 2.}}

</required>

<prohibited>

- {{Domain anti-pattern 1.}}
- {{Domain anti-pattern 2.}}

</prohibited>

</domain_standards>

<workflow>

<step name="resolve_requirements">{{Resolve only choices repository truth cannot decide.}}</step>
<step name="create_artifact">{{Create the artifact at the resolved path from the output specification.}}</step>
<step name="validate_artifact">{{Run the exact validation and repair every failure.}}</step>

</workflow>

<success_criteria>

- The artifact exists at the resolved path and matches the output specification.
- Every required domain rule holds and every prohibited pattern is absent.
- The declared validation passes.

</success_criteria>
