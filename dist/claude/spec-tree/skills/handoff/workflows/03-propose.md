<objective>
A persistence proposal containing the approval-required closure decisions and canonical session disposition.
</objective>

Use the six reflection perspectives from workflow 02 as the proposal input. Imperfections fixed inline during workflow 02 are reported as completed work, not as proposals.

<session_disposition_header>
Before any proposal, print a plain-text header naming the canonical continuation plan plus every session that will be archived:

```text
Canonical continuation: <new handoff | none (--no-session)>
Sessions to archive after closure: <id-1>, <id-2>, ...
```

The claimed-session list comes from `ids` in the `<RESOLVED_CLAIMED_SESSIONS ids="…" artifact_ids="…">` marker emitted by workflow 02. Treat `artifact_ids` as candidates, never as an archive list. Partition those candidates by independent continuation thread against the canonical continuation plan, comparing `goal`, `next_step`, `specs`, and `files`. Emit the authoritative partition marker:

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

Emit exactly one `partition` per independent continuation thread in the canonical plan, including threads with no prior artifact; those records use an empty `archive_ids:` value. Separately require every candidate id to appear in exactly one partition's `archive_ids`. A missing or duplicate thread record, or duplicate, absent, zero-thread, or multi-thread candidate assignment, is ambiguous, so STOP and ask the operator before proposing or archiving. The header lists every claimed id plus the archive ids across all partitions selected for this closure. If both sets are empty, write `Sessions to archive after closure: none`.

This header is declared intent, not a vote. Default path is archive-all-listed. If the user wants to exclude any id, they raise it in free text before the workflow executes. Never leave a claimed session beside the new continuation.

When `<CONTINUATION_SIGNAL state="present">` exists, a canonical continuation is allowed only if continuation by Claude is impossible now. Do not present "create handoff" as a normal option for actionable coordination notes. A completed claimed session can anchor a node that still has unrelated `PLAN.md` or `ISSUES.md` continuation; in that case, closure is blocked while Claude can still reconcile or execute the note. If a real stop condition exists, workflow 04 may create the canonical continuation only after `<EXISTING_SESSION_RECONCILIATION status="none">` or `status="same-owner-continuation"` confirms the queue will not receive a duplicate.

If `<EXISTING_SESSION_RECONCILIATION status="existing-owner">` exists, report that an existing session already owns the continuation and do not propose a new session. If `status="ambiguous"` exists, STOP and ask the operator to resolve ownership before any continuation proposal.

When no persistence items require user approval, do not call `AskUserQuestion` only to approve the disposition. State the header, name that there are no approval-required persistence edits, and proceed to workflow 04. A structured question is reserved for approval-required persistence edits, ambiguous session disposition, user-disputed disposition, or the explicit `--no-session` contradiction handled by workflow 04 Path A.

**STOP if the user disputes the disposition.** If the user objects to the canonical continuation plan, the archive list, or any session id in either, halt the workflow. Do not proceed to workflow 04, do not archive, do not write the canonical continuation. Return to workflow 02 and re-reflect with the user's correction before proposing again.

</session_disposition_header>

<process>
When one or more persistence items require user approval, present them through `AskUserQuestion` as one decision per item. Each question names the item and destination and offers two choices: **Approve** (write to the named destination) and **Skip** (keep as coordination context only when a continuation session is valid). Group questions by perspective and send at most three questions per call so the same interaction works on every supported harness.

**Imperfection labels MUST include the destination** from the `<perspective_imperfections>` taxonomy in `02-reflect.md`. Examples:

```text
☑ [Imperfection → code-typescript refs] fast-check v4: fc.stringOf → fc.string({ unit: ... })
☑ [Imperfection → typescript-standards-arch] ADR audit: 'no ADR exists' is REJECT, not N/A
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

- Session-disposition header printed before the proposal, naming the canonical continuation plan and every session that will be archived.
- User has reviewed and approved (or rejected) all proposed persistence items, or no approval-required persistence items existed and the workflow proceeded without a structured question.
- Approved items are recorded for execution in workflow 04.
- Unapproved items are noted as coordination-only context for the session file.

</success_criteria>

<failure_modes>

**Turned an actionable note into a queue entry.** Claude completed the claimed session's original deliverable, saw that the anchored node still had unrelated `PLAN.md` or `ISSUES.md` continuation, then proposed a new handoff instead of reconciling the note. That inflated the session queue and split work away from the durable map. When a coordination note is actionable and Claude can still act, return to the work; propose a continuation only after a real stop condition exists and the existing-session search proves no other session owns it.

</failure_modes>
