---
name: orchestrate-officers
description: >-
  ALWAYS invoke this skill when one operator-facing session supervises officer sessions that each execute one Change through herdr and agent-mail. NEVER supervise those officers by constructing environment or mail commands directly.
argument-hint: "<operator request or officer event>"
allowed-tools: Read, "{{! tool('use_skill') !}}", Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/derive_ledger.py":*)
---

<objective>
A supervised officer fleet whose Changes advance through bounded, durable,
event-driven execution while the operator uses one session, one inbox, and one
pane.
</objective>

<capabilities>

Use only these two operational capabilities:

- `coding-agents:operate-herdr` for inventory, read, bounded wait, prompt,
  start, relaunch, stop, and other pane operations it owns
- `coding-agents:operate-agent-mail` for registration, message records, inbox
  reads, and receipts

Pass semantic requests to those skills and preserve their complete results.
Neither infer nor reproduce their underlying command grammar. This skill has no
daemon, watcher, or polling loop.

</capabilities>

<required_references>

Read `${CLAUDE_SKILL_DIR}/references/officer-order.md` before preparing an
officer's launch prompt or order. Read
`${CLAUDE_SKILL_DIR}/references/standing-rules.md` before the first fleet
operation and again after compaction or restart.

</required_references>

<workflow>

Interpret `$ARGUMENTS` as the operator request or officer event and select the
one operation it names. When `$ARGUMENTS` is empty or names several operations,
return an invalid-invocation result that lists the eight accepted operations.
Carry out exactly one of these eight operations for each invocation, then
return to the event boundary.

1. **Launch.** Use `coding-agents:operate-herdr` to inventory the environment.
   Require the exact absolute worktree, frozen full HEAD, and an existing free
   pane before starting an officer. A linked worktree is prepared outside this
   skill; do not request a workspace open for it. Start or relaunch the officer
   in the proven pane. Deliver only the launch prompt, naming the Change and the
   store-safe word-list mail name the officer must register. Use one bounded
   wait for the registration fact. Stop the pane when registration is not
   proven within that bound.
2. **Order.** Refuse an order with any unfilled template field, an unproven
   worktree, or an unregistered mail identity. Use
   `coding-agents:operate-agent-mail` to send the complete order as one `order`
   record. Record its store identity in the per-Change ledger.
3. **Read.** Read only after a message, an officer state change, a crossed
   bound, or an operator-named cadence. Use the inbox capability for message
   records and the environment capability for a relevant pane state. Rebuild
   the ledger from those records and sealed verification-journal data after
   every compaction or restart. A read with no state change produces no report
   unless the operator requested one.
4. **Correct.** Treat the skill invocation as standing authorization only for
   panes launched by this skill. Read the officer's pane before repeating a
   stalled prompt. Answer a guarded prompt only when the latest officer fact
   establishes that the action is the next step in its governing flow. Dismiss
   an unexpected prompt and remove its cause. Do not send an interrupt while a
   Verifier pass runs.
5. **Answer.** Decide questions whose answer is already fixed by loaded skills,
   decisions, specs, and checked state. Send the decision and its evidence as
   an `answer` record. Write an unresolved decision in this orchestrating
   session's pane under the autonomy rules in the standing-rules reference.
6. **Escalate.** Lead with evidence, consequence, options, and one
   recommendation. Hold only the affected decision; continue every independent
   officer. Apply the autonomous and operator-held decision classes exactly as
   the standing-rules reference defines them.
7. **Housekeep.** Compact an officer idle beyond the declared bound, relaunch an
   officer whose session ended, and report every officer by absolute worktree
   and Change. Keep the officer's internal state and verification run
   identities with that officer. Mail each commit and verdict before any
   compaction.
8. **Close.** Close an officer whose Change is Applied. After release, order the
   release through mail, stop the session through
   `coding-agents:operate-herdr`, and relaunch the agent in the same pane before
   the next order so it loads the current plugin catalog.

</workflow>

<round_control>

One round is one Author or Fixer pass plus every Verifier pass it triggers. Run
at most two rounds for one Change without the operator's word. On a second
rejection, require the repeated-class check, the pushed changeset, the sealed
journal runs, and a split, track, or stop proposal. Decide that proposal only
under the standing autonomy rules. A third round waits for the operator.

</round_control>

<ledger_derivation>

The bundled entry point accepts one JSON document with this source-owned
shape:

```json
{
  "schemaVersion": 1,
  "change": "owner/changes#123",
  "mailRecords": [],
  "journalRuns": []
}
```

Each mail record preserves the store's `id` and string `body`. A JSON body with
a `ledger` object contributes its declared fields; other bodies remain durable
mail facts without entering the numerical ledger. Each journal object preserves
its `runId`. Submit the document through one of these forms and preserve the
complete result.

When the shell accepts multiline input:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/derive_ledger.py" derive <<'JSON'
{"schemaVersion":1,"change":"owner/changes#123","mailRecords":[],"journalRuns":[]}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"schemaVersion":1,"change":"owner/changes#123","mailRecords":[],"journalRuns":[]}' | python3 "${CLAUDE_SKILL_DIR}/scripts/derive_ledger.py" derive
```

Accept only `schemaVersion: 1` with `status: "succeeded"`. The ledger carries
exactly `change`, `passes`, `heads`, `verdicts`, `findingProvenance`, `reads`,
`runningSpend`, and `wallTimeSeconds`, with source provenance on every event.

</ledger_derivation>

<script_validation>

The ledger entry point is tested with these inputs and results:

- sample input `{"schemaVersion":1,"change":"owner/changes#123","mailRecords":[],"journalRuns":[]}` exits zero and writes the versioned succeeded result with the complete empty ledger
- invalid input `{"schemaVersion":2,"change":"owner/changes#123","mailRecords":[],"journalRuns":[]}` exits two and writes `status: "invalid-input"` with the required-version detail
- malformed JSON exits two and writes the deterministic invalid-input result
- the entry point reads stdin and writes stdout and stderr only; successful and invalid runs create no temporary files, so cleanup leaves no path behind

</script_validation>

<result>

Return the operation, the complete officer identity, absolute worktree, Change,
triggering event, capability results, ledger change, and next event boundary.
Spend and wall time are courtesy fields rather than gates. Preserve complete
session, message, commit, and verification-run identities.

</result>

<success_criteria>

- Every officer has one proven worktree, pane, Change, and registered mail
  identity before receiving an order.
- Every order and result is durable in agent-mail, and the ledger can be rebuilt
  from message records and sealed verification-journal data.
- Reads are event-driven or operator-scheduled, all waits are bounded, and an
  unchanged read stays quiet unless the operator requested a report.
- The two-round ceiling, autonomy boundary, reuse rule, lifecycle ownership,
  and fresh-session-after-release rule remain in force across compaction and
  restart.

</success_criteria>

<failure_modes>

**Claude opened an existing linked worktree.** The environment capability can
reject an open request for a linked worktree that already exists. Prove the
worktree and pane before launch, then start the officer in that pane without an
open request.

**Claude treated a submitted first prompt as active work.** A fresh session can
accept its first prompt without beginning the task. Read the pane before
submitting a second prompt, and repeat only when the launch text is absent.

**Claude reused a stopped officer session.** Stop closes both the pane and the
session it contains. Relaunch the selected agent in a proven pane before the
next order.

**Claude treated an empty adapter inbox as an empty store.** The adapter can
return zero rows while the store contains records. Use only the Captain's
explicit read-only store instruction for that project until the recorded
adapter defect is repaired; never derive a raw store command.

</failure_modes>
