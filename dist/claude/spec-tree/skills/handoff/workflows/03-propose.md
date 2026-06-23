<objective>
A persistence proposal carrying only the items that require user approval, derived from the four reflection perspectives of workflow 02. Imperfections fixed inline during workflow 02 are reported as completed work, not as proposals.

</objective>

<session_disposition_header>
Before any proposal, print a plain-text header naming the canonical continuation plan plus every session that will be archived:

```text
Canonical continuation: <rewrite-in-place of <artifact-id> | new handoff | none (--no-session)>
Sessions to archive after closure: <id-1>, <id-2>, ...
```

The list comes from the `<RESOLVED_CLAIMED_SESSIONS ids="…" artifact_id="…">` marker emitted by workflow 02 — every session in `ids` (claimed), plus the artifact only if it will be archived rather than rewritten. If `ids=""` (fresh handoff, no prior pickup) and `artifact_id="none"`, write `Sessions to archive after closure: none`.

This header is declared intent, not a vote. Default path is archive-all-listed. If the user wants to exclude any id, they raise it in free text before the workflow executes. Never leave a claimed session beside the new continuation.

When `<CONTINUATION_SIGNAL state="present">` exists, a canonical continuation is mandatory unless the user disputes the signal. Do not present "omit handoff" as a normal option. A completed claimed session can anchor a node that still has unrelated `PLAN.md` or `ISSUES.md` continuation; in that case, archive the completed session and carry the remaining node work through the canonical continuation: rewrite the mid-session artifact in place when `artifact_id` is present, otherwise create a new thin handoff. If the user passed `--no-session`, workflow 04 Path A handles that as a contradiction to resolve, not as a normal proposal choice.

When no persistence items require user approval, do not call `AskUserQuestion` only to approve the disposition. State the header, name that there are no approval-required persistence edits, and proceed to workflow 04. A structured question is reserved for approval-required persistence edits, ambiguous session disposition, user-disputed disposition, or the explicit `--no-session` contradiction handled by workflow 04 Path A.

**STOP if the user disputes the disposition.** If the user objects to the canonical continuation plan, the archive list, or any session id in either, halt the workflow. Do not proceed to workflow 04, do not archive, do not write the canonical continuation. Return to workflow 02 and re-reflect with the user's correction before proposing again.

</session_disposition_header>

<spx_claude_staleness>
When a `<SPX_CLAUDE_STALE>` marker is present in the conversation — emitted by `/understand` when the product's `spx/CLAUDE.md` and `spx/AGENTS.md` are absent or behind the installed template — include a proposal item to reconcile it:

```text
☑ [Imperfection → run /update-spx] spx/CLAUDE.md and spx/AGENTS.md are [stale|absent] vs the installed template — reconcile via /update-spx
```

Include this item even when no other imperfection surfaced — template drift is a real, actionable continuation the operator should see.

</spx_claude_staleness>

<process>
When one or more persistence items require user approval, present a single `AskUserQuestion` with `multiSelect: true`. Group items by type: imperfections (with their destination), path-forward insights, and a skip option for coordination-only items.

```json
{
  "questions": [{
    "question": "Review persistence proposal — select items to approve:",
    "header": "Persist",
    "multiSelect": true,
    "options": [
      { "label": "[Imperfection → destination] summary", "description": "→ target named by nature (e.g., 'code-typescript refs', 'CLAUDE.md', 'typescript-standards', 'ISSUES.md in spx/{node}')" },
      { "label": "[Insight] summary", "description": "→ target: amend spec / PLAN.md in spx/{node} / remove stale PLAN.md" },
      { "label": "[Skip] N items", "description": "→ session file only (coordination context)" }
    ]
  }]
}
```

**Imperfection labels MUST include the destination** from the `<perspective_imperfections>` taxonomy in `02-reflect.md`. Examples:

```text
☑ [Imperfection → code-typescript refs] fast-check v4: fc.stringOf → fc.string({ unit: ... })
☑ [Imperfection → typescript-standards-arch] ADR audit: 'no ADR exists' is REJECT, not N/A
☑ [Imperfection → spec-tree plugin] Invoke /contextualize before suggesting handoff
☑ [Imperfection → CLAUDE.md] Require git mv for file moves
☑ [Imperfection → ISSUES.md in spx/55-example.enabler] Tests for assertion 3 missing
```

This lets the user verify at a glance that each item is going to the right place.

**`AskUserQuestion` has two hard limits: 4 options per question, 4 questions per call.** Batch actionable items so no single question exceeds 4 options, and no call exceeds 4 questions.

**Chunking rules:**

1. **Group items by perspective first.** Each perspective produces one or more questions.
2. **Perspective has ≤3 actionable items** → one question with those items plus `[Skip this perspective]` as the 4th option.
3. **Perspective has >3 items** → chunk within the perspective:
   - Question N: first 3 items + `[See more from this perspective]` as 4th option.
   - Question N+1: next 3 items + same continuation, repeat.
   - Final question for the perspective: remaining items + `[Skip remaining]` as the final option.
4. **Total questions across all perspectives >4** → split into multiple `AskUserQuestion` calls. Wait for the user's answers to each call before presenting the next batch — the user may revise their approach based on what they approved, and late items may become redundant.
5. **Global skip**: the overall `[Skip] N items → session file only` option appears as the last option in the last question of the last call — never mixed with per-perspective skip options.

Don't collapse a long list into a terse summary option to fit the limit. Each actionable item must be visible and separately approvable.

</process>

<success_criteria>

- Session-disposition header printed before the proposal, naming the canonical continuation plan and every session that will be archived.
- User has reviewed and approved (or rejected) all proposed persistence items, or no approval-required persistence items existed and the workflow proceeded without a structured question.
- Approved items are recorded for execution in workflow 04.
- Unapproved items are noted as coordination-only context for the session file.
- When a `<SPX_CLAUDE_STALE>` marker is present, the proposal includes an `/update-spx` reconciliation item.

</success_criteria>

<failure_modes>

**Asked whether to omit a required continuation.** Claude completed the claimed session's original deliverable, saw that the anchored node still had unrelated `PLAN.md` or `ISSUES.md` continuation, then asked the operator to approve either creating or omitting a handoff. That wasted a turn and implied the continuation signal was optional. When continuation is present, create the canonical continuation by default; ask only if the user explicitly requested `--no-session`, disputes the signal, or a separate persistence edit needs approval.

</failure_modes>
