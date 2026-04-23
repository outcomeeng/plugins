---
name: { { skill-name } }
description: |
  Analyze {{subject}} for {{purpose}}.
  Use when users ask to review, analyze, or extract insights from {{triggers}}.
---

<objective>
Extract actionable insights from {{subject}} by applying systematic analysis.
</objective>

<quick_start>
{{Quick example of running an analysis}}
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

<analysis_scope>
**What to analyze**:

- {{Item 1}}
- {{Item 2}}
- {{Item 3}}

**What to ignore**:

- {{Exclusion 1}}
- {{Exclusion 2}}

</analysis_scope>

<evaluation_criteria>

| Criterion              | Weight | How to Assess |
| ---------------------- | ------ | ------------- |
| {{Criterion 1}}        | {{X%}} | {{Method}}    |
| {{Criterion 2}}        | {{X%}} | {{Method}}    |
| {{Criterion 3}}        | {{X%}} | {{Method}}    |
| </evaluation_criteria> |        |               |

<output_format>

## Analysis Report: {{Subject}}

### Executive Summary

{{1-2 paragraph overview}}

### Key Findings

1. **{{Finding 1}}**: {{Details}}
2. **{{Finding 2}}**: {{Details}}
3. **{{Finding 3}}**: {{Details}}

### Recommendations

- {{Recommendation 1}}
- {{Recommendation 2}}

### Detailed Analysis

{{Section-by-section breakdown}}
</output_format>

<synthesis>
After gathering findings:

1. Combine findings into actionable insights
2. Prioritize by impact
3. Identify patterns across findings
4. Make specific recommendations

</synthesis>

<success_criteria>
Analysis is complete when:

- [ ] All scope items analyzed
- [ ] Criteria applied consistently
- [ ] Report follows output format
- [ ] Recommendations are actionable

</success_criteria>
