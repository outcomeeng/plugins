---
name: orchestrate-officers
description: >-
  ALWAYS invoke this skill when one operator-facing session supervises officer sessions that each execute one Change through herdr and agent-mail. NEVER supervise those officers by constructing environment or mail commands directly.
argument-hint: "<operator request or officer event>"
allowed-tools: Read, Bash(printf:*), Bash(python3 "${SKILL_DIR}/scripts/derive_ledger.py":*)
---

<objective>
The result of one routed supervision operation over an officer fleet, carrying
that operation's validated capability results, the ledger change, and the next
event boundary.

</objective>

<essential_principles>

Use only these composed capabilities, each invoked by name and used for the
operations it owns:

- Use skill `coding-agents:operate-herdr`. It owns inventory, read, bounded
  wait, prompt, start, relaunch, stop, and the other pane operations.
- Use skill `coding-agents:operate-agent-mail`. It owns the mail project key,
  registration, message records, inbox reads, and receipts.
- Use skill `spec-tree:project-run-journal`. It owns read-only inspection of
  each sealed verification run whose complete identity a durable mail record
  supplies.

Beyond them, the one executable this skill runs is its own bundled ledger entry
point, governed by `<ledger_derivation>`; `printf` appears only as the shell
plumbing that feeds that entry point its document on a single command line.

Pass semantic requests to those skills and preserve their complete results.
Neither infer nor reproduce their underlying command grammar. This skill has no
daemon, watcher, or polling loop. Carry out exactly one routed operation per
invocation, then return to the event boundary.

A capability result that reports a store or environment command is accepted as
proof only when it carries `schemaVersion: 1`, `status: "succeeded"`, and
`commandExitCode: 0`. Every herdr result is of that kind: a JSON operation
carries `response.result`, while a read carries terminal text in
`response.output`. An agent-mail result of that kind additionally carries a
non-empty `projectKey`, `response`, and `data`; a delivered record carries its
integer store-assigned `id`.

The agent-mail project-key answer is the one result the rule above does not
govern. It runs no store command, so it proves the key on a zero exit and a
non-empty `projectKey` alone, and carries no `schemaVersion`, no success
`status`, no `commandExitCode`, no `response`, and no `data`. Judging that
answer by the versioned rule converts a real success into a failed operation
and leaves the workflows that need the key — the officer's exact inbox
instruction and the read-only store instruction for the affected project —
without it. Its own failure carries `status: "repository-unresolved"` with
`detail` and a non-zero exit.

Require the operation-specific identity and state fields named by the routed
workflow before relying on either result. Preserve and return every other
answer as a failed operation without inferring success or trying a fallback.

</essential_principles>

<intake>

Interpret `$ARGUMENTS` as the operator request or officer event. Select one of
the operations in `<routing>`. When the request is empty, ambiguous, or
names several operations, run nothing and return `invalid-invocation` with the
accepted operation names.

</intake>

<routing>

| Requested operation | Workflow                              |
| ------------------- | ------------------------------------- |
| launch              | `${SKILL_DIR}/workflows/launch.md`    |
| order               | `${SKILL_DIR}/workflows/order.md`     |
| read                | `${SKILL_DIR}/workflows/read.md`      |
| correct             | `${SKILL_DIR}/workflows/correct.md`   |
| answer              | `${SKILL_DIR}/workflows/answer.md`    |
| escalate            | `${SKILL_DIR}/workflows/escalate.md`  |
| housekeep           | `${SKILL_DIR}/workflows/housekeep.md` |
| close               | `${SKILL_DIR}/workflows/close.md`     |

</routing>

<reference_index>

| Reference                                           | Purpose                                                           |
| --------------------------------------------------- | ----------------------------------------------------------------- |
| `${SKILL_DIR}/references/officer-order.md`          | Complete launch-and-order contract                                |
| `${SKILL_DIR}/references/standing-rules.md`         | Fleet-wide autonomy, durability, event, and lifecycle rules       |
| `${SKILL_DIR}/references/ledger-contract.md`        | Ledger input document, derived ledger, and refused sources        |
| `${SKILL_DIR}/references/ledger-reconstruction.md`  | Ledger input acquisition after a compaction or restart            |
| `${SKILL_DIR}/references/ledger-script-coverage.md` | Tested cases, inputs, and executing evidence for that entry point |

</reference_index>

<workflows_index>

All operation workflows live under `${SKILL_DIR}/workflows/`:

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

The bundled entry point derives one per-Change ledger from a JSON document on
stdin. What that document holds, what the ledger holds, and which sources the
entry point refuses live in
`${SKILL_DIR}/references/ledger-contract.md`; this section carries the
invocation form and the rule for accepting a result, so contract detail the
entry point gains later lands in that reference rather than here.

Submit the document through one of these forms and preserve the complete
result.

When the shell accepts multiline input:

```bash
python3 "${SKILL_DIR}/scripts/derive_ledger.py" derive <<'JSON'
{"schemaVersion":1,"change":"owner/changes#123","mailRecords":[],"journalRuns":[]}
JSON
```

When the runner requires one physical command line:

```bash
printf '%s\n' '{"schemaVersion":1,"change":"owner/changes#123","mailRecords":[],"journalRuns":[]}' | python3 "${SKILL_DIR}/scripts/derive_ledger.py" derive
```

Accept only `schemaVersion: 1` with `status: "succeeded"`. Every refusal — of
the argument vector, of the document, or of one record inside it — writes one
`status: "invalid-input"` result on stdout carrying `schemaVersion`, `status`,
and `detail`, exits two, and leaves the error stream empty, so one parse reads
every outcome and no source reaches the caller as a traceback. Read each total
the accepted ledger carries into an exact decimal type: the totals are decimal
strings rather than JSON numbers, and a float parse drops digits the sources
carried.

Reconstruction after a compaction or restart runs only then, and its acquisition
procedure lives in `${SKILL_DIR}/references/ledger-reconstruction.md`.

</ledger_derivation>

<script_validation>

The executed cases for the bundled ledger entry point — reachability, populated
derivation, and each documented rejection, with the inputs each uses and the
evidence that executes it — are recorded in
`${SKILL_DIR}/references/ledger-script-coverage.md`.

</script_validation>

<result>

Return the operation, the complete officer identity, absolute worktree, Change,
triggering event, capability results, ledger change, and next event boundary.
Spend and wall time are courtesy fields rather than gates. Preserve complete
session, message, commit, and verification-run identities.

A refused invocation returns `invalid-invocation` and the accepted operation
names, and nothing else — no capability ran, so it carries no officer identity,
capability result, or ledger change to report.

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
  authorization for a pane the operator's invocation assigned to this fleet, and
  no pane outside that set is mutated.
- A request that is empty, ambiguous, or names several operations returns
  `invalid-invocation` with the accepted operation names, and the result carries
  no capability call, because none ran.
- After compaction or restart, the acquisition in
  `${SKILL_DIR}/references/ledger-reconstruction.md` reaches correlation
  closure over the durable mail and sealed journal inputs, and running the
  documented derivation over them produces the ledger keys
  `${SKILL_DIR}/references/ledger-contract.md` declares under
  `## The derived ledger`, each entry carrying the source that supplied it.

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
