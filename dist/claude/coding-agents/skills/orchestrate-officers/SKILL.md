---
name: orchestrate-officers
description: >-
  ALWAYS invoke this skill when one operator-facing session supervises officer sessions that each execute one Change through herdr and agent-mail. NEVER supervise those officers by constructing environment or mail commands directly.
argument-hint: "<operator request or officer event>"
allowed-tools: Read, Skill, Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/derive_ledger.py":*)
---

<objective>
A supervised officer fleet whose Changes advance through bounded, durable,
event-driven execution, every officer pane reached only through this session.
</objective>

Use skill `coding-agents:operate-herdr`.

Use skill `coding-agents:operate-agent-mail`.

Use skill `spec-tree:project-run-journal`.

<essential_principles>

Use only these composed capabilities:

- `coding-agents:operate-herdr` for inventory, read, bounded wait, prompt,
  start, relaunch, stop, and other pane operations it owns
- `coding-agents:operate-agent-mail` for registration, message records, inbox
  reads, and receipts
- `spec-tree:project-run-journal` for read-only inspection of each sealed
  verification run whose complete identity a durable mail record supplies

Beyond them, the one executable this skill runs is its own bundled ledger entry
point, governed by `<ledger_derivation>`.

Pass semantic requests to those skills and preserve their complete results.
Neither infer nor reproduce their underlying command grammar. This skill has no
daemon, watcher, or polling loop. Carry out exactly one routed operation per
invocation, then return to the event boundary.

For either coding-agents capability, accept proof only from a result carrying
`schemaVersion: 1`, `status: "succeeded"`, and `commandExitCode: 0`. An
agent-mail result additionally carries a non-empty `projectKey`, `response`,
and `data`; a delivered record carries its integer store-assigned `id`. A herdr
JSON operation carries `response.result`, while a read carries terminal text in
`response.output`. Require the operation-specific identity and state fields
named by the routed workflow before relying on the result. Preserve and return
any other status and detail as a failed operation without inferring success or
trying a fallback.

</essential_principles>

<intake>

Interpret `$ARGUMENTS` as the operator request or officer event. Select one of
the eight operations in `<routing>`. When the request is empty, ambiguous, or
names several operations, run nothing and return `invalid-invocation` with the
eight accepted operation names.

</intake>

<routing>

| Requested operation | Workflow                                     |
| ------------------- | -------------------------------------------- |
| launch              | `${CLAUDE_SKILL_DIR}/workflows/launch.md`    |
| order               | `${CLAUDE_SKILL_DIR}/workflows/order.md`     |
| read                | `${CLAUDE_SKILL_DIR}/workflows/read.md`      |
| correct             | `${CLAUDE_SKILL_DIR}/workflows/correct.md`   |
| answer              | `${CLAUDE_SKILL_DIR}/workflows/answer.md`    |
| escalate            | `${CLAUDE_SKILL_DIR}/workflows/escalate.md`  |
| housekeep           | `${CLAUDE_SKILL_DIR}/workflows/housekeep.md` |
| close               | `${CLAUDE_SKILL_DIR}/workflows/close.md`     |

</routing>

<reference_index>

| Reference                                                  | Purpose                                                     |
| ---------------------------------------------------------- | ----------------------------------------------------------- |
| `${CLAUDE_SKILL_DIR}/references/officer-order.md`          | Complete launch-and-order contract                          |
| `${CLAUDE_SKILL_DIR}/references/standing-rules.md`         | Fleet-wide autonomy, durability, event, and lifecycle rules |
| `${CLAUDE_SKILL_DIR}/references/ledger-reconstruction.md`  | Ledger input acquisition after a compaction or restart      |
| `${CLAUDE_SKILL_DIR}/references/ledger-script-coverage.md` | Tested cases and inputs for the bundled ledger entry point  |

</reference_index>

<workflows_index>

All operation workflows live under `${CLAUDE_SKILL_DIR}/workflows/`:

