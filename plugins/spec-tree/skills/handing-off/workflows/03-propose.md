<objective>
Present the combined output of the five reflection perspectives as a persistence proposal. Only items that require user approval appear here. Deficiencies fixed inline during workflow 02 are done — report them as completed work, not as proposals.

</objective>

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

- User has reviewed and approved (or rejected) all proposed persistence items.
- Approved items are recorded for execution in workflow 04.
- Unapproved items are noted as coordination-only context for the session file.

</success_criteria>
