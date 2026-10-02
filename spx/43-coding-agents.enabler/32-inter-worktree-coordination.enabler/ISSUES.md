# Issues

## Eval run history is stale for the coordination-decision suite

The newest passing row for `evals/coordination-decision` (16/16, git SHA
`d15d5b8a77c97b1cc1660dec6a4652e0c15af71b`, 2026-08-28) is an ancestor of the
current head, and the declared producers differ from the ones that run scored:
`message-agents/SKILL.md` step 5 requires a matching `/operate-prowl plan-handback`
result before a production request, `operate-prowl/scripts/prowl_environment.py`
requires the handback `adapterPath` to equal the source-owned adapter path,
`message-agents/SKILL.md` routes doorbell resolution through the mail operations
`list`, `read`, and `acknowledge`, `coordinate-agents/SKILL.md` carries a changed
frontmatter line, and `prompt.md` is rematerialized from those producers. No passing run proves the node's `[eval]` assertions
against the current prompt and producers.

**Settlement condition**: one passing run of
`just eval spx/43-coding-agents.enabler/32-inter-worktree-coordination.enabler/evals/coordination-decision/eval.toml`
at default ceilings on a head that carries the current producers, with its row
committed to `history.jsonl`.

**Evidence**: `spec-tree:eval-evidence-auditor` finding `f-004` on head
`a65659114b99767b90b4d920550fff5dc0824794` during Change #76, whose prototype
boundary runs no eval; `spec-tree:eval-evidence-auditor` finding `f-004`, rule
`run-evidence`, severity `REJECT`, on head
`0e1e2b6fd8f6511d9971470286b7487f8fc165fe` during
[Change #132](https://github.com/outcomeeng/changes/issues/132), whose producer
edits regenerated `prompt.md`.

## The no-coordination cases do not enforce an empty message plan

The assertion that independent work with no overlap, dependency, shared
mutation, or correlated blocker maps to no coordination message is not enforced
by the cases that exercise it. In `independent-work-sends-nothing` (line 4 of
`evals/coordination-decision/cases.jsonl`) and
`different-blockers-do-not-correlate` (line 6), the expected `"messages": []`
is vacuous under `is_subset` in `outcomeeng_evals/grader.py`: an empty expected
list matches every actual list. The first case's `must_not_contain` forbids only
`ownership-proposal` messages and the second forbids no message kind, so a
verdict of `status: no-coordination, reason: independent` that carries a `fact`
message to the other participant passes both cases.

**Impact**: the suite can pass while the no-message assertion in
`inter-worktree-coordination.md` is unfulfilled, so a passing run is no
evidence for it.

**Settlement condition**: every case exercising the no-message assertion fails
on a verdict that carries any message, of any kind, to any participant.

**Evidence**: `spec-tree:eval-evidence-auditor` finding `f-002`, rule
`assertion-alignment`, severity `REJECT`, on head
`0e1e2b6fd8f6511d9971470286b7487f8fc165fe`.

## The shared-blocker case cannot tell one recovery fact from all of them

The assertion that shared blockers produce one operator action plus recovery
facts for every affected workflow is exercised only by
`shared-blocker-one-action-all-recovery-facts` (line 5 of
`evals/coordination-decision/cases.jsonl`). That case has two participants, one
of them the caller, so exactly one non-caller workflow is affected. A producer
that messages only the first non-caller affected participant passes it as well
as one that messages every affected participant.

**Impact**: the "every affected workflow" quantifier has no case that could
falsify it.

**Settlement condition**: a shared-blocker case with at least two non-caller
affected participants fails unless each of them receives the recovery facts.

**Evidence**: `spec-tree:eval-evidence-auditor` finding `f-003`, rule
`assertion-alignment`, severity `WARNING`, on head
`0e1e2b6fd8f6511d9971470286b7487f8fc165fe`.
