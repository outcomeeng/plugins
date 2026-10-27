<objective>

The rule catalog of the ADR audit: every rule identifier a native finding may carry, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog or the catalog of a composed language skill.

</objective>

<contents>
- `key_form`
- `form_rules`
- `blocked_inspection_rules`
- `composed_rules`

</contents>

<key_form>

The unit of a finding is the audited ADR file path, or `input` when the request carries no path. The key is `<unit>:<rule-id>`, for example `spx/55-example.enabler/15-y.adr.md:temporal-voice`. One key covers every location in the ADR where that rule is violated, and the finding lists each such location by the section or rule text, never a line number.

Severity in the tables below labels the defect on touched text. A finding whose locations all lie outside touched text takes severity `filed`.

</key_form>

<form_rules>

| Identifier                | Severity | Rule                                                                                                                                  | Stated in                                                       |
| ------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `missing-section`         | blocking | The ADR states its decision in the opening and carries a `## Verification` section.                                                   | The canonical ADR template, loaded in `audit_workflow` Step 1   |
| `temporal-voice`          | blocking | Every section states architecture truth atemporally.                                                                                  | `audit_workflow` Step 4                                         |
| `invalid-draft-rule`      | blocking | An untagged rule directly under `## Verification` names a subject, a constrained condition, and an observation that would violate it. | `audit_workflow` Step 5                                         |
| `invalid-tag`             | blocking | A routed rule carries exactly one tag valid for its subsection, and an `### Audit` slug repeats nowhere in the ADR.                   | `audit_workflow` Step 5                                         |
| `assertion-type-mismatch` | blocking | A `### Testing` rule's declared assertion type is compatible with the claim's quantifier and evidence shape.                          | `audit_workflow` Step 5; `product-tree:test-evidence-standards` |

</form_rules>

<blocked_inspection_rules>

Each rule below fires when a required inspection cannot run, and the finding names the blocked inspection.

| Identifier                     | Severity | Rule                                                                                                      | Stated in                |
| ------------------------------ | -------- | --------------------------------------------------------------------------------------------------------- | ------------------------ |
| `missing-target`               | blocking | The request carries the ADR path.                                                                         | `audit_workflow` Step 1  |
| `template-missing`             | blocking | The canonical ADR template guidance loads.                                                                | `audit_workflow` Step 3  |
| `test-standards-unavailable`   | blocking | The assertion-type litmus of `product-tree:test-evidence-standards` loads when `### Testing` holds rules. | `audit_workflow` Step 5  |
| `language-routing-unavailable` | blocking | A language-specific ADR resolves to a reliable implementation-language partition.                         | `audit_workflow` Step 5b |
| `language-skill-unavailable`   | blocking | The `audit-<lang>-architecture` skill of each discovered partition loads.                                 | `audit_workflow` Step 5b |
| `language-result-invalid`      | blocking | A composed result satisfies the invoked skill's declared verdict contract.                                | `audit_workflow` Step 5b |

</blocked_inspection_rules>

<composed_rules>

A validated composed finding keeps the rule identifier from the rule catalog of the invoked `audit-<lang>-architecture` skill, and its key is `<adr-file-path>:<that identifier>`. This catalog adds no identifier for it.

</composed_rules>
