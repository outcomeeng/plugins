<definition_of_ready maturity="Proposed" cumulative="true">

Judge every criterion; this table is the complete criterion set for Proposed Maturity, so apply no criterion outside it. Each criterion judges the record against the record rule it names in `<record_rules>`. A failed criterion is a blocking finding; a finding against any other record rule is non-blocking under `review-bar`.

| ID                        | Criterion                                                                                                                                                                  |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `proposed-identity`       | `title`, `product`, `maturity: Proposed`, and `lifecycle` identify one intended Output, its owning Product or none for a root, and a valid Lifecycle under `record-shape`. |
| `proposed-relationships`  | `predecessors`, `parent`, and `blocked_by` satisfy `lineage` and `blockers`, and `blocked_by` names every known blocker.                                                   |
| `proposed-intent`         | `## Intent` states What, Why, and Evidence under `intent`, with Observation present only where an observation gives rise to the Change.                                    |
| `proposed-governance`     | `## Governance` names every record the Output touches, each with its verdict `in line`, `amended`, or `new`, under `governance`.                                           |
| `proposed-decisions`      | `## Governance mutations` holds the exact text of every decision the Output adds or amends, under `governance-mutations`.                                                  |
| `proposed-nodes`          | `## Spec mutations` names every Node the Output touches by its opening line, under `spec-mutations`.                                                                       |
| `proposed-questions`      | Every known question that can change the intended Output stands under `## Open questions` under `open-questions`; no answer is invented.                                   |
| `proposed-input-boundary` | The record satisfies `received-input-boundary`.                                                                                                                            |
| `proposed-body-authority` | The body satisfies `body-authority`.                                                                                                                                       |

No criterion requires an operator review statement, and no criterion is an audit verdict.

</definition_of_ready>
