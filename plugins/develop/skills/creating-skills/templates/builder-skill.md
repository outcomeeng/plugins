---
name: { { skill-name } }
description: |
  Create {{artifacts}} for {{domain}}.
  Use when users ask to build {{triggers}}.
---

<objective>
Create production-quality {{artifacts}} that follow {{domain}} best practices.
</objective>

<quick_start>
{{Minimal example of creating the artifact}}
</quick_start>

<before_implementation>
Gather context to ensure successful implementation:

| Source                   | Gather                                    |
| ------------------------ | ----------------------------------------- |
| **Codebase**             | Existing structure, patterns, conventions |
| **Conversation**         | User's specific requirements, constraints |
| **Skill References**     | Domain patterns from `references/`        |
| **User Guidelines**      | Project-specific conventions              |
| </before_implementation> |                                           |

<required_clarifications>
Ask about USER'S context (not domain knowledge):

1. **Data shape**: "What structure will input have?"
2. **Output type**: "What artifact to create?"
3. **Constraints**: "Any specific requirements?"

</required_clarifications>

<output_specification>
{{Define what the artifact looks like}}

**Structure**:

```
{{artifact structure}}
```

**Example**:

```
{{example artifact}}
```

</output_specification>

<domain_standards>

### Must Follow

- [ ] {{Standard 1}}
- [ ] {{Standard 2}}
- [ ] {{Standard 3}}

### Must Avoid

- {{Anti-pattern 1}}
- {{Anti-pattern 2}}

</domain_standards>

<output_checklist>
Before delivering, verify:

- [ ] Artifact meets requirements
- [ ] Follows domain standards
- [ ] No anti-patterns present
- [ ] Tested/validated

</output_checklist>

<success_criteria>
Builder task is complete when:

- [ ] Artifact created successfully
- [ ] All standards followed
- [ ] User requirements met

</success_criteria>
