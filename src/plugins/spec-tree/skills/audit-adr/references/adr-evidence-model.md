<objective>

The rule catalog of the ADR audit: the identifier, severity, and recording unit of every rule the audit enforces.

</objective>

<contents>

- `<rule_catalog>` — the identifier and severity of every ADR audit rule

</contents>

<rule_catalog>

Every rule the ADR audit enforces has one row: one stable identifier, one severity, and the unit that records it. A finding names exactly one identifier from this table, carries the severity its row declares, and names no identifier outside it. A composed language finding is the one exception: it retains the identifier that the invoked language audit's own rule catalog gives the violated rule. A defect no row covers is a gap in this standard: the rule enters this table before any finding cites it.

| Identifier                     | Severity | Rule                                                                                                                  | Unit                                     |
| ------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `missing-section`              | blocking | The ADR states its decision in the opening and carries the `## Verification` section its template requires.           | `section-structure`                      |
| `template-missing`             | blocking | The canonical ADR template guidance loads, so the valid section set derives from it.                                  | `section-structure`                      |
| `temporal-voice`               | blocking | Every section states atemporal architecture truth, with no reference to past behavior, events, or current state.      | `atemporal-voice`                        |
| `invalid-draft-rule`           | blocking | An untagged rule directly under `## Verification` names an observable condition and a concrete violating observation. | `tag-validity`                           |
| `invalid-tag`                  | blocking | A routed rule carries exactly one tag, valid for its subsection.                                                      | `tag-validity`                           |
| `assertion-type-mismatch`      | blocking | A `### Testing` rule's assertion type fits the quantifier and evidence shape of its claim.                            | `tag-validity`                           |
| `test-standards-unavailable`   | blocking | The test-evidence standards load for the assertion-type check when `### Testing` holds rules.                         | `tag-validity`                           |
| `language-routing-unavailable` | blocking | A language-specific ADR resolves a reliable implementation-language partition.                                        | the partition's unit, else the root      |
| `language-skill-unavailable`   | blocking | The language architecture audit skill for each discovered partition loads.                                            | the partition's unit                     |
| `language-result-invalid`      | blocking | A composed language result satisfies the invoked skill's declared verdict contract.                                   | the partition's unit                     |
| `context-unavailable`          | blocking | Every decision a loaded record cites by full `spx/` path can be read.                                                 | the concern that names it, else the root |

</rule_catalog>
