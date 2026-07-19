---
name: "{{skill-name}}"
description: >-
  ALWAYS invoke this skill when {{trigger conditions}}.
allowed-tools: "{{least-privilege tool list required by this workflow}}"
---

<objective>
A {{request type}} routed to the one workflow that produces {{observable output family}}.
</objective>

<essential_principles>

- {{Principle that applies to every route.}}
- {{Cross-route safety or authority boundary.}}
- {{Cross-route validation requirement.}}

</essential_principles>

<intake>
What would you like to do?

1. {{First option}}
2. {{Second option}}
3. {{Third option}}

**Wait for the response before proceeding.**
</intake>

<routing>

| Response          | Workflow                                        |
| ----------------- | ----------------------------------------------- |
| 1, "{{keywords}}" | `${SKILL_DIR}/workflows/{{first-workflow}}.md`  |
| 2, "{{keywords}}" | `${SKILL_DIR}/workflows/{{second-workflow}}.md` |
| 3, "{{keywords}}" | `${SKILL_DIR}/workflows/{{third-workflow}}.md`  |

</routing>

<reference_index>

| File                 | Purpose                         |
| -------------------- | ------------------------------- |
| `{{reference-1}}.md` | {{Load condition and purpose.}} |
| `{{reference-2}}.md` | {{Load condition and purpose.}} |

</reference_index>

<workflows_index>

| Workflow            | Purpose                         |
| ------------------- | ------------------------------- |
| `{{workflow-1}}.md` | {{Distinct intent and output.}} |
| `{{workflow-2}}.md` | {{Distinct intent and output.}} |
| `{{workflow-3}}.md` | {{Distinct intent and output.}} |

</workflows_index>

<success_criteria>

- Representative input selects exactly one intended route.
- Every routed workflow exists and produces its declared output.
- Every bundled reference is cited by a consumer and loads only when required.

</success_criteria>
