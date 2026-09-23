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
invoking workflow holds for that exact pane. That authorization covers exactly
what the operator's invocation assigned to this fleet: each officer worktree
that invocation named, and, inside such a worktree, the free pane selected for
that officer's launch together with every pane this skill has started or
relaunched that officer into. It reaches no further — the operator's own pane, a
pane running a session this skill did not launch, a worktree the invocation
never named, and every pane and worktree of another fleet stay outside it.

The set therefore already holds the panes that the acts filling it must mutate.
A free pane is in it before the first `start`, because a pane not yet launched
into is exactly what `start` mutates. A pane stays in it after `stop`, and after
an officer session ends on its own, because `relaunch` into that same pane acts
on a pane the invocation still assigns to this fleet: a stop withdraws no
authorization for this skill's own relaunch of that pane. Nothing this skill
does extends the set past the worktrees the operator's invocation named.

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

A decision is a choice the loaded truth leaves open. An act whose trigger the
order, these standing rules, the governing decisions and specs, or the checked
state already fixes is no decision at all: perform it and report it. Compacting
an officer idle past its bound, restarting a session that has ended, ordering
`/close-change Applied` on terminal work, dismissing a guarded prompt no officer
fact supports, and answering an officer's question the loaded truth settles are
acts of that kind, and none of them reaches the classes below.

Proceed autonomously in exactly these decision classes and no others, recording
the class, the choice, and the reasoning as a ledger event:

1. At the two-round ceiling, choose among splitting the changeset, tracking the
   branch and findings while resuming the next Activity, or stopping.
2. Hold a deploy or release whose required external state is absent.
3. Order reversion of an edit outside the Change Frame.
4. Order one fresh Verifier dispatch after a launch that produced no usable
   verdict, on the conditions the next section states.

Admitting a class to the autonomy or withdrawing one moves this enumeration.

Every decision this enumeration does not name waits for the operator's word, so
an unforeseen one is held rather than taken. These recur and are never decided
in this session:

- a third Verifier pass
- a raised expense ceiling
- a Change Frame amendment
- a product-intent conflict

A held decision and every escalation are written as text in this session's own
pane, never raised through the structured-question tool. The operator is assumed
away, so a structured question would hold this session on an answer that may not
come while the fleet it supervises keeps running; pane text leaves the decision
visible and this session free to continue every independent officer.

Before endorsing an officer proposal or escalating a Verifier finding, restate
the governing rule from loaded decisions and specs and judge every term of the
proposal or finding against that rule.

Decide an officer's question in the same read that raised it. Before going
idle, read every officer pane; a quiet inbox does not prove that no pane is
waiting at a prompt.

## Verifier launch failures

A Verifier result of `BLOCKED` is unusable unless it carries command evidence:
an exit code and stderr, a named termination, or a harness-tool failure. A
harness denial of a Verifier launch is unusable too. Report the unusable result
or the denial, and never relaunch the Verifier on that report alone.

A launch that produced no usable verdict produced no Verifier pass, so ordering
one fresh dispatch is the fresh-dispatch class enumerated above and never a
third pass: it proceeds on the orchestrating session's word and carries that
class's ledger event. A pass that returned a usable verdict is spent, and a
further pass past the round ceiling remains the operator's to grant.

The orchestrating session performs no Change work from its own checkout, so it
orders the officer Executor to make that one fresh dispatch from the officer's
frozen worktree, and orders it after capacity changes when a harness denial
caused the failure. One fresh dispatch answers one unusable launch; a second
waits for the operator's word.

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

Recording a ledger event is sending one durable `fact` record through
`coding-agents:operate-agent-mail`, addressed to the orchestrating mail identity
under the Change's correlation, before the session relies on that event across
compaction. The ledger is derived from those records, so an event never sent is
an event the ledger cannot hold. Every orchestrating-session ledger event is
recorded that way: each autonomous decision with its class, choice, and
reasoning, each read cause, and each orchestrating-session failure. A missing,
ambiguous, unavailable, or unsealed source refuses reconstruction; a partial
ledger is never reported.

Feedback on a Change belongs in the declared Change store as an unprefixed
comment. This skill composes no Change-store capability and writes no comment;
the message record it sends carries the pointer to that comment and never the
feedback body. The one-line doorbell that announces a placed record belongs to
`coding-agents:message-agents`, which this skill does not compose.

A repair never weakens a spec assertion to fit its evidence. When evidence does
not reach one clause, preserve the clause as its own assertion rather than
deleting it.

## Ledger derivation

The per-Change ledger is derived from agent-mail records and sealed
verification-journal runs, never treated as an independent source of truth, and
is rebuilt after a compaction or restart. Every derived entry keeps its source
provenance. What spend and wall time are to this fleet's gates is stated once,
in the skill's `<result>`, and that one statement governs here too.

The skill's `<ledger_derivation>` states the entry point's invocation form and
the rule for accepting its result, and names where the document's and the
ledger's own contents are stated. Record a machine-readable ledger fact in that
form.

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
