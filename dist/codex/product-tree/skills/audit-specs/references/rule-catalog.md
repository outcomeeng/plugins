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

| Identifier                 | Severity | Rule                                                                                                                                                                                                       | Stated in                                       |
| -------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `missing-section`          | blocking | The node spec carries a kind statement and an `## Assertions` section.                                                                                                                                     | `audit_workflow` Step 3                         |
| `malformed-kind-statement` | blocking | The kind statement matches its canonical template, or the prior grammar the foundation admits for an enabler or outcome.                                                                                   | `audit_workflow` Step 3                         |
| `missing-frontmatter`      | blocking | The node spec carries the front matter its canonical kind template requires.                                                                                                                               | `audit_workflow` Step 3                         |
| `missing-assertions`       | blocking | The `## Assertions` section contains at least one row.                                                                                                                                                     | `audit_workflow` Step 3                         |
| `heading-mismatch`         | blocking | Every row stands under a group heading that names its verification type, every group holds at least one row, and a `Given … When … Then …` row stands under no `Test.` heading other than `Test.Scenario`. | `<constraints>`; `audit_workflow` Steps 3 and 5 |
| `temporal-voice`           | blocking | Every section states product truth atemporally.                                                                                                                                                            | `audit_workflow` Step 4                         |
| `invalid-tag`              | blocking | A row carries no tag, and its leading slug repeats nowhere in the spec.                                                                                                                                    | `<constraints>`; `audit_workflow` Step 5        |
| `evidence-type-mismatch`   | blocking | Under a `Test.` heading, the assertion type fits the claim's quantifier, and a universal claim never stands under `Test.Scenario`.                                                                         | `<constraints>`; `audit_workflow` Step 5        |
| `prose-coupling`           | blocking | A claim whose subject is the content of an authored prose or documentation artifact stands under no `Test.` heading.                                                                                       | `<constraints>`; `audit_workflow` Step 5        |
| `slug-link-mismatch`       | blocking | A row's slug links an artifact only in the directory its heading's type names, and an `Audit` row links none.                                                                                              | `<constraints>`; `audit_workflow` Step 5        |
| `unfalsifiable-assertion`  | blocking | A row's claim is specific and falsifiable.                                                                                                                                                                 | `audit_workflow` Step 5                         |

</form_rules>

<blocked_inspection_rules>

Each rule below fires when a required inspection cannot run, and the finding names the blocked inspection.

| Identifier           | Severity | Rule                                                                               | Stated in               |
| -------------------- | -------- | ---------------------------------------------------------------------------------- | ----------------------- |
| `missing-target`     | blocking | The request carries the node-spec path.                                            | `audit_workflow` Step 1 |
| `unsupported-target` | blocking | The target is an output or variant spec; a product document carries no assertions. | `audit_workflow` Step 1 |
| `template-missing`   | blocking | The canonical kind template loads beneath the foundation's resolved template root. | `audit_workflow` Step 1 |

</blocked_inspection_rules>
