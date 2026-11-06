<objective>

The rule catalog of the PDR audit: every rule identifier a finding may carry, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog.

</objective>

<contents>
- `key_form`
- `form_rules`
- `blocked_inspection_rules`

</contents>

<key_form>

The unit of a finding is the audited PDR file path, or `input` when the request carries no path. The key is `<unit>:<rule-id>`, for example `spx/55-example.enabler/15-y.pdr.md:temporal-language`. One key covers every location in the PDR where that rule is violated, and the finding lists each such location by the section, property, or rule text, never a line number.

Severity in the tables below labels the defect on touched text. A finding whose locations all lie outside touched text takes severity `filed`.

</key_form>

<form_rules>

| Identifier                   | Severity | Rule                                                                                                                                                                                                            | Stated in                                                       |
| ---------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `missing-section`            | blocking | The PDR carries a `## Verification` section.                                                                                                                                                                    | `audit_workflow` Step 2                                         |
| `architecture-content`       | blocking | Every statement is product behavior the declared audience observes or operates, and none states architecture or implementation.                                                                                 | `audit_workflow` Step 3                                         |
| `non-observable-property`    | blocking | The behavior the CAN RELY ON line names is observable and falsifiable from the declared audience's perspective.                                                                                                 | `audit_workflow` Step 4                                         |
| `unstable-property`          | blocking | The behavior the CAN RELY ON line names holds across all applicable contexts, including failure and boundary conditions.                                                                                        | `audit_workflow` Step 4                                         |
| `missing-verification-rules` | blocking | The `## Verification` section contains rules.                                                                                                                                                                   | `audit_workflow` Step 5                                         |
| `declaration-form`           | blocking | The PDR opens with a GOVERNS paragraph, writes each mapping rule as its own `### Mapping: <slug>` subsection, keeps each group to at most ten rules, and holds no text outside its opening, a rule, or a table. | `audit_workflow` Step 5                                         |
| `invalid-draft-rule`         | blocking | A rule directly under `## Verification`, outside any group, names a subject, a constrained condition, and an observation that would violate it.                                                                 | `audit_workflow` Step 5                                         |
| `invalid-tag`                | blocking | A rule is verifiable and specific, carries no tag, and its leading slug repeats nowhere in the PDR.                                                                                                             | `audit_workflow` Step 5                                         |
| `assertion-type-mismatch`    | blocking | A rule's assertion type, named by its group heading, is compatible with the claim's quantifier and evidence shape.                                                                                              | `audit_workflow` Step 5; `product-tree:test-evidence-standards` |
| `temporal-language`          | blocking | The opening and every rule state product truth atemporally.                                                                                                                                                     | `audit_workflow` Step 6                                         |
| `consistency-violation`      | blocking | The PDR contradicts neither the product document nor an ancestor PDR.                                                                                                                                           | `audit_workflow` Step 7                                         |

</form_rules>

<blocked_inspection_rules>

Each rule below fires when a required inspection cannot run, and the finding names the blocked inspection.

| Identifier                   | Severity | Rule                                                                                                            | Stated in               |
| ---------------------------- | -------- | --------------------------------------------------------------------------------------------------------------- | ----------------------- |
| `missing-target`             | blocking | The request carries the PDR path.                                                                               | `audit_workflow` Step 1 |
| `test-standards-unavailable` | blocking | The assertion-type litmus of `product-tree:test-evidence-standards` loads when a group names an assertion type. | `audit_workflow` Step 5 |

</blocked_inspection_rules>
