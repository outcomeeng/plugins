<definition_of_ready maturity="Framed" cumulative="true">

Judge every criterion; this table includes the complete Proposed requirements and is the complete criterion set for Framed Maturity, so apply no criterion outside it. Each criterion judges the record against the record rule it names in `<record_rules>`.

| ID                      | Criterion                                                                                                                                          |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `framed-record`         | The front matter and the body's section set and order satisfy `record-shape`, and the body opens with `## Intent`.                                 |
| `framed-identity`       | `title`, `product`, `maturity: Framed`, and `lifecycle` identify one intended Output, one Product, and a valid Lifecycle under `record-shape`.     |
| `framed-relationships`  | `refined_from` and `blocked_by` satisfy `lineage` and `blockers`, and `blocked_by` names every known blocker.                                      |
| `framed-intent`         | `## Intent` states What, Why, and Evidence under `intent`, with Observation present only where an observation gives rise to the Change.            |
| `framed-input-boundary` | The record satisfies `received-input-boundary`.                                                                                                    |
| `framed-body-authority` | The body satisfies `body-authority`.                                                                                                               |
| `framed-nodes`          | `## Nodes` names every affected or intended Node with its target malleability under `nodes`.                                                       |
| `framed-assertions`     | `## Assertion operations` names every Assertion operation by its owning Node or decision record and its exact target under `assertion-operations`. |
| `framed-decisions`      | `## Decisions` holds every question that can change the intended Output, and each carries its answer under `decisions`.                            |

</definition_of_ready>
