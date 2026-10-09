<overview>

Who decides what across the positions. Read it before routing any question, block or decision.

</overview>

<positions>

Positions are named `{Product} {Position}`; the Director takes no product. Ranked highest first, the highest rank wins a conflict:

| Rank | Position     | Holds                                                                                                         |
| ---- | ------------ | ------------------------------------------------------------------------------------------------------------- |
| 1    | Director     | Order across products, the operating model, the board and the general override                                |
| 2    | Maintainer   | One product's context; refinement of its Changes; its priority, Frame and Slice backlogs; abandon attestation |
| 3    | Contributor  | Refinement and delivery of instruction-only Changes, without an Executor; studies and defect analysis         |
| 4    | Orchestrator | Delivery mechanics: worktree, branch and salvage preparation, Executor start and checks                       |
| 5    | Executor     | One claimed Executable Change through `/execute-change`                                                       |

The Advisor holds the outside view. It reads Changes with a cleared context and records verdicts only; it never contextualizes. Its review follows a Director decision in batches; a revise verdict reopens the decision.

A session that holds no position and no Orchestrator manages does no refinement: it pushes its branch, writes a Handoff on its Change, releases any Claim and ends.

</positions>

<decision_map>

| Question or block                                                                             | Owner                                                                    |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| A question an ADR, PDR, the methodology or a recorded ruling settles                          | The Maintainer decides and cites it; never labelled an operator decision |
| Order, scope and slicing inside a direction the operator stated                               | The Maintainer                                                           |
| Priority, Frame attestation and Slice confirmation: the three Submitted backlogs              | The Maintainer of the Product                                            |
| Order across Products, the operating model and the board                                      | The Director                                                             |
| Delivery mechanics: worktree, branch, salvage, rebase, stray untracked file, round sequencing | The Orchestrator decides and reports after                               |
| Touched-file debt inside the Frame                                                            | The Executor's rounds fix it                                             |
| A finding that needs a record change                                                          | Delivery stops; the Maintainer revises the record in discovery           |
| New intent, an unsettled product question, cost, permission, credentials, safety              | The operator, through the Director's structured question                 |

Everything inside a Product runs without the Director and the operator: the Maintainer is autonomous there and the Contributor works under the Maintainer's mandate. The Director answers a position's question about its own Product with: the decision is yours. The operator acts on safety-critical matters and on questions that add intent, and holds the general override.

</decision_map>

<operator_questions>

- Ask the operator one question at a time through the structured-question tool, with the exact passage and link, after every action that does not depend on the answer.
- Establish first whether a proposed change is feasible; never ask the operator to answer a Change it has not read.
- Before pointing the operator at a position's pane, ask whether the operator is available now. An unanswered question takes a position out of service.
- Never ask the operator to act in a herdr pane.

</operator_questions>

<lifecycle_skills>

Read the lifecycle skill before ordering anything it covers; the skills state their own procedure and outrank orders:

- `spec-tree:claim-change` — Claim, checkout of the Handoff's branch, sync.
- `spec-tree:release-change` — only the winning claimant releases; it checkpoints uncommitted work, pushes, and writes a five-line Handoff.
- `spec-tree:close-change` — Applied, Refined or Abandoned with their preconditions.
- `spec-tree:merge` — the only route to the default branch.

Malleability lives only in a spec's front matter. A node's malleability selects its gates: `spec` needs Validate, reachability tests and a result for every tagged assertion; `verification` adds a result for every assertion; `implementation` adds evidence that passes audit. A changeset merges by the least malleable node it touches.

</lifecycle_skills>
