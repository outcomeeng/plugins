<objective>
The canonical structure for an auditor skill — the family whose output is a structured verdict.
</objective>

<output_is_a_verdict>
An auditor's output is a **verdict**: a structured judgment over a defined scope, against a defined standard. An auditor produces no fix, no commit, and no artifact other than the verdict. Every section below serves that one output.
</output_is_a_verdict>

<skeleton>
Ordered sections of an auditor `SKILL.md`:

| Section              | Content                                                                                                                                                                                                                                         |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<objective>`        | The verdict as output: the scope, the standard, and the finding categories — APPROVED, or REJECTED with each finding naming the artifact, the violated rule, and the evidence. The full row/field schema lives in `<verdict_format>`, not here. |
| `<constraints>`      | Read-only; produces a verdict, never fixes or commits.                                                                                                                                                                                          |
| `<audit_workflow>`   | The ordered steps that arrive at the verdict. The standard name for an auditor's procedure — not `process`, `critical_workflow`, or `workflow`.                                                                                                 |
| `<verdict_format>`   | The full output schema: the rows and fields of the verdict, one grouping per finding category named in `<objective>`. The standard name for an auditor's output block — not `output_format`.                                                    |
| `<failure_modes>`    | Auditor-specific failures from real use (false-approve, scope skipped, scored instead of judged), each as what / why / how-to-avoid.                                                                                                            |
| `<success_criteria>` | The properties that prove the verdict is sound — see `<success_criteria_shape>`.                                                                                                                                                                |
| reference sections   | `<reference_guides>` / `<reference_index>` as needed.                                                                                                                                                                                           |

Auditors carry **no `<quick_start>`** — the objective states the verdict and `<audit_workflow>` states the steps, so an abbreviated path only duplicates them.
</skeleton>

<objective_examples>
The objective names the verdict, not the activity:

- ❌ "Audit an ADR for its structure, atemporal voice, and conformance to the evidence model." (bare activity verb)
- ❌ "Evaluate SKILL.md files against best practices." (activity verb)
- ✅ "A verdict on one ADR against the ADR evidence model — APPROVED, or REJECTED with each finding naming the section, the violated rule, and the evidence. Findings fall in three categories: section structure, atemporal voice, and per-rule tag validity."
- ✅ "A verdict on implementation code — APPROVED, or REJECTED with each finding naming the design flaw, the violated rule, and the evidence."
- ✅ "A verdict on test evidence — APPROVED, or REJECTED with each finding naming the assertion or evidence artifact, the failed evidence property, and the evidence."

Code-auditor and test-auditor objectives use the APPROVED/REJECTED field form above. Their `<verdict_format>` owns the detailed row schema and may group findings by concern; the objective stays stable when a language adds or renames a row.

</objective_examples>

<success_criteria_shape>
An auditor's `<success_criteria>` states verdict soundness, never a re-list of the workflow steps:

- Every applicable rule was judged — none skipped (coverage-complete).
- The verdict states its overall determination — APPROVED/REJECTED, PASS/FAIL, or the auditor's keep/worth-improving/must-fix grouping — with no rule left unevaluated.
- Each finding that flags a problem is falsifiable: it names the artifact, the violated rule, and the evidence.
- The same input yields the same verdict (reproducible).

The ordered steps ("`/contextualize` invoked", "artifact read", "tests run") belong in `<audit_workflow>`, not here — listing them as success criteria is the activity/output confusion the output framing removes.
</success_criteria_shape>

<prose_variant>
The prose auditors (`audit-prose`, `audit-document`) may name their procedure section to fit their domain. They keep the verdict-as-output `<objective>` and the `<success_criteria>` soundness shape.
</prose_variant>
