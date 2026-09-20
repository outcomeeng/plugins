# Officer order template

Copy this template into one durable `order` record. Replace every placeholder.
An unfilled field refuses the order.

## Identity and frozen subject

- Change: `<repository#number and complete Change title>`
- Activity: `<exact Activity identifier and text>`
- Officer mail identity: `<registered store-assigned word-list name>`
- Exact inbox instruction: `<verbatim instruction supplied by the orchestrating session for this pool>`
- Mail correlation: `<stable per-Change correlation>`
- Absolute worktree: `<absolute path>`
- Worktree proof: `<checked free-pool or occupancy result>`
- Branch: `<complete branch ref>`
- Frozen HEAD: `<full commit SHA>`
- Verifier changeset selector: `origin/<base>...HEAD`

`<base>` is the active flow's resolved changeset base. For a pull request, use
its checked `baseRefName`; otherwise use the base the governing flow resolved.

Each worktree pool has its own mail project. Registration in another pool does
not establish an identity here. Descriptive agent names can be rejected by the
store; use its accepted word-list name and require the officer to report that
effective name before sending this order.

## Operator words

> `<operator's words copied verbatim>`

Do not paraphrase, extend, or silently narrow this text.

## Frame and build constraints

- Governing Change Frame: `<complete Frame text or authoritative reference>`
- Owned paths and mutations: `<exact paths and external mutations>`
- Required skills: `<complete list>`
- Required deterministic commands: `<complete commands and bounds>`
- Forbidden actions: `<complete prohibitions>`
- Completion condition: `<exact committed and verification state>`

## Delegation contract

- Officer role: `Executor`
- Author: `<configured Author definition and fresh subagent session>`
- Verifiers: `<configured Verifier definitions, each in a separate fresh subagent session>`
- Fixer: `<fresh session of the Author definition, launched only after a rejected verdict>`
- Activity facts: `<each fact names the subagent sessions that performed the work>`
- Officer authoring boundary: `The officer authors, audits, reviews, and fixes nothing itself.`

## Round ceiling

- Round definition: `one Author or Fixer pass plus every Verifier pass it triggers`
- Autonomous ceiling: `two rounds`
- Third-round rule: `wait for the operator's word`
- Second-rejection procedure: `report the repeated finding class, read the pushed changeset, read the sealed verification-journal runs, and propose split, track, or stop`
- Repeated-class hard stop: `a new finding of a class already repaired twice on the same subject stops the officer and releases the Change with a Handoff`

## Standing rules

Attach the current orchestrating-session standing rules from
`${CLAUDE_SKILL_DIR}/references/standing-rules.md`, including the autonomy
table, judgment step, `filed` disposition, ledger derivation, event-read rule,
verdict reuse rule, release lifecycle, and known transport facts. The order
records that reference as standing authority for the officer's execution.

Until the agent-mail inbox defect tracked in the consumer repository's declared
Change store is settled, every bell line to the officer carries the message id
and the orchestrating session's read-only authorization for the store's exact
inbox command. The bell is a pointer and authorization only; it never carries
the order text.

## Change lifecycle

- Terminal completion: `order /close-change Applied`
- Continuation remaining on a held nonterminal Change: `order /release-change`
  with a Handoff naming the completed and next Activities, blockers, and
  hazards
- Session lifecycle: `after either Change operation succeeds, stop the officer
  and relaunch the same agent kind in the same pane before its next order`

## Reporting cadence

- Immediate facts: `<events that require a message as they occur>`
- Operator cadence: `<named cadence or none>`
- Commit report: `mail every full commit SHA before compaction`
- Verdict report: `mail every verdict and complete verification run identity before compaction`
- Quiet-read rule: `an unchanged read produces no report unless the operator requested one`
- Escalation shape: `evidence, consequence, options, one recommendation`
