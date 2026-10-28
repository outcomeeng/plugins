<objective>

The rule catalog of the spec-node audit: every rule identifier a finding may carry, the unit it is recorded on, its severity, and the clause it states. A finding is keyed `<unit>:<rule-id>` over these identifiers, and no finding names an identifier outside this catalog.

</objective>

<contents>
- `key_form`
- `form_rules`
- `blocked_inspection_rules`

</contents>

<key_form>

The unit of a finding is the child unit key `spec:<designator>:<node-spec-file-path>` of the property it concerns. The key is `<unit>:<rule-id>`, for example `spec:atemporal-voice:spx/55-example.enabler/x.md:temporal-voice`. One key covers every location in the node spec where that rule is violated on that unit, and the finding lists each such location by the section or assertion text, never a line number, separated by `;`.

Severity in the tables below labels the defect on touched text. A finding whose locations all lie outside touched text is returned as `filed` with its recorded severity.

</key_form>

<form_rules>

| Identifier                 | Unit                | Severity | Rule                                                                                                                       | Stated in                                                              |
| -------------------------- | ------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `missing-section`          | `section-structure` | blocking | The node spec carries a kind statement and an `## Assertions` section.                                                     | `audit_workflow` Step 4                                                |
| `malformed-kind-statement` | `section-structure` | blocking | The kind statement matches its canonical template, or the prior grammar the foundation admits for an enabler or outcome.   | `audit_workflow` Step 4                                                |
| `missing-frontmatter`      | `section-structure` | blocking | The node spec carries the front matter its canonical kind template requires.                                               | `audit_workflow` Step 4                                                |
| `missing-assertions`       | `section-structure` | blocking | The `## Assertions` section contains at least one assertion.                                                               | `audit_workflow` Step 4                                                |
| `heading-mismatch`         | `section-structure` | blocking | Each claim-shape heading holds at least one assertion of its claim shape, and no verification-type heading appears.        | `<constraints>` HEADINGS DESCRIBE CLAIM SHAPE; `audit_workflow` Step 4 |
| `temporal-voice`           | `atemporal-voice`   | blocking | Every section states product truth atemporally.                                                                            | `audit_workflow` Step 5                                                |
| `invalid-tag`              | `tag-fitness`       | blocking | A routed assertion carries exactly one supported tag in its canonical form, and a path-bearing mechanism carries its path. | `audit_workflow` Step 6                                                |
| `evidence-type-mismatch`   | `tag-fitness`       | blocking | Under `[test]`, the assertion type fits the claim's quantifier, and a universal claim is never `scenario`.                 | `<constraints>` VERIFICATION TYPE MUST FIT THE CLAIM; Step 6           |
| `prose-coupling`           | `tag-fitness`       | blocking | A claim whose subject is the content of an authored prose or documentation artifact never carries `[test]`.                | `<constraints>` VERIFICATION TYPE MUST FIT THE CLAIM; Step 6           |
| `unfalsifiable-assertion`  | `tag-fitness`       | blocking | An untagged authoring declaration is specific and falsifiable.                                                             | `audit_workflow` Step 6                                                |

</form_rules>

<blocked_inspection_rules>

Each rule below fires when a required inspection cannot run, and the finding names the blocked inspection. A request that carries no node-spec path, or names a product document, starts no run and returns `BLOCKED`, so it has no rule here.

| Identifier         | Unit                | Severity | Rule                                                                               | Stated in               |
| ------------------ | ------------------- | -------- | ---------------------------------------------------------------------------------- | ----------------------- |
| `template-missing` | `section-structure` | blocking | The canonical kind template loads beneath the foundation's resolved template root. | `audit_workflow` Step 4 |

</blocked_inspection_rules>
