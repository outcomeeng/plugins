# Officer order template

## Contents

- [Identity and frozen subject](#identity-and-frozen-subject)
- [Operator words](#operator-words)
- [Frame and build constraints](#frame-and-build-constraints)
- [Delegation contract](#delegation-contract)
- [Round ceiling](#round-ceiling)
- [Verification reuse](#verification-reuse)
- [Standing rules](#standing-rules)
- [Change lifecycle](#change-lifecycle)
- [Reporting cadence](#reporting-cadence)

Copy this template into one durable `order` record. Replace every placeholder.
An unfilled field refuses the order.

## Identity and frozen subject

- Change: `<repository#number and complete Change title>`
- Activity: `<exact Activity identifier and text>`
- Officer mail identity: `<registered store-assigned word-list name>`
- Officer permission posture: `<the disallowed-tools argument the launch carried
  on this officer's session, or the recorded absence of such an argument on this
  officer's agent surface>`
- Exact inbox instruction: `<verbatim instruction supplied by the orchestrating session for this repository's mail project>`
- Mail correlation: `<stable per-Change correlation>`
- Absolute worktree: `<absolute path>`
- Worktree proof: `<checked free-pool or occupancy result>`
- Branch: `<complete branch ref>`
- Frozen HEAD: `<full commit SHA>`
- Verifier changeset selector: `origin/<base>...HEAD`

`<base>` is the active flow's resolved changeset base. For a pull request, use
its checked `baseRefName`; otherwise use the base the governing flow resolved.

The permission posture is recorded here, never requested here: starting the
session set it, as the launch workflow's `<permission_posture>` states. An order
that asks an officer not to reach for a tool the session still carries does not
hold.

The repository has one mail project, identified by that repository, so an
identity registered in it is valid for every checkout of that repository and is
registered once rather than per checkout. Descriptive agent names can be
rejected by the store; use its accepted word-list name and require the officer
to report that effective name before sending this order.

## Operator words

> `<operator's words copied verbatim>`

Do not paraphrase, extend, or silently narrow this text.

## Frame and build constraints

- Governing Change Frame: `<complete Frame text or authoritative reference>`
- Owned paths and mutations: `<exact paths and external mutations>`
- Required skills: `<complete list>`
- Required deterministic commands: `<complete commands and bounds>`
- Worktree ownership: `the officer owns the assigned worktree while this order
  stands and is accountable for what it does there; every file operation inside
  it, removal included, is open to the officer`
- Forbidden actions: `<complete prohibitions this Change's Frame or the
  operator's words impose>`
- Completion condition: `<exact committed and verification state>`

`Forbidden actions` carries only what this Change's Frame or the operator's
words prohibit. It never carries a standing prohibition on removing a file: the
officer owns the assigned worktree, a removal there loses nothing another
session holds and nothing Git cannot restore, and the worktree-ownership field
above states that positively so no order can invert it.

## Delegation contract

- Officer role: `Executor`
- Author: `<configured Author definition and fresh subagent session>`
- Verifiers: `<configured Verifier definitions, each in a separate fresh subagent session>`
- Fixer: `<fresh session of the Author definition, launched only after a rejected verdict>`
- Activity facts: `<each fact names the subagent sessions that performed the work>`
- Officer authoring boundary: `The officer authors, audits, reviews, and fixes nothing itself.`
- Concurrent integration: `the Executor may commit the Fixer's work while that
  Fixer still runs, so a Fixer that observes a commit carrying its own files made
  no error and never touches history to undo it`

## Round ceiling

- Round ceiling: `the round definition, autonomous ceiling, second-rejection
  procedure, and third-round rule stated in the skill's <round_control>`
- Repeated-class hard stop: `a new finding of a class already repaired twice on the same subject stops the officer and releases the Change with a Handoff`

The skill's `<round_control>` states the round definition, the autonomous
ceiling, the second-rejection procedure, and the third-round rule. Fill the
first field by citing it, never by restating its values, so one authored
statement governs all four. The repeated-class hard stop is this template's own
and is stated here in full.

## Verification reuse

- Byte-identical reuse: `a Verifier verdict already reached on a byte-identical
  subject is reused and never re-dispatched`
- Rebase preservation: `after a rebase, that reuse holds only when the
  repository's preservation proof establishes an unchanged branch diff and an
  unrelated base movement, together with every further condition the
  repository's merge overlay declares; absent that proof the verdict is
  re-dispatched`
- Base-delta validation: `the narrower validation the base delta requires is
  run whatever the preservation proof permits to be reused`

The verification-reuse intent is stated here in full rather than left to the
standing authority recorded below, so every filled order carries it.

## Standing rules

- Standing authority: `<the orchestrating-session standing rules in force for
  this order, recorded as the authority governing the officer's execution>`

When a checked store observation proves records exist after the adapter inbox
returned zero, every bell line to the officer carries the message id and the
orchestrating session's read-only authorization for the store's exact inbox
command. The bell is a pointer and authorization only; it never carries the
order text.

## Change lifecycle

- Terminal completion: `order /close-change Applied`
- Continuation remaining on a held nonterminal Change: `order /release-change`
  with a Handoff naming the completed and next Activities, blockers, and
  hazards
- Session lifecycle: `after a validated durable lifecycle-result fact reports
  that the Change operation succeeded, stop the officer and relaunch the same
  agent kind in the same pane before its next order`
- Lifecycle result report: `after the Change operation succeeds, mail one fact
  carrying the standing rules' officerLifecycleResult object with the exact
  Change, triggering order store id, operation, status, resulting lifecycle,
  and complete Handoff when releasing; order delivery alone never permits the
  orchestrating session to stop`

## Reporting cadence

- Immediate facts: `<events that require a message as they occur>`
- Operator cadence: `<named cadence or none>`
- Commit report: `mail every full commit SHA before compaction`
- Verdict report: `mail every verdict and complete verification run identity before compaction`
- Quiet-read rule: `an unchanged read produces no report unless the operator requested one`
- Escalation shape: `evidence, consequence, options, one recommendation`
