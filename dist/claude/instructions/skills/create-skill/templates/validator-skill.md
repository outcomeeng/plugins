---
name: "{{skill-name}}"
description: >-
  ALWAYS invoke this skill when validating {{triggers}}.
---

<objective>
A deterministic verdict on whether {{subject}} satisfies the declared quality contract, with criterion-level evidence and remediation for every failure.
</objective>

<quality_criteria>

| Criterion       | Evidence            | Pass threshold |
| --------------- | ------------------- | -------------- |
| {{Criterion 1}} | {{Evidence source}} | {{Threshold}}  |
| {{Criterion 2}} | {{Evidence source}} | {{Threshold}}  |

</quality_criteria>

<verdict_contract>

| Verdict   | Mechanical condition                  | Required action                                     |
| --------- | ------------------------------------- | --------------------------------------------------- |
| `PASS`    | Every criterion meets its threshold   | Return evidence rows                                |
| `FAIL`    | One or more criteria miss a threshold | Return failed rows and remediation                  |
| `BLOCKED` | Required evidence cannot be obtained  | Return the missing evidence and acquisition failure |

</verdict_contract>

<validation_report>

<verdict>{{PASS, FAIL, or BLOCKED}}</verdict>
<coverage>{{Every criterion and evidence source inspected.}}</coverage>
<results>{{Criterion, observed value, threshold, and status.}}</results>
<remediation>{{Exact correction for each failed criterion.}}</remediation>

</validation_report>

<workflow>

<step name="collect_evidence">{{Collect every declared evidence source without mutation.}}</step>
<step name="evaluate_criteria">{{Compare each observation with its threshold.}}</step>
<step name="derive_verdict">{{Apply the verdict contract mechanically.}}</step>
<step name="render_report">{{Return all rows and required remediation.}}</step>

</workflow>

<success_criteria>

- Every criterion has an observed value or an explicit evidence-acquisition failure.
- The verdict follows mechanically from the criterion rows.
- Every failed criterion has specific remediation and validation changes no subject file.

</success_criteria>
