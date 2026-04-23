---
name: { { skill-name } }
description: |
  Automate {{process/task}} for {{domain}}.
  Use when users need to {{trigger conditions}}.
---

<objective>
Execute {{process}} reliably and repeatably.
</objective>

<quick_start>

```bash
{{Quick command to run the automation}}
```

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

<available_scripts>

| Script                    | Purpose     | Usage                             |
| ------------------------- | ----------- | --------------------------------- |
| `scripts/{{script-1}}.py` | {{Purpose}} | `python {{script-1}}.py {{args}}` |
| `scripts/{{script-2}}.py` | {{Purpose}} | `python {{script-2}}.py {{args}}` |
| </available_scripts>      |             |                                   |

<dependencies>
**Runtime**:
- Python 3.10+
- {{Package 1}}
- {{Package 2}}

**Installation**:

```bash
pip install {{packages}}
```

</dependencies>

<input_output>
**Input**:

- Format: {{Input format}}
- Location: {{Where to find input}}
- Constraints: {{Any limitations}}

**Output**:

- Format: {{Output format}}
- Location: {{Where output is saved}}
- Validation: {{How to verify}}

</input_output>

<error_handling>

| Error             | Cause     | Recovery       |
| ----------------- | --------- | -------------- |
| {{Error 1}}       | {{Cause}} | {{How to fix}} |
| {{Error 2}}       | {{Cause}} | {{How to fix}} |
| </error_handling> |           |                |

<workflow>
1. **Prepare**: Verify input and dependencies
2. **Execute**: Run the automation script
3. **Validate**: Check output is correct
4. **Clean up**: Remove temporary files

</workflow>

<success_criteria>
Automation is complete when:

- [ ] Script runs without errors
- [ ] Output matches expected format
- [ ] Validation passes
- [ ] No temporary files left behind

</success_criteria>
