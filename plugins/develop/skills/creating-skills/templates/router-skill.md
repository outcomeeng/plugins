---
name: { { skill-name } }
description: |
  {{What this skill does}}.
  Use when {{trigger conditions}}.
---

<essential_principles>
{{Principles that ALWAYS apply, regardless of which workflow runs}}

**Principle 1**: {{Explanation}}

**Principle 2**: {{Explanation}}

**Principle 3**: {{Explanation}}
</essential_principles>

<intake>
What would you like to do?

1. {{First option}}
2. {{Second option}}
3. {{Third option}}

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Workflow |
|----------|----------|
| 1, "{{keywords}}" | `workflows/{{first-workflow}}.md` |
| 2, "{{keywords}}" | `workflows/{{second-workflow}}.md` |
| 3, "{{keywords}}" | `workflows/{{third-workflow}}.md` |

**After reading the workflow, follow it exactly.**
</routing>

<quick_reference>
{{Brief reference information always useful to have visible}}
</quick_reference>

<reference_index>
All in `references/`:

| File               | Purpose     |
| ------------------ | ----------- |
| {{reference-1}}.md | {{Purpose}} |
| {{reference-2}}.md | {{Purpose}} |
| </reference_index> |             |

<workflows_index>
All in `workflows/`:

| Workflow           | Purpose     |
| ------------------ | ----------- |
| {{workflow-1}}.md  | {{Purpose}} |
| {{workflow-2}}.md  | {{Purpose}} |
| </workflows_index> |             |

<success_criteria>
A well-executed {{skill name}}:

- [ ] {{First criterion}}
- [ ] {{Second criterion}}
- [ ] {{Third criterion}}

</success_criteria>