| Workflow       | Output                                                               |
| -------------- | -------------------------------------------------------------------- |
| `launch.md`    | One officer started in a proven pane and bounded registration result |
| `order.md`     | One complete durable order record and ledger identity                |
| `read.md`      | One event-caused state read and rebuilt ledger when required         |
| `correct.md`   | One authorized prompt correction or dismissal                        |
| `answer.md`    | One evidence-backed answer record or held decision                   |
| `escalate.md`  | One bounded escalation with its decision disposition                 |
| `housekeep.md` | One compaction, relaunch, or fleet-status action                     |
| `close.md`     | One Change disposal and fresh-session transition                     |

</workflows_index>

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

Each mail record preserves the store's integer `id` and string `body`. A JSON
body with a `ledger` object contributes its declared fields; other bodies
remain durable mail facts without entering the derived ledger. That object
carries any of `pass`, `head`, `verdict`, `decision`, `failure`,
`findingProvenance`, `read`, `spend`, and `wallTimeSeconds`. A `decision` event
records its autonomous class, choice, and reasoning. A `failure` event records
an operator instruction naming an officer session or an officer fact reporting
an operator interaction. A `read` event records one of the causes `message`,
`officer-state-change`, `bound-crossed`, and `operator-cadence`. Each journal
object preserves its `runToken`. Submit the document through one of these forms
and preserve the complete result.

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
exactly `change`, `passes`, `heads`, `verdicts`, `decisions`, `failures`,
`findingProvenance`, `reads`, `runningSpend`, and `wallTimeSeconds`, with source
provenance on every entry: the mail record's integer store `id`, or the journal
run's `runToken`. Runs repeating one `runToken` contribute once. Every rejection
— a malformed document, a refused schema version, or a wrong argument vector —
exits two and writes one `status: "invalid-input"` result carrying
`schemaVersion`, `status`, and `detail` on stdout, leaving stderr empty, so one
parse reads every outcome. A rejection caused by one record names that record's
position, so a document holding many records identifies the offending one.

Reconstruction after a compaction or restart runs only then, and its acquisition
procedure lives in `${CLAUDE_SKILL_DIR}/references/ledger-reconstruction.md`.

</ledger_derivation>

<script_validation>

The executed cases for the bundled ledger entry point — reachability, populated
derivation, and each documented rejection, with the inputs each uses — are
recorded in `${CLAUDE_SKILL_DIR}/references/ledger-script-coverage.md`.

</script_validation>

<result>

Return the operation, the complete officer identity, absolute worktree, Change,
triggering event, capability results, ledger change, and next event boundary.
Spend and wall time are courtesy fields rather than gates. Preserve complete
session, message, commit, and verification-run identities.

</result>

<success_criteria>

- A launch result includes the successful herdr inventory/start identity, exact
  worktree and pane, frozen full HEAD, Change, bounded wait result, and proven
  registered mail identity before any order is sent.
- An order result includes a successful agent-mail response whose returned
  record has an integer store `id`; a derivation run over that record succeeds
  and preserves the id as source provenance.
- A read result names one allowed event cause, preserves the successful inbox or
  pane response, and emits no state-change report when the checked state is
  unchanged unless operator cadence requested one.
- Every returned operation includes the complete capability results it relied
  on; each accepted result satisfies `<essential_principles>`, and any failed
  capability status remains a failed operation.
- Every mutating herdr operation the result reports carries the standing pane
  authorization for a pane this skill launched, and no pane outside that set is
  mutated.
- After compaction or restart, the acquisition in
  `${CLAUDE_SKILL_DIR}/references/ledger-reconstruction.md` reaches correlation
  closure over the durable mail and sealed journal inputs, and running the
  documented derivation over them produces the ledger keys in
  `<ledger_derivation>`, each entry carrying the source that supplied it.

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

**Claude treated an empty adapter inbox as an empty store.** When a checked
store observation proves records exist after an adapter inbox returned zero,
use only the orchestrating session's explicit read-only store instruction for
that project; never derive a raw store command.

</failure_modes>
