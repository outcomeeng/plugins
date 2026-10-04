<definition_of_ready maturity="Sliced" cumulative="true">

Judge every criterion; this table includes the complete Proposed and Framed requirements and is the complete criterion set for Sliced Maturity, so apply no criterion outside it. Each criterion judges the record against the shared rule it names in `change-record.md`.

| ID                      | Criterion                                                                                                                                                |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sliced-record`         | The front matter and the body's section set and order satisfy `record-shape`, and the body opens with `## Intent`.                                       |
| `sliced-identity`       | `title`, `product`, `maturity: Sliced`, and `lifecycle` identify one intended Output, one Product, and a valid Lifecycle.                                |
| `sliced-relationships`  | `refined_from` and `blocked_by` satisfy `lineage` and `blockers`, `blocked_by` names every known blocker, and the dependency graph has no blocker cycle. |
| `sliced-intent`         | `## Intent` states What, Why, and Evidence under `intent`, with Observation present only where an observation gives rise to the Change.                  |
| `sliced-input-boundary` | The record satisfies `received-input-boundary`.                                                                                                          |
| `sliced-body-authority` | The body satisfies `body-authority`.                                                                                                                     |
| `sliced-nodes`          | `## Nodes` names every affected or intended Node with its target malleability under `nodes`.                                                             |
| `sliced-assertions`     | `## Assertion operations` names every Assertion operation by its owning Node or decision record and its exact target under `assertion-operations`.       |
| `sliced-decisions`      | `## Decisions` holds every question that can change the intended Output, and each carries its answer under `decisions`.                                  |
| `sliced-slice`          | `## Slice` names one vertical slice in one repository, with resolved dependencies and sequence and an observable check, under `slice`.                   |

</definition_of_ready>
