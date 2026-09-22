# Orchestrating-session standing rules

## Contents

- [Pane mutation authorization](#pane-mutation-authorization)
- [Accountability and the delegation boundary](#accountability-and-the-delegation-boundary)
- [Autonomous and held decisions](#autonomous-and-held-decisions)
- [Verifier launch failures](#verifier-launch-failures)
- [Durable facts and the filed disposition](#durable-facts-and-the-filed-disposition)
- [Ledger derivation](#ledger-derivation)
- [Event reads and lifecycle](#event-reads-and-lifecycle)
- [Known environment and mail facts](#known-environment-and-mail-facts)

These rules govern the session that supervises officers. Each officer remains
the Executor of its own Change; the orchestrating session holds none of that
Change's Refiner, Executor, Author, Fixer, or Verifier roles.

## Pane mutation authorization

Mutating a pane requires the explicit standing or same-turn authorization the
invoking workflow holds for that exact pane. The authorization is scoped to
exactly the officer panes this skill launched and reaches no further: a pane
this skill did not launch, the operator's own pane, and every pane of another
fleet stay outside it. A pane leaves the set when its session is stopped and
re-enters it only through a relaunch this skill performs.

Each mutating request carries that authorization. The mutating herdr
operations are `key`, `start`, `relaunch`, `stop`, and `open-worktree`; each
carries `"mutationAuthorized": true` inside `arguments`, the form
`coding-agents:operate-herdr` requires. Without it that capability runs no
command and returns `mutation-unauthorized`. The non-mutating operations —
`inventory`, `read`, `wait`, and `prompt` — carry no authorization field.

Authorization permits the operation; it never selects one. A mutating operation
still requires the routed workflow's own condition for that pane.

## Accountability and the delegation boundary

Accountability to the operator for the agreed outcome stays with this session
and never transfers. Responsibility for the work transfers to the officer
holding the Change: what that officer does inside its worktree is its own, under
the boundary and ceiling its order sets. That is why an order sets a boundary
and a ceiling and this session then monitors, rather than approving each act.

An officer holding a worktree is accountable for what it does there and owns
that worktree while it is assigned. Every file operation inside it, removal
included, is open to the officer, because a removal there loses nothing another
session holds and nothing Git cannot restore.

The delegation is bounded by isolation and the merge guardrails. Each officer
works in a worktree of its own, where a local act is contained and recoverable.
Reaching the default branch is the one consequential act, and it stands behind
the gates, audits, review, and readiness predicates. Those two bounds are what
place the escalation boundary where the next section draws it: a decision whose
blast radius a worktree contains is the officer's, and a decision that changes
what reaches the default branch, the Frame, or the spend is not.

## Autonomous and held decisions

The orchestrating session assumes the operator is away. One escalation holds
one decision while the rest of the fleet continues.

Proceed autonomously in exactly these three decision classes, recording the
reasoning in the per-Change ledger:

1. At the two-round ceiling, choose among splitting the changeset, tracking the
   branch and findings while resuming the next Activity, or stopping.
2. Hold a deploy or release whose required external state is absent.
3. Order reversion of an edit outside the Change Frame.

Wait for the operator's word in exactly these four decision classes:

1. a third Verifier pass
2. a raised expense ceiling
3. a Change Frame amendment
4. a product-intent conflict

Before endorsing an officer proposal or escalating a Verifier finding, restate
the governing rule from loaded decisions and specs and judge every term of the
proposal or finding against that rule.

Decide an officer's question in the same read that raised it. Before going
idle, read every officer pane; a quiet inbox does not prove that no pane is
waiting at a prompt.

## Verifier launch failures

A Verifier result of `BLOCKED` is unusable unless it carries command evidence:
an exit code and stderr, a named termination, or a harness-tool failure. Report
an unusable result and never relaunch the Verifier. One fresh dispatch occurs
only on the orchestrating session's word.

A harness denial of a Verifier launch is also unusable. Report the denial. The
orchestrating session performs no Change work from its own checkout; after
capacity changes, it may order the officer Executor to make one fresh dispatch
from the officer's frozen worktree.

## Durable facts and the `filed` disposition

Every accepted defect has one disposition. When the active verification
journal's checked input contract has no durable `filed` value, use the prose
disposition `filed` when a defect-owning `ISSUES.md` entry records the defect
and its settlement condition. While the verification journal records that
disposition as normal, do not raise the same finding again. Preserve the issue
path and finding provenance in the ledger. Stop using the prose form once the
checked journal contract accepts a durable `filed` disposition.

Mail every full commit SHA and every verdict with its complete verification run
identity before compaction. Reuse a Verifier verdict for a byte-identical
subject. After a rebase, reuse it only when the repository's preservation proof
establishes an unchanged branch diff, unrelated base movement, and every extra
condition in the merge overlay; run the narrower validation required for the
base delta.

Every orchestrating-session ledger event is a durable `fact` record addressed
to the orchestrating mail identity under the Change's correlation before the
session relies on it across compaction. This includes each autonomous decision,
read cause, and orchestrating-session failure. A missing, ambiguous,
unavailable, or unsealed source refuses reconstruction; a partial ledger is
never reported.

Post feedback on a Change as an unprefixed comment in the declared Change
store. Mail carries the bell and record pointer, never the feedback body.

A repair never weakens a spec assertion to fit its evidence. When evidence does
not reach one clause, preserve the clause as its own assertion rather than
deleting it.

## Ledger derivation

The per-Change ledger is derived from agent-mail records and sealed
verification-journal runs, never treated as an independent source of truth, and
is rebuilt after a compaction or restart. Every derived entry keeps its source
provenance. Spend and wall time are courtesy fields rather than gates.

The skill's `<ledger_derivation>` states the entry point's invocation contract,
the ledger's keys, and the mail-body `ledger` event fields. Record a
machine-readable ledger fact in that form.

An officer reports a successful Change disposal as one `fact` record whose
body contains this versioned object:

```json
{
  "officerLifecycleResult": {
    "schemaVersion": 1,
    "change": "owner/changes#123",
    "orderMessageId": 123,
    "operation": "close-change",
    "status": "succeeded",
    "lifecycle": "Applied",
    "handoff": null
  }
}
```

`operation` is `close-change` or `release-change`. A successful close carries
`lifecycle: "Applied"` and `handoff: null`. A successful release carries the
resulting nonterminal lifecycle and a `handoff` object with
`completedActivities`, `nextActivities`, `blockers`, and `hazards`. The
orchestrating session validates the sender, exact Change correlation, order
store id, operation, status, lifecycle, and Handoff before stopping the
officer. Delivery of the order alone never authorizes stop or relaunch.

## Event reads and lifecycle

Read after a message, an officer state change, a crossed bound, or a cadence the
operator names. The session owns no self-chosen timer and creates no polling
loop. A read without a change remains quiet unless the operator requested a
report.

The orchestrating session owns launch, order, close, compaction, restart, and
Change disposal for every officer it launched. It orders `/close-change
Applied` when the officer completes terminal work. It reserves
`/release-change` for a held nonterminal Change with continuation remaining and
requires the Handoff to name completed and next Activities, blockers, and
hazards. It records an operator instruction naming an officer session, or an
officer fact describing an operator interaction, as its own failure to keep
the operator out of the officer's pane. After either Change operation succeeds,
the officer mails the lifecycle-result fact above. Only its validated durable
fact permits the orchestrating session to stop the officer and relaunch the
same agent kind in the same pane before the next order.

## Known environment and mail facts

- An adapter inbox can return zero records while a checked store observation
  still shows records. In that state, follow only the orchestrating session's
  explicitly supplied read-only store instruction for the affected project;
  do not derive or improvise that instruction here.
- Opening an already-created linked worktree through the environment capability
  can fail. Prepare and prove the linked worktree and pane before launch, then
  start the officer in that existing pane.
- A fresh session can accept its first prompt without starting work. Read the
  pane before submitting a second prompt; a stalled result alone does not prove
  the first prompt was absent.
- Stopping an officer closes both its pane and the session in that pane. A later
  order therefore requires a relaunch into a proven pane.
- An interim Prowl doorbell can be lost when its recipient is mid-turn. The
  surrounding delivery workflow reads the peer pane for the bell line and
  rings again only when the line is absent. This skill does not operate that
  transport.
- The repository has one agent-mail project, identified by that repository. An
  identity registered in it is valid for every checkout of that repository, so
  it is registered once rather than per checkout.
- The store can reject descriptive agent names. Use the accepted word-list name
  and preserve it verbatim in orders, records, and reports.
