<objective>

The rule catalog of the ADR audit: every rule identifier a native finding may carry, the unit it is recorded on, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog or the catalog of a composed language skill.

</objective>

<contents>
- `key_form`
- `form_rules`
- `blocked_inspection_rules`
- `composed_rules`

</contents>

<key_form>

The unit of a finding is the child unit key `adr:<designator>:<adr-file-path>` of the property or composed concern it concerns. The key is `<unit>:<rule-id>`, for example `adr:atemporal-voice:spx/55-example.enabler/15-y.adr.md:temporal-voice`. One key covers every location in the ADR where that rule is violated on that unit, and the finding lists each such location by the section or rule text, never a line number, separated by `;`.

Severity in the tables below labels the defect on touched text. A finding whose locations all lie outside touched text is returned as `filed` with its recorded severity.

</key_form>

<form_rules>

| Identifier                | Unit                | Severity | Rule                                                                                                                                  | Stated in                                                       |
| ------------------------- | ------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `missing-section`         | `section-structure` | blocking | The ADR states its decision in the opening and carries a `## Verification` section.                                                   | The canonical ADR template, loaded in `audit_workflow` Step 1   |
| `temporal-voice`          | `atemporal-voice`   | blocking | Every section states architecture truth atemporally.                                                                                  | `audit_workflow` Step 5                                         |
| `invalid-draft-rule`      | `tag-validity`      | blocking | An untagged rule directly under `## Verification` names a subject, a constrained condition, and an observation that would violate it. | `audit_workflow` Step 6                                         |
| `invalid-tag`             | `tag-validity`      | blocking | A routed rule carries exactly one tag valid for its subsection, and an `### Audit` slug repeats nowhere in the ADR.                   | `audit_workflow` Step 6                                         |
| `assertion-type-mismatch` | `tag-validity`      | blocking | A `### Testing` rule's declared assertion type is compatible with the claim's quantifier and evidence shape.                          | `audit_workflow` Step 6; `product-tree:test-evidence-standards` |

</form_rules>

<blocked_inspection_rules>

Each rule below fires when a required inspection cannot run, and the finding names the blocked inspection. A request that carries no ADR path starts no run and returns `BLOCKED`, so it has no rule here.

| Identifier                     | Unit                     | Severity | Rule                                                                                                      | Stated in               |
| ------------------------------ | ------------------------ | -------- | --------------------------------------------------------------------------------------------------------- | ----------------------- |
| `template-missing`             | `section-structure`      | blocking | The canonical ADR template guidance loads.                                                                | `audit_workflow` Step 4 |
| `test-standards-unavailable`   | `tag-validity`           | blocking | The assertion-type litmus of `product-tree:test-evidence-standards` loads when `### Testing` holds rules. | `audit_workflow` Step 6 |
| `language-routing-unavailable` | `language-routing`       | blocking | A language-specific ADR resolves to a reliable implementation-language partition.                         | `audit_workflow` Step 7 |
| `language-skill-unavailable`   | `<lang>:language-skill`  | blocking | The `audit-<lang>-architecture` skill of each discovered partition loads.                                 | `audit_workflow` Step 7 |
| `language-result-invalid`      | `<lang>:language-result` | blocking | A composed result satisfies the invoked skill's declared verdict contract.                                | `audit_workflow` Step 7 |

</blocked_inspection_rules>

<composed_rules>

A validated composed finding keeps the rule identifier from the rule catalog of the invoked `audit-<lang>-architecture` skill, is recorded on the child unit `adr:<lang>:<row-name>:<adr-file-path>`, and its key is that unit key and identifier. This catalog adds no identifier for it.

</composed_rules>
