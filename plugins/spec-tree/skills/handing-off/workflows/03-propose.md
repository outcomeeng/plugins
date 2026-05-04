<objective>
Present the combined output of the four reflection perspectives as a persistence proposal. Only items that require user approval appear here. Imperfections fixed inline during workflow 02 are done — report them as completed work, not as proposals.

</objective>

<session_disposition_header>
Before the `AskUserQuestion` block, print a plain-text header naming the canonical continuation plan plus every session that will be archived:

```text
Canonical continuation: <rewrite-in-place of <artifact-id> | new handoff | none (--no-session)>
Sessions to archive after closure: <id-1>, <id-2>, ...
```

The list comes from the `<RESOLVED_SCOPE ids="…" artifact_id="…">` marker emitted by workflow 02 — every session in `ids` (in-scope), plus the artifact only if it will be archived rather than rewritten. If `ids=""` (fresh handoff, no prior pickup) and `artifact_id="none"`, write `Sessions to archive after closure: none`.

This header is declared intent, not a vote. Default path is archive-all-listed. If the user wants to exclude any id, they raise it in free text before answering the proposal. Never leave an in-scope session beside the new continuation.

**STOP if the user disputes the disposition.** If the user objects to the canonical continuation plan, the archive list, or any session id in either, halt the workflow. Do not proceed to workflow 04, do not archive, do not write the canonical continuation. Return to workflow 02 and re-reflect with the user's correction before proposing again.

</session_disposition_header>

<process>
Present a single `AskUserQuestion` with `multiSelect: true`. Group items by type: imperfections (with their destination), path-forward insights, and a skip option for coordination-only items.

```json
{
  "questions": [{
    "question": "Review persistence proposal — select items to approve:",
    "header": "Persist",
    "multiSelect": true,
    "options": [
      { "label": "[Imperfection → destination] summary", "description": "→ target named by nature (e.g., 'coding-typescript refs', 'CLAUDE.md', 'standardizing-typescript', 'ISSUES.md in spx/{node}')" },
      { "label": "[Insight] summary", "description": "→ target: amend spec / PLAN.md in spx/{node} / remove stale PLAN.md" },
      { "label": "[Skip] N items", "description": "→ session file only (coordination context)" }
    ]
  }]
}
```

**Imperfection labels MUST include the destination** from the `<perspective_imperfections>` taxonomy in `02-reflect.md`. Examples:

```text
☑ [Imperfection → coding-typescript refs] fast-check v4: fc.stringOf → fc.string({ unit: ... })
☑ [Imperfection → standardizing-typescript-arch] ADR audit: 'no ADR exists' is REJECT, not N/A
☑ [Imperfection → spec-tree plugin] Invoke /contextualizing before suggesting handoff
☑ [Imperfection → CLAUDE.md] Require git mv for file moves
☑ [Imperfection → ISSUES.md in spx/21-foo.enabler] Tests for assertion 3 missing
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
- User has reviewed and approved (or rejected) all proposed persistence items.
- Approved items are recorded for execution in workflow 04.
- Unapproved items are noted as coordination-only context for the session file.

</success_criteria>
