<definition_of_ready maturity="Framed" cumulative="true">

Judge every criterion; this table includes the complete Proposed requirements and is the complete criterion set for Framed Maturity, so apply no criterion outside it. Each criterion judges the record against the record rule it names in `<record_rules>`.

| ID                            | Criterion                                                                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `framed-record`               | The front matter and the body's section set and order satisfy `record-shape`, the title and Intent satisfy `record-limits`, and the body opens with `## Intent`.         |
| `framed-identity`             | `title`, `product`, `maturity: Framed`, and `lifecycle` identify one intended Output, its owning Product or none for a root, and a valid Lifecycle under `record-shape`. |
| `framed-relationships`        | `refined_from`, `parent`, and `blocked_by` satisfy `lineage` and `blockers`, and `blocked_by` names every known blocker.                                                 |
| `framed-intent`               | `## Intent` states What, Why, and Evidence under `intent`, with Observation present only where an observation gives rise to the Change.                                  |
| `framed-input-boundary`       | The record satisfies `received-input-boundary`.                                                                                                                          |
| `framed-body-authority`       | The body satisfies `body-authority`.                                                                                                                                     |
| `framed-governance`           | `## Governance` lists every governing record with its verdict `in line`, `amended`, or `new` under `governance`.                                                         |
| `framed-governance-mutations` | `## Governance mutations` holds a block for each amended or new record under `governance-mutations`.                                                                     |
| `framed-spec-mutations`       | `## Spec mutations` holds a block for each affected or intended Node, each opening with the Node's malleability before and after under `spec-mutations`.                 |
| `framed-open-questions`       | `## Open questions` is empty or absent under `open-questions`.                                                                                                           |

</definition_of_ready>
