<objective>
A persistence proposal containing the approval-required closure decisions and one explicit session disposition per continuation thread.
</objective>

<required_reading>

Use workflow 02's imperfections, path-forward, next-context, external-state, claimed-sessions, and existing-sessions perspectives plus its resolved continuation-thread records as the proposal input. Imperfections fixed inline during workflow 02 are reported as completed work, not as proposals.

</required_reading>

<session_disposition_header>
Before any proposal, print a plain-text header naming every thread disposition plus every session that will be archived:

```text
Continuation threads:
- <thread-id>: <new handoff | no handoff (no reader) | existing owner <session-id>>
Sessions to archive after closure: <id-1>, <id-2>, ...
Archived sessions to delete after closure: <archive-id-1>, <archive-id-2>, ... | none
```

The thread list comes from `<RESOLVED_CONTINUATION_THREADS>`. The claimed-session list comes from `ids` in `<RESOLVED_CLAIMED_SESSIONS ids="…" artifact_ids="…">`. Treat `artifact_ids` as candidates, never as an archive list. Partition those candidates by matching `thread_id`, comparing `goal`, `next_step`, `specs`, and `files`. Emit the authoritative partition marker:

```text
<RESOLVED_ARTIFACT_PARTITIONS candidate_ids="artifact-1,artifact-2,...">
<partition thread_id="thread-1" disposition="fresh-session|zero-handoff|existing-owner">
continuation: <canonical continuation identity or existing owner id>
archive_ids: artifact-1
</partition>
<partition thread_id="thread-2" disposition="fresh-session|zero-handoff|existing-owner">
continuation: <canonical continuation identity or existing owner id>
archive_ids: artifact-2
</partition>
</RESOLVED_ARTIFACT_PARTITIONS>
```

Emit exactly one `partition` for every `<RESOLVED_CONTINUATION_THREADS>` record and no extra partition. Derive its disposition from that record: `fresh-session` for `continuation="present"` with owner status `none` or `same-owner-continuation` and a real stop condition; `zero-handoff` for `continuation="absent"`; `existing-owner` for owner status `existing-owner`; `ambiguous` stops before proposal. Threads with no prior artifact use an empty `archive_ids:` value. Require every candidate id to appear in exactly one partition's `archive_ids`. A missing or duplicate thread record, mismatch between thread and partition sets, or duplicate, absent, zero-thread, or multi-thread candidate assignment is ambiguous, so STOP and ask the operator before proposing or archiving. The header lists every thread disposition, every claimed id, and the archive ids across all partitions. If both archive sets are empty, write `Sessions to archive after closure: none`.

This header is declared intent, not a vote. Default path is archive-all-listed. If the user wants to exclude any id, they raise it in free text before the workflow executes. Never leave a claimed session beside the new continuation.

When `<HANDOFF_OPTIONS prune="true" ... />` was emitted and at least one partition has `disposition="fresh-session"`, read `spx session list --status archive --json` before presenting the header. Build the proposed deletion set as the exact union of the IDs already in archive and every claimed or partition `archive_ids` entry the header says this closure will archive. Present one dedicated structured approval for that complete deletion set, even when no persistence edit otherwise requires approval. Emit `<APPROVED_PRUNE ids="archive-id-1,archive-id-2,...">` only after approval; emit `ids=""` when the union is empty. If the operator rejects deletion, omit the marker and preserve every archived session. When the marker records `prune="false"`, or no partition creates a fresh session, write `Archived sessions to delete after closure: none` and emit no prune marker.

For each record with `continuation="present"`, a fresh continuation is allowed only if continuation by Claude is impossible now. Do not present a fresh handoff for an actionable coordination note while Claude can act. An `existing-owner` record reports its owner and proposes no fresh session for that thread. An `ambiguous` record stops the entire proposal until the operator resolves that thread's ownership.

When no persistence items require user approval and `<HANDOFF_OPTIONS prune="false" ... />` was emitted, do not call `AskUserQuestion` only to approve the disposition. State the header, name that there are no approval-required persistence edits, and proceed to workflow 04. A structured question is reserved for approval-required persistence edits, the exact prune deletion set, ambiguous session disposition, user-disputed disposition, or the explicit no-session contradiction handled by workflow 04 Path A.

**STOP if the user disputes the disposition.** If the user objects to any thread disposition, the archive list, or any session id, halt the workflow. Do not proceed to workflow 04, archive, or write a continuation. Return to workflow 02 and re-reflect with the user's correction before proposing again.

</session_disposition_header>

<process>
When one or more persistence items require user approval, present them through `AskUserQuestion` as one decision per item. Each question names the item and destination and offers two choices: **Approve** (write to the named destination) and **Skip** (keep as coordination context only when a continuation session is valid). Group questions by perspective and send at most three questions per call so the same interaction works on every supported harness.

**Imperfection labels MUST include the destination** from the `<perspective_imperfections>` taxonomy in `02-reflect.md`. Examples:

```text
☑ [Imperfection → code-typescript refs] fast-check v4: fc.stringOf → fc.string({ unit: ... })
☑ [Imperfection → audit-typescript-architecture skill] ADR audit: 'no ADR exists' is REJECT, not N/A
☑ [Imperfection → spec-tree plugin] Invoke /contextualize before suggesting handoff
☑ [Imperfection → CLAUDE.md] Require git mv for file moves
☑ [Imperfection → ISSUES.md in spx/55-example.enabler] Tests for assertion 3 missing
```

This lets the user verify at a glance that each item is going to the right place.

**Chunking rules:**

1. Group items by perspective first.
2. Ask one independently answerable question per item, with **Approve** and **Skip** choices.
3. Send no more than three questions in one `AskUserQuestion` call.
4. Wait for each call's answers before presenting the next batch; approved items can make later items redundant.
5. Never collapse multiple actionable items into one summary choice. Every item remains visible and independently approvable.

</process>

<success_criteria>

- Session-disposition header printed before the proposal, naming every thread disposition and every session that will be archived.
- User has reviewed and approved (or rejected) all proposed persistence items, or no approval-required persistence items existed and the workflow proceeded without a structured question.
- When `<HANDOFF_OPTIONS prune="true" ... />` applies to a fresh-session closure, the operator has approved or rejected the exact union of existing and closure-created archive IDs, and an approval emits `<APPROVED_PRUNE>`.
- Approved items are recorded for execution in workflow 04.
- Unapproved items are noted as coordination-only context for the session file.

</success_criteria>

<failure_modes>

**Turned an actionable note into a queue entry.** Claude completed the claimed session's original deliverable, saw that the anchored node still had unrelated `PLAN.md` or `ISSUES.md` continuation, then proposed a new handoff instead of reconciling the note. That inflated the session queue and split work away from the durable map. When a coordination note is actionable and Claude can still act, return to the work; propose a continuation only after a real stop condition exists and the existing-session search proves no other session owns it.

</failure_modes>
