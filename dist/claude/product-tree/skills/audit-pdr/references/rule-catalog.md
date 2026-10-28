<objective>

The rule catalog of the PDR audit: every rule identifier a finding may carry, the unit it is recorded on, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog.

</objective>

<contents>
- `key_form`
- `form_rules`
- `blocked_inspection_rules`

</contents>

<key_form>

The unit of a finding is the child unit key `pdr:<designator>:<pdr-file-path>` of the property it concerns. The key is `<unit>:<rule-id>`, for example `pdr:atemporal-voice:spx/55-example.enabler/15-y.pdr.md:temporal-voice`. One key covers every location in the PDR where that rule is violated on that unit, and the finding lists each such location by the section, property, or rule text, never a line number, separated by `;`.

Severity in the tables below labels the defect on touched text. A finding whose locations all lie outside touched text is returned as `filed` with its recorded severity.

</key_form>

<form_rules>

| Identifier                   | Unit                     | Severity | Rule                                                                                                                                            | Stated in                                                       |
| ---------------------------- | ------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `architecture-content`       | `content-classification` | blocking | Every statement is product behavior the declared audience observes or operates, and none states architecture or implementation.                 | `audit_workflow` Step 4                                         |
| `non-observable-property`    | `property-quality`       | blocking | Every product property is observable and falsifiable from the declared audience's perspective.                                                  | `audit_workflow` Step 5                                         |
| `unstable-property`          | `property-quality`       | blocking | Every product property holds across all applicable contexts, including failure and boundary conditions.                                         | `audit_workflow` Step 5                                         |
| `invalid-draft-rule`         | `property-quality`       | blocking | An untagged rule directly under `## Verification` names a subject, a constrained condition, and an observation that would violate it.           | `audit_workflow` Step 6                                         |
| `missing-section`            | `tag-validity`           | blocking | The PDR carries a `## Verification` section.                                                                                                    | `audit_workflow` Step 2                                         |
| `missing-verification-rules` | `tag-validity`           | blocking | The `## Verification` section contains rules.                                                                                                   | `audit_workflow` Step 6                                         |
| `invalid-tag`                | `tag-validity`           | blocking | A routed rule is verifiable and specific, carries exactly one tag valid for its subsection, and an `### Audit` slug repeats nowhere in the PDR. | `audit_workflow` Step 6                                         |
| `assertion-type-mismatch`    | `tag-validity`           | blocking | A `### Testing` rule's declared assertion type is compatible with the claim's quantifier and evidence shape.                                    | `audit_workflow` Step 6; `product-tree:test-evidence-standards` |
| `temporal-voice`             | `atemporal-voice`        | blocking | Every section states product truth atemporally.                                                                                                 | `audit_workflow` Step 7                                         |
| `consistency-violation`      | `consistency`            | blocking | The PDR contradicts neither the product document nor an ancestor PDR.                                                                           | `audit_workflow` Step 8                                         |

</form_rules>

<blocked_inspection_rules>

Each rule below fires when a required inspection cannot run, and the finding names the blocked inspection. A request that carries no PDR path starts no run and returns `BLOCKED`, so it has no rule here.

| Identifier                   | Unit           | Severity | Rule                                                                                                      | Stated in               |
| ---------------------------- | -------------- | -------- | --------------------------------------------------------------------------------------------------------- | ----------------------- |
| `test-standards-unavailable` | `tag-validity` | blocking | The assertion-type litmus of `product-tree:test-evidence-standards` loads when `### Testing` holds rules. | `audit_workflow` Step 6 |

</blocked_inspection_rules>
