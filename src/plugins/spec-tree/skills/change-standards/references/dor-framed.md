<definition_of_ready maturity="Framed" cumulative="true">

Judge every criterion; this table includes the complete Proposed requirements and is the complete criterion set for Framed Maturity, so apply no criterion outside it. Each criterion judges the record against the record rule it names in `<record_rules>`. A criterion's blocking status follows `review-bar`.

| ID                            | Criterion                                                                                                                                                                                       |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `framed-identity`             | `title`, `product`, `maturity: Framed`, and `lifecycle` identify one intended Output, its owning Product or none for a root, and a valid Lifecycle under `record-shape`.                        |
| `framed-relationships`        | `predecessors`, `parent`, and `blocked_by` satisfy `lineage` and `blockers`, and `blocked_by` names every known blocker.                                                                        |
| `framed-intent`               | `## Intent` states What, Why, and Evidence under `intent`, with Observation present only where an observation gives rise to the Change.                                                         |
| `framed-input-boundary`       | The record satisfies `received-input-boundary`.                                                                                                                                                 |
| `framed-body-authority`       | The body satisfies `body-authority`.                                                                                                                                                            |
| `framed-governance`           | `## Governance` lists every record the Output touches or that governs it, by its path from `spx/`, each with the verdict `in line`, `amended`, or `new`, under `governance`.                    |
| `framed-governance-mutations` | `## Governance mutations` holds the exact text of every decision the Output adds or amends, under `governance-mutations`.                                                                       |
| `framed-spec-mutations`       | `## Spec mutations` holds a block for each affected or intended Node stating its assertions, each opening with the Node's malleability before and after, under `spec-mutations`.                |
| `framed-no-open-question`     | `## Open questions` is empty or absent under `open-questions`, and each question the Frame settled stands under `## Assumptions` as its answer and one sentence of reason, under `assumptions`. |

</definition_of_ready>
