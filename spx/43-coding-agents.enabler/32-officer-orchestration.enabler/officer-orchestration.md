---
id: 01a0b229-e719-7fe9-903c-d357d04d1384
malleability: spec
---

# Officer Orchestration

PROVIDES the supervision contract of an orchestrating agent session — launch, order, read, correct, answer, escalate, housekeep, and close — over officer sessions that each execute one Change
SO THAT an operator
CAN run a fleet of coding agents through one session, one inbox, and one pane, never opening an officer's

## Assertions

### Compliance

- ALWAYS: the orchestrating session launches every officer into a herdr pane through `spx/43-coding-agents.enabler/18-herdr-environment.enabler`, the one officer environment, delivers the launch prompt that names the Change and the mail name the officer registers under, and delivers every later order as a message record of `spx/43-coding-agents.enabler/18-agent-mail.enabler`; an order with an unfilled field or an unproven worktree is refused, an officer without a mail identity receives only the launch prompt, and one that has not registered within the bounded wait is stopped
- ALWAYS: the officer is the Executor of its Change; the order's delegation field names the Author, the Verifiers, and a fresh session of the Author's definition as Fixer, all subagent sessions, and each Activity fact names the subagent sessions that did the work
- NEVER: a third round — one Author or Fixer pass with every Verifier pass it triggers — runs on one Change without the operator's word; the second rejected round produces the repeated-class check, a reading of the pushed changeset, a reading of the sealed journal runs, and a split, track, or stop proposal
- ALWAYS: the operator's invocation of the orchestrating skill is the standing authorization for the panes of the officers it launched; the skill sets mutation authorization for those panes only, answers a prompt when the officer's latest fact shows the guarded action is its flow's next step, dismisses a prompt with no such fact and removes its cause, and never sends an interrupt while a Verifier pass runs
- ALWAYS: reads happen on events — a message, an officer state change, a bound crossed — or on a cadence the operator names, never on a timer of the session's own; a read without a change produces no report unless the operator asked for one
- ALWAYS: the per-Change ledger — passes, heads, verdicts, finding provenance, reads with their cause, running spend and wall time — is a derivation from the message records and the verification journal, rebuilt from those sources after a compaction or restart, and spend and wall time are reported as a courtesy, never as a gate
- ALWAYS: the orchestrating session compacts an officer idle past the bound, restarts one whose session is gone, and closes one whose Change is Applied without an operator instruction; an operator instruction that names an officer's session, or an officer fact reporting an operator interaction, is recorded in the ledger as a failure of the orchestrating session
- ALWAYS: officers are reported by their absolute worktree path and Change, every escalation leads with evidence, consequence, options, and one recommendation, what loaded truth settles is decided in the session, and the rest is raised to the operator through the structured question
