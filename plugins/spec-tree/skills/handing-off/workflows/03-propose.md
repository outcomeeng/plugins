<objective>
Present the combined output of the six reflection perspectives as a persistence proposal. Only items that require user approval appear here. Deficiencies fixed inline during workflow 02 are done — report them as completed work, not as proposals.

</objective>

<session_disposition_header>
Before the `AskUserQuestion` block, print a plain-text header naming the canonical continuation plan plus every session that will be archived:

```text
Canonical continuation: <rewrite-in-place of <artifact-id> | new handoff | none (--no-session)>
Sessions to archive after closure: <id-1>, <id-2>, ...
```

The list comes from `<perspective_session_scope>` in workflow 02 — every session classified as **in-scope**, plus every mid-session artifact that will be archived (rather than rewritten). If SESSION_SCOPE is empty (fresh handoff, no prior pickup) and no artifact exists, write `Sessions to archive after closure: none`.

This header is declared intent, not a vote. Default path is archive-all-listed. If the user wants to exclude any id, they raise it in free text before answering the proposal. Never leave an in-scope session beside the new continuation.

**STOP if the user disputes the disposition.** If the user objects to the canonical continuation plan, the archive list, or any session id in either, halt the workflow. Do not proceed to workflow 04, do not archive, do not write the canonical continuation. Return to workflow 02 and re-reflect with the user's correction before proposing again.

</session_disposition_header>

<process>
Present a single `AskUserQuestion` with `multiSelect: true`. Group items by type: lessons, issues, insights, and a skip option for coordination-only items.

```json
{
  "questions": [{
    "question": "Review persistence proposal — select items to approve:",
    "header": "Persist",
    "multiSelect": true,
    "options": [
      { "label": "[Lesson → destination] summary", "description": "→ target named by nature (e.g., 'coding-typescript refs', 'CLAUDE.md', 'standardizing-typescript')" },
      { "label": "[Issue] summary", "description": "→ target: fix spec / ISSUES.md in spx/{node}" },
      { "label": "[Insight] summary", "description": "→ target: amend spec / PLAN.md in spx/{node} / remove stale PLAN.md" },
      { "label": "[Skip] N items", "description": "→ session file only (coordination context)" }
    ]
  }]
}
```

**Lesson labels MUST include the destination type** from the `<perspective_lessons>` taxonomy in `02-reflect.md`. Examples:

```text
☑ [Lesson → coding-typescript refs] fast-check v4: fc.stringOf → fc.string({ unit: ... })
☑ [Lesson → standardizing-typescript-arch] ADR audit: 'no ADR exists' is REJECT, not N/A
☑ [Lesson → spec-tree plugin] Invoke /contextualizing before suggesting handoff
☑ [Lesson → CLAUDE.md] Require git mv for file moves
```

This lets the user verify at a glance that each lesson is going to the right place.

**`AskUserQuestion` is limited to 4 options.** If there are more than 3 actionable items, batch them by perspective (one question per perspective with items as options). The "[Skip]" option always appears as the last option in the last question.

</process>

<success_criteria>

- Session-disposition header printed before the proposal, naming the canonical continuation plan and every session that will be archived.
- User has reviewed and approved (or rejected) all proposed persistence items.
- Approved items are recorded for execution in workflow 04.
- Unapproved items are noted as coordination-only context for the session file.

</success_criteria>
