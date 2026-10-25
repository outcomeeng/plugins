<objective>

The rule catalog of the spec-node audit: every rule identifier a finding may carry, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog.

</objective>

<contents>
- `key_form`
- `form_rules`
- `blocked_inspection_rules`

</contents>

<key_form>

The unit of a finding is the audited node-spec file path, or `input` when the request carries no path. The key is `<unit>:<rule-id>`, for example `spx/55-example.enabler/x.md:temporal-voice`. One key covers every location in the node spec where that rule is violated, and the finding lists each such location by the section or assertion text, never a line number.

Severity in the tables below labels the defect on touched text. A finding whose locations all lie outside touched text takes severity `filed`.

</key_form>

<form_rules>

| Identifier                 | Severity | Rule                                                                                                                       | Stated in                                                              |
| -------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `missing-section`          | blocking | The node spec carries a kind statement and an `## Assertions` section.                                                     | `audit_workflow` Step 3                                                |
| `malformed-kind-statement` | blocking | The kind statement matches its canonical template, or the prior grammar the foundation admits for an enabler or outcome.   | `audit_workflow` Step 3                                                |
| `missing-frontmatter`      | blocking | The node spec carries the front matter its canonical kind template requires.                                               | `audit_workflow` Step 3                                                |
| `missing-assertions`       | blocking | The `## Assertions` section contains at least one assertion.                                                               | `audit_workflow` Step 3                                                |
| `heading-mismatch`         | blocking | Each claim-shape heading holds at least one assertion of its claim shape, and no verification-type heading appears.        | `<constraints>` HEADINGS DESCRIBE CLAIM SHAPE; `audit_workflow` Step 3 |
| `temporal-voice`           | blocking | Every section states product truth atemporally.                                                                            | `audit_workflow` Step 4                                                |
| `invalid-tag`              | blocking | A routed assertion carries exactly one supported tag in its canonical form, and a path-bearing mechanism carries its path. | `audit_workflow` Step 5                                                |
| `evidence-type-mismatch`   | blocking | Under `[test]`, the assertion type fits the claim's quantifier, and a universal claim is never `scenario`.                 | `<constraints>` VERIFICATION TYPE MUST FIT THE CLAIM; Step 5           |
| `prose-coupling`           | blocking | A claim whose subject is the content of an authored prose or documentation artifact never carries `[test]`.                | `<constraints>` VERIFICATION TYPE MUST FIT THE CLAIM; Step 5           |
| `unfalsifiable-assertion`  | blocking | An untagged authoring declaration is specific and falsifiable.                                                             | `audit_workflow` Step 5                                                |

</form_rules>

<blocked_inspection_rules>

Each rule below fires when a required inspection cannot run, and the finding names the blocked inspection.

| Identifier           | Severity | Rule                                                                               | Stated in               |
| -------------------- | -------- | ---------------------------------------------------------------------------------- | ----------------------- |
| `missing-target`     | blocking | The request carries the node-spec path.                                            | `audit_workflow` Step 1 |
| `unsupported-target` | blocking | The target is an output or variant spec; a product spec carries no assertions.     | `audit_workflow` Step 1 |
| `template-missing`   | blocking | The canonical kind template loads beneath the foundation's resolved template root. | `audit_workflow` Step 1 |

</blocked_inspection_rules>
