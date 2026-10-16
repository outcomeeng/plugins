<objective>

The rule catalog of the spec-node audit: the identifier, severity, and recording unit of every rule the audit enforces.

</objective>

<contents>

- `<rule_catalog>` — the identifier and severity of every spec-node audit rule

</contents>

<rule_catalog>

Every rule the spec-node audit enforces has one row: one stable identifier, one severity, and the unit that records it. A finding names exactly one identifier from this table, carries the severity its row declares, and names no identifier outside it. A defect no row covers is a gap in this standard: the rule enters this table before any finding cites it.

| Identifier                 | Severity | Rule                                                                                                                                  | Unit                                     |
| -------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `unsupported-target`       | blocking | The target is an output or variant spec, never a product spec.                                                                        | the root                                 |
| `template-missing`         | blocking | The canonical kind template loads, so the opening, front matter, and tag forms derive from it.                                        | `section-structure`                      |
| `missing-section`          | blocking | The node carries a kind statement and an `## Assertions` section.                                                                     | `section-structure`                      |
| `malformed-kind-statement` | blocking | The kind statement carries every clause its template, or its admitted prior form, requires.                                           | `section-structure`                      |
| `missing-frontmatter`      | blocking | The node carries the front matter its template requires.                                                                              | `section-structure`                      |
| `missing-assertions`       | blocking | The `## Assertions` section holds at least one assertion.                                                                             | `section-structure`                      |
| `heading-mismatch`         | blocking | Each claim-shape heading is nonempty and holds only assertions of its claim shape, and no verification-type heading appears.          | `section-structure`                      |
| `temporal-voice`           | blocking | Every section states atemporal product truth, with no reference to past behavior, events, or current state.                           | `atemporal-voice`                        |
| `invalid-tag`              | blocking | A routed assertion carries exactly one tag its template and malleability admit, with a path or slug where the mechanism requires one. | `tag-fitness`                            |
| `evidence-type-mismatch`   | blocking | A `[test]` assertion's assertion type fits the claim's quantifier, and is one the `/test` router would produce.                       | `tag-fitness`                            |
| `prose-coupling`           | blocking | A claim about authored prose or documentation content carries `[eval]` or `[audit]`, never `[test]`.                                  | `tag-fitness`                            |
| `unfalsifiable-assertion`  | blocking | An untagged assertion names an observable condition and a concrete violating observation.                                             | `tag-fitness`                            |
| `context-unavailable`      | blocking | Every decision a loaded record cites by full `spx/` path can be read.                                                                 | the concern that names it, else the root |

</rule_catalog>
