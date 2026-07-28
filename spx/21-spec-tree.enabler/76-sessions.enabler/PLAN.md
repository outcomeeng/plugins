# Plan: Sessions

Composition of this node is partial. `spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler`, `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler`, and `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler/30-claim-verification.enabler` exist. The handoff concerns and the pickup resumption concern still sit on this node's spec and are reserved below.

## Reserved index horizon

Indices below `32` are reserved for this decomposition, because the ordering evidence places every session concern ahead of `spx/21-spec-tree.enabler/76-sessions.enabler/32-session-skill-invocation.enabler` — that node declares the invocation surface for flags whose behavior the handoff and pickup concerns define.

| Address                                                                 | Status   |
| ----------------------------------------------------------------------- | -------- |
| `spx/21-spec-tree.enabler/76-sessions.enabler/15-session-store.enabler` | exists   |
| `spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler`       | reserved |
| `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler`        | exists   |

Within `spx/21-spec-tree.enabler/76-sessions.enabler/25-handoff.enabler`, reserve `20-closure.enabler`, `40-continuation-disposition.enabler`, `60-session-document.enabler`, and `80-closeout-report.enabler`. Within `spx/21-spec-tree.enabler/76-sessions.enabler/28-pickup.enabler`, `30-claim-verification.enabler` exists and `60-resumption.enabler` is reserved.

## Ordering evidence

| Predecessor                                                          | Basis                | Constraining contribution                                           | Successor                                                                                            | Required by                                                                                                                   | Consequence if absent                                                                                                               |
| -------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `13-handoff-persistence.adr.md`                                      | ADR constraint       | The `git_ref` anchor contract and its origin-branch validity rule   | `15-session-store.enabler`                                                                           | The `git_ref` derivation Scenarios and the explicit-work-branch refusal                                                       | The store records an anchor whose validity nothing governs                                                                          |
| `15-session-store.enabler`                                           | provider/consumer    | The `.spx/sessions/` store and the `spx session` command contract   | `25-handoff.enabler`, `28-pickup.enabler`, `32-session-skill-invocation.enabler`, `43-issue.enabler` | The handoff persistence precondition, the pickup checkout-currency rule, the declared queue reads, and the issue-filing write | Every consumer specifies behavior against a store and command contract with no definition in its context                            |
| `25-handoff.enabler`                                                 | provider/consumer    | The session document and the fields it carries                      | `28-pickup.enabler`                                                                                  | The `/contextualize` target-selection rule and the claim-reconciliation verdicts                                              | Pickup's target selection and claim reconciliation read `git_ref`, `next_step`, and `<nodes>`, which nothing in its context defines |
| `25-handoff.enabler`, `28-pickup.enabler`                            | provider/consumer    | Flag semantics for `--no-session`, `--prune`, and `--auto-continue` | `32-session-skill-invocation.enabler`                                                                | The `argument-hint` frontmatter rules and the `$ARGUMENTS` parsing rule                                                       | The declared invocation surface names flags whose behavior is undefined                                                             |
| `20-closure.enabler`                                                 | logical prerequisite | Whether closure may proceed at all                                  | `40-continuation-disposition.enabler`                                                                | The closure-thread partitioning rule                                                                                          | Thread continuation state is resolved before the precondition permitting closure is established                                     |
| `40-continuation-disposition.enabler`                                | logical prerequisite | Whether a session document exists for each thread                   | `60-session-document.enabler`                                                                        | The repository-derived-pointer rule and the external-state rule                                                               | Document shape governs a document whose existence is undecided                                                                      |
| `40-continuation-disposition.enabler`, `60-session-document.enabler` | provider/consumer    | The session ids and dispositions a closure produced                 | `80-closeout-report.enabler`                                                                         | The session-mechanics operator-actionable-rows rule                                                                           | The closeout reports ids and dispositions it cannot derive                                                                          |
| `30-claim-verification.enabler`                                      | provider/consumer    | The three-verdict reconciliation                                    | `60-resumption.enabler`                                                                              | The post-context evidence review and the five-way classification                                                              | Evidence review and classification consume verdicts nothing produces                                                                |

## Disposition checkpoint

