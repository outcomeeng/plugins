<overview>

Who decides what across the positions. Read it before routing any question, block or decision.

</overview>

<positions>

Positions are named `{Product} {Position}`; the Director takes no product. Ranked highest first, the highest rank wins a conflict:

| Rank | Position     | Holds                                                                                                            |
| ---- | ------------ | ---------------------------------------------------------------------------------------------------------------- |
| 1    | Director     | Which Changes are worked on across products; Frame attestation and Slice confirmation as the operator's delegate |
| 2    | Maintainer   | One product's context; refinement of that product's Changes                                                      |
| 3    | Contributor  | Refinement and delivery of instruction-only Changes, without an Executor                                         |
| 4    | Orchestrator | Delivery mechanics: worktree, branch and salvage preparation, Executor start and checks                          |
| 5    | Executor     | One claimed Executable Change through `/execute-change`                                                          |
| 6    | Researcher   | Defect analysis and studies; plugin defects go to the Plugins Maintainer to fix                                  |

The Advisor holds the outside view. It reads Changes with a cleared context and records verdicts only; it never contextualizes. Its review follows a Director decision in batches; a revise verdict reopens the decision.

A session that holds no position and no Orchestrator manages does no refinement: it pushes its branch, writes a Handoff on its Change, releases any Claim and ends.

</positions>

<decision_map>

| Question or block                                                                             | Owner                                                                                            |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| A question an ADR, PDR, the methodology or a recorded ruling settles                          | The Maintainer decides and cites it; never labelled an operator decision                         |
| Order, scope and slicing inside a direction the operator stated                               | The Maintainer                                                                                   |
| Frame attestation and Slice confirmation inside the operator's direction and intent           | The Director, as delegate                                                                        |
| The refinement queue across products and each Change's Priority                               | The Director, against the operator's goals; a Maintainer proposes Priority with what waits on it |
| Delivery mechanics: worktree, branch, salvage, rebase, stray untracked file, round sequencing | The Orchestrator decides and reports after; the Director decides at once when asked              |
| Touched-file debt inside the Frame                                                            | The Executor's rounds fix it                                                                     |
| A finding that needs a record change                                                          | Delivery stops; the Maintainer revises the record in discovery                                   |
| New intent, an unsettled product question, cost, permission, credentials, safety              | The operator, through the Director's structured question                                         |

Nothing on the Change board needs the operator: priority, Frame attestation, Slice confirmation and abandonment are the Director's. The operator acts on safety-critical matters, and on questions that add intent.

</decision_map>

<operator_questions>

- Ask the operator one question at a time through the structured-question tool, with the exact passage and link, after every action that does not depend on the answer.
- Establish first whether a proposed change is feasible; never ask the operator to answer a Change it has not read.
- Before pointing the operator at a position's pane, ask whether the operator is available now. An unanswered question takes a position out of service.
- Never ask the operator to act in a herdr pane.

</operator_questions>

<lifecycle_skills>

Before ordering anything a lifecycle skill covers, use that skill; each states its own procedure and outranks orders:

- Use skill `spec-tree:claim-change` for a Claim, the checkout of the Handoff's branch and the sync.
- Use skill `spec-tree:release-change`; only the winning claimant releases, and it checkpoints uncommitted work, pushes, and writes a five-line Handoff.
- Use skill `spec-tree:close-change` for Applied, Refined or Abandoned with their preconditions.
- Use skill `spec-tree:merge`; it is the only route to the default branch.

Read each node's malleability in its spec's front matter before ordering or reporting any evidence audit; use skill `spec-tree:understand` for the gates a malleability selects.

</lifecycle_skills>
