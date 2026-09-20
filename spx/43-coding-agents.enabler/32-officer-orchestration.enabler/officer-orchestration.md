---
id: 01a0b229-e719-7fe9-903c-d357d04d1384
malleability: spec
---

# Officer Orchestration

PROVIDES the supervision contract of an orchestrating agent session — launch, order, read, correct, answer, escalate, housekeep, and close — over officer sessions that each execute one Change
SO THAT an operator
CAN run a fleet of coding agents through one session, one inbox, and one pane, never opening an officer's

The orchestrating session is an agent session that holds none of the five Roles — Refiner, Executor, Author, Fixer, Verifier — for any Change an officer executes; it stands in for the operator toward the officers and owns each officer session's lifecycle, never the officer's work.

## Assertions

### Scenarios

- Given empty durable source records for a named Change, when the ledger derivation entry point executes, then its versioned result has the complete minimum ledger shape with empty passes, heads, verdicts, finding provenance, reads, running spend, and zero wall time [test](tests/test_ledger_derivation.scenario.l1.py)

### Compliance

- ALWAYS: the orchestrating session launches every officer into a herdr pane through `spx/43-coding-agents.enabler/18-herdr-environment.enabler`, the one officer environment, delivers the launch prompt that names the Change and the mail name the officer registers under, and delivers every later order as a message record of `spx/43-coding-agents.enabler/18-agent-mail.enabler`; an order with an unfilled field or an unproven worktree is refused, an officer without a mail identity receives only the launch prompt, and one that has not registered within the bounded wait is stopped [probe](probes/officer-run/probe.md)
- ALWAYS: the officer is the Executor of its Change and each Activity fact names the subagent sessions that did the work [probe](probes/officer-run/probe.md)
- ALWAYS: the officer order's delegation contract names the Author, every Verifier, and a fresh session of the Author's definition as Fixer, all as subagent sessions [audit]
- NEVER: a third round — one Author or Fixer pass with every Verifier pass it triggers — runs on one Change without the operator's word; the second rejected round produces the repeated-class check, a reading of the pushed changeset, a reading of the sealed journal runs, and a split, track, or stop proposal to the orchestrating session, which decides it under the autonomy the assertions below declare [probe](probes/officer-run/probe.md)
- ALWAYS: the operator's invocation of the orchestrating skill is the standing authorization for the panes of the officers it launched; the skill sets mutation authorization for those panes only, answers a prompt when the officer's latest fact shows the guarded action is its flow's next step, dismisses a prompt with no such fact and removes its cause, and never sends an interrupt while a Verifier pass runs [probe](probes/officer-run/probe.md)
- ALWAYS: reads happen on events — a message, an officer state change, a bound crossed — or on a cadence the operator names, never on a timer of the session's own; a read without a change produces no report unless the operator asked for one [probe](probes/officer-run/probe.md)
- ALWAYS: the per-Change ledger — passes, heads, verdicts, finding provenance, reads with their cause, running spend and wall time — is a derivation from the message records and the verification journal, rebuilt from those sources after a compaction or restart, and spend and wall time are reported as a courtesy, never as a gate [probe](probes/officer-run/probe.md)

- ALWAYS: the orchestrating session compacts an officer idle past the bound, restarts one whose session is gone, and closes one whose Change is Applied without an operator instruction; after release, it orders /release-change, stops the session through the herdr capability, and relaunches the agent in the same pane before the next order [probe](probes/officer-run/probe.md)
- ALWAYS: lifecycle operations leave the officer responsible for its internal state, run identities, results, and workflow continuation, while an operator instruction naming its session or an officer fact reporting an operator interaction is recorded in the ledger as a failure of the orchestrating session to keep the operator out of that officer's pane [audit]
- ALWAYS: officers are reported by their absolute worktree path and Change, every escalation leads with evidence, consequence, options, and one recommendation, what loaded truth settles is decided in the session, and the rest is written as text in the orchestrating session's own pane, never raised through a structured question [probe](probes/officer-run/probe.md)
- ALWAYS: the orchestrating session assumes the operator is away; an escalation holds only its decision and never the fleet, and exactly three decisions proceed autonomously with their reasoning recorded in the ledger: at the two-pass ceiling, split the changeset, track the branch and findings while resuming the next Activity, or stop; hold a deploy or release blocked by external state; and order reversion of an edit outside the Frame. A third Verifier pass, a raised expense ceiling, a Frame change, and a product-intent conflict wait for the operator's word without exception [probe](probes/officer-run/probe.md)
- ALWAYS: before endorsing an officer proposal or escalating a Verifier finding, the orchestrating session restates the governing rule from loaded decisions and specs and judges every term against it [audit]
- ALWAYS: every order carries the standing rule that a Verifier verdict on a byte-identical subject is reused and never re-dispatched, and that after a rebase reuse is permitted only when the preservation proof in `spx/15-merging.pdr.md` establishes that the branch diff is unchanged and the base movement is unrelated, and any further condition the repository's merge overlay declares holds, with the base delta's narrower validation still run; every commit and verdict is mailed before compaction [probe](probes/officer-run/probe.md)
- ALWAYS: the officer order template carries the complete reuse, rebase-preservation, narrow-validation, commit-and-verdict-mail, release, stop, and fresh-session-relaunch intent [audit]
