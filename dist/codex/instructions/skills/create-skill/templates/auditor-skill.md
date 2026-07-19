---
name: "audit-{{subject}}"
description: >-
  {{Subject}} audit methodology — judges {{target}} against {{governing standards}}.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

<objective>
An `APPROVED` or `REJECTED` verdict on {{scope}} against {{governing standards}}, with findings grouped as {{category one}}, {{category two}}, and {{category three}}; every rejected finding names the artifact location, violated rule, and evidence.
</objective>

<constraints>

- NEVER modify files, commit changes, or replace the subject under audit.
- ALWAYS inspect every applicable rule before deriving the verdict.
- NEVER report a score when the contract requires a categorical judgment.

</constraints>

<audit_workflow>

1. Resolve {{the complete audit scope}}.
2. Load {{the governing standards and repository-local specialization}}.
3. Judge every applicable rule and record falsifiable findings as they arise.
4. Derive the overall verdict from the finding rows and return the complete schema.

</audit_workflow>

<verdict_format>

```json
{
  "overall": "APPROVED | REJECTED",
  "scope": "{{exact audited scope}}",
  "rows": [
    {
      "name": "{{category one | category two | category three}}",
      "findings": [
        {
          "artifact": "{{path and line or section}}",
          "rule": "{{violated rule}}",
          "evidence": "{{falsifiable evidence}}",
          "required_fix": "{{correction required for approval}}"
        }
      ]
    }
  ]
}
```

</verdict_format>

<failure_modes>

{{Include only auditor failures observed in actual use, each with what happened, why it failed, and how to avoid it. Remove this section when no observed failure exists.}}

</failure_modes>

<success_criteria>

- Every applicable rule is judged, with none silently skipped.
- The overall verdict follows from the finding rows.
- Every rejected finding names the artifact, violated rule, and falsifiable evidence.
- The same subject and standards produce the same verdict.

</success_criteria>