Every sibling pair under this node, stated before any index was assigned. Files and directories share one numeric namespace here, so the decision records are siblings of the child nodes.

| Pair                                                                                                                               | Disposition         | Proving row                                                                                                |
| ---------------------------------------------------------------------------------------------------------------------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------- |
| `13-handoff-persistence.adr.md` -> `15-session-store.enabler`                                                                      | ordered             | ADR-constraint row                                                                                         |
| `15-session-store.enabler` -> `25-handoff.enabler`, `28-pickup.enabler`, `32-session-skill-invocation.enabler`, `43-issue.enabler` | ordered             | store provider/consumer row                                                                                |
| `15-session-store.enabler` <-> `21-compact-continuity.pdr.md`                                                                      | unordered           | none, and none needed: the store sits at the lower slot, which asserts nothing about the decision above it |
| `21-compact-continuity.pdr.md` -> `25-handoff.enabler`, `28-pickup.enabler`                                                        | ordered by position | the compaction rules constrain every session concern loaded after them                                     |
| `25-handoff.enabler` -> `28-pickup.enabler`                                                                                        | ordered             | session-document provider/consumer row                                                                     |
| `25-handoff.enabler`, `28-pickup.enabler` -> `32-session-skill-invocation.enabler`                                                 | ordered             | flag-semantics provider/consumer row                                                                       |
| every child -> `65-pickup-claim-verification.adr.md`                                                                               | unordered           | none, and none needed: a higher-index sibling constrains nothing below it                                  |

Two nodes at different indices with no ordering evidence are sound only where the lower slot asserts nothing about the higher one. Genuine independent peers take the same index.

## Assertion destinations

The 35 assertions remaining on `sessions.md` move as follows.

- `25-handoff.enabler/20-closure.enabler` — the harness command form for `spx session handoff` payload input; the linked-worktree detach sequence; the worktree-occupancy-claim preservation rule; the clean-and-pushed persistence precondition and its named bypass; the reflection read of `PLAN.md` and `ISSUES.md`; the closure precondition and its coordination-note blockers; the branch-ahead-of-base continuation rule; the node-less anchor option.
- `25-handoff.enabler/40-continuation-disposition.enabler` — the search before adding a continuation; the never-mutate rule; runtime-identity verification before filing; the completed-deliverable-with-unrelated-note rule; closure-thread partitioning; the never-omit-for-unfinished-work rule; zero-handoff closure; both `--no-session` rules; the no-automation-passes-the-flag rule.
- `25-handoff.enabler/60-session-document.enabler` — the `goal` and `next_step` frontmatter wording; repository-derived pointers; recorded external state; the never-a-retrospective rule.
- `25-handoff.enabler/80-closeout-report.enabler` — the operator-useful closeout fields, and the session-mechanics block's operator-actionable content.
- `28-pickup.enabler/60-resumption.enabler` — `/contextualize` target selection by priority; the post-context evidence review; the five-way classification; the `owned_elsewhere` stop; the no-surprises proposal. Checkout currency before presenting session detail already sits on `28-pickup.enabler` itself, because it constrains both children.

Cross-cutting assertions stay on this node: the three compact-continuity rules, governed by `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md`.

## Decision placement

`spx/21-spec-tree.enabler/76-sessions.enabler/13-handoff-persistence.adr.md`, `spx/21-spec-tree.enabler/76-sessions.enabler/21-compact-continuity.pdr.md`, and `spx/21-spec-tree.enabler/76-sessions.enabler/65-pickup-claim-verification.adr.md` stay at this node. Placement routes through a `/decompose` pass once the child boundaries exist on disk, so each decision is judged against real children rather than proposed ones.

## Worklist

1. Invoke `/understand`, then `/contextualize spx/21-spec-tree.enabler/76-sessions.enabler`.
2. Create `25-handoff.enabler` and its four reserved children, moving the assertions named above out of `sessions.md`. Count assertions before and after; the total across this node and its descendants stays at 59.
3. Create `28-pickup.enabler/60-resumption.enabler` and move its six assertions.
4. Resolve decision placement for the three decision records through `/decompose`.
5. Gate each written child with the spec auditor, then run the changeset review and ship through `/merge`.
