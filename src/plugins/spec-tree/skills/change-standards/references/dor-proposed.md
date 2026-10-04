<definition_of_ready maturity="Proposed" cumulative="true">

Judge every criterion; this table is the complete criterion set for Proposed Maturity, so apply no criterion outside it. Each criterion judges the record against the shared rule it names in `change-record.md`.

| ID                        | Criterion                                                                                                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `proposed-record`         | The front matter and the body's section set and order satisfy `record-shape`, and the body opens with `## Intent`.                               |
| `proposed-identity`       | `title`, `product`, `maturity: Proposed`, and `lifecycle` identify one intended Output, one Product, and a valid Lifecycle under `record-shape`. |
| `proposed-relationships`  | `refined_from` and `blocked_by` satisfy `lineage` and `blockers`, and `blocked_by` names every known blocker.                                    |
| `proposed-intent`         | `## Intent` states What, Why, and Evidence under `intent`, with Observation present only where an observation gives rise to the Change.          |
| `proposed-questions`      | Every known question that can change the intended Output stands under `## Decisions` under `decisions`; no answer is invented.                   |
| `proposed-input-boundary` | The record satisfies `received-input-boundary`.                                                                                                  |
| `proposed-body-authority` | The body satisfies `body-authority`.                                                                                                             |

Readiness at Proposed is the approving audit against this table; no criterion requires an operator review statement, and no criterion is an audit verdict.

</definition_of_ready>
