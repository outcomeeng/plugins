# Officer run

The protocol lives at `probes/officer-run/probe.md`, the target of each
behavioral assertion's `[probe]` tag. Working runs stay in an ignored `runs/`
inside this directory; every future attested run retains at least one
inspectable artifact beside this file.

## Intent

Exercise one ordinary officer lifecycle from launch through release and fresh
relaunch. The run addresses the risk that an orchestrating session performs an
officer's work, loses durable facts across compaction, reads on a self-chosen
timer, re-dispatches reusable verification, or keeps a stale session after
release.

## Environment and preconditions

- A released coding-agents plugin contains `/orchestrate-officers`,
  `/operate-herdr`, and `/operate-agent-mail` at the versions under evaluation.
- One executable Change has an exact Activity, Frame, frozen full HEAD,
  deterministic commands, and configured Author, Fixer, and Verifier
  definitions.
- One linked worktree is already created, proven free, and associated with an
  existing herdr pane; opening that linked worktree is outside the run.
- The repository has an available agent-mail store and a candidate store-safe
  word-list identity.
- The observer can retain mail-thread exports, herdr inventories, and the
  orchestrating session's pane transcript without editing them.

## Protocol

1. Capture the herdr inventory and frozen full HEAD. Invoke
   `/orchestrate-officers` with the Change, Activity, worktree, pane, operator
   words, order fields, and a bounded registration wait.
2. Observe that only the launch prompt reaches the unregistered officer. After
   the officer reports its effective registered mail identity, observe one
   complete order record and no order with an unfilled field.
3. Observe the officer act as Executor, delegate Author and Verifier work, and
   name the working subagent sessions in each Activity fact. Retain the
   corresponding mail records and verification-journal run identities.
4. Trigger one message event, one officer-state change, and one crossed bound.
   Observe one causally recorded read for each. Leave the officer unchanged for
   one additional read opportunity and observe no report.
5. Record one commit and one Verifier verdict. Compact or restart the
   orchestrating session, then rebuild the per-Change ledger from the exported
   mail records and sealed journal runs. Compare passes, full heads, verdicts,
   finding provenance, read causes, running spend, and wall time.
6. Present a byte-identical verified subject and observe verdict reuse without
   another Verifier dispatch. If the base moved, retain the preservation proof
   and narrower base-delta validation before accepting reuse.
7. Release the Change. Observe the release order, stop, and fresh relaunch in
   the same pane before the next order. Capture the final inventory and the
   complete new session identity.

## Attested run

- Date: pending a release containing `/orchestrate-officers`
- Observations: no run has been executed; no behavioral result is claimed
- Artifacts: none

## Verdict

No verdict. The protocol is authored for a future run after the skill is
released.

## Limitations

This protocol reaches exactly the assertions whose own `[probe]` tag names this
file. Every other assertion of the node is settled by the verification its own
tag names, which this protocol neither supplies nor withholds; the node spec is
the only authority on which assertions those are, and none of them is a
limitation of this protocol.

Within that reach, an ordinary run does not force these conditions, so an
assertion depending on one of them stays Declared after the run:

- a second rejected round and an attempted third pass on one Change
- the guarded, unexpected, stalled, and Verifier-time pane-prompt conditions
- each autonomous decision class and each operator-held decision class

No probe pin exists yet. A future run must retain, at minimum, the mail-thread
export, inventories before launch and after stop, the pane transcript, sealed
verification-journal run identities, and hashes for every retained artifact.
