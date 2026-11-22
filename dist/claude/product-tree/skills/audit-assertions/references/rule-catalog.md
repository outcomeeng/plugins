<objective>

The rule catalog of the assertion audit: every rule identifier a finding may carry, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog.

</objective>

<contents>

- `key_form`
- `assertion_rules`

</contents>

<key_form>

The unit of a finding is the unit key of the audited assertion, `assertion:<slug>:<path>`, where the slug is the assertion's leading slug. The key is `<unit>:<rule-id>`, for example `assertion:no-dead-links:spx/55-example.enabler/x.md:subject-not-found`. One key covers every location where that rule is violated on that assertion, and the finding lists each such location by the subject path and the line or section, separated by `;`.

An Audit Assertion opens with its leading slug, its one name in the spec. The slug identifies the unit and opens the finding's message, so the slug is carried by the unit key and the message and is never the rule identifier. The identifier names the way the audit judges the assertion.

Severity in the table labels the defect: `blocking` for a merge-safety defect and `debt` for a real defect that does not jeopardize merge safety. A finding whose locations all lie outside touched text is returned as `filed` with its recorded severity.

</key_form>

<assertion_rules>

| Identifier          | Severity          | Rule                                                                                              | Stated in               |
| ------------------- | ----------------- | ------------------------------------------------------------------------------------------------- | ----------------------- |
| `constraint-unmet`  | `blocking`/`debt` | The subject the assertion names holds the constraint the assertion states.                        | `audit_workflow` Step 4 |
| `subject-not-found` | `blocking`/`debt` | Every subject the assertion's text names can be located in the product.                           | `audit_workflow` Step 4 |
| `subject-unnamed`   | `blocking`/`debt` | The assertion's text names an identifiable artifact, behavior, or constraint to judge it against. | `audit_workflow` Step 4 |

</assertion_rules>
