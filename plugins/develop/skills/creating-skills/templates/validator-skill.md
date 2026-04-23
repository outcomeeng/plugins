---
name: { { skill-name } }
description: |
  Validate {{subject}} for {{compliance/quality}}.
  Use when users ask to check, audit, or verify {{triggers}}.
---

<objective>
Enforce quality standards by systematically validating {{subject}} against defined criteria.
</objective>

<quick_start>
{{Quick example of running a validation}}
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

<quality_criteria>

| Criterion           | Weight | Pass Threshold |
| ------------------- | ------ | -------------- |
| {{Criterion 1}}     | {{X%}} | {{Threshold}}  |
| {{Criterion 2}}     | {{X%}} | {{Threshold}}  |
| {{Criterion 3}}     | {{X%}} | {{Threshold}}  |
| </quality_criteria> |        |                |

<scoring_rubric>
**3 (Excellent)**: {{Definition}}

**2 (Good)**: {{Definition}}

**1 (Needs Work)**: {{Definition}}

**0 (Fail)**: {{Definition}}
</scoring_rubric>

<thresholds>
| Result | Score Range | Action |
|--------|-------------|--------|
| **Pass** | ≥ {{X}} | Approved, no changes needed |
| **Conditional** | {{X}} - {{Y}} | Approved with noted improvements |
| **Fail** | < {{Y}} | Blocked, must fix issues |
</thresholds>

<remediation>
| Issue | Severity | Fix |
|-------|----------|-----|
| {{Issue 1}} | {{High/Medium/Low}} | {{How to fix}} |
| {{Issue 2}} | {{High/Medium/Low}} | {{How to fix}} |
</remediation>

<validation_report>

## Validation Report: {{Subject}}

### Summary

- **Status**: {{Pass/Conditional/Fail}}
- **Score**: {{X}}/{{Total}}
- **Date**: {{YYYY-MM-DD}}

### Results by Criterion

| Criterion       | Score   | Notes     |
| --------------- | ------- | --------- |
| {{Criterion 1}} | {{X}}/3 | {{Notes}} |
| {{Criterion 2}} | {{X}}/3 | {{Notes}} |

### Issues Found

1. **{{Issue}}**: {{Description}}
   → Fix: {{Remediation}}

### Recommendation

{{Overall recommendation}}
</validation_report>

<success_criteria>
Validation is complete when:

- [ ] All criteria evaluated
- [ ] Scores assigned per rubric
- [ ] Report generated
- [ ] Remediation guidance provided (if needed)

</success_criteria>
