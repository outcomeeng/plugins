<example>

**Workflow 01 output — anchored nodes**

- `spx/21-test-harness.enabler/32-temp-files.enabler` — tests written and passing, implementation complete
- `spx/21-test-harness.enabler/43-fixtures.enabler` — spec authored, tests written but failing

**Workflow 02 output — five perspectives**

- **Lessons**: User corrected import pattern twice — relative imports where absolute were required. Rule: "always use absolute imports from the package root." Also: `tempfile.NamedTemporaryFile` needs `delete=False` on Windows — a library gotcha.
- **Issues**: No existing ISSUES.md. The `43-fixtures.enabler` spec has 5 assertions but 2 are untestable without the implementation — not an issue, just TDD sequence.
- **Path forward**: Existing PLAN.md in `43-fixtures.enabler` is stale — steps 1-3 are complete, only steps 4-5 remain. The approach (context managers over explicit cleanup) was validated.
- **Skills**: Used `/testing-python`, skipped `/coding-python` on first attempt which caused import violations. Next agent must invoke `/coding-python` before writing implementation.
- **Starting point**: `43-fixtures.enabler`, TDD step 7 (implement), invoke `/coding-python`.

**Workflow 03 output — approved persistence items**

```text
☑ [Lesson → CLAUDE.md] Always use absolute imports from package root
☑ [Lesson → coding-python refs] tempfile.NamedTemporaryFile needs delete=False on Windows
☑ [Insight] Update PLAN.md in 43-fixtures.enabler: remove completed steps 1-3, keep 4-5
☐ [Skip] 2 items → session file only
```

**Workflow 04 — execution**

1. Writes CLAUDE.md entry (absolute imports), adds tempfile caveat to `coding-python/references/`.
2. Updates PLAN.md in `43-fixtures.enabler` — removes steps 1-3, keeps steps 4-5.
3. Stages and commits session-owned files via `/committing-changes`.
4. Records state: `32-temp-files.enabler` and `43-fixtures.enabler/tests/` committed; unrelated foreign changes remain uncommitted.
5. Finds the current pickup marker in conversation:

```text
<PICKUP_CHECKPOINT id="2026-03-29_10-15-00" target="spx/21-test-harness.enabler/43-fixtures.enabler" mode="ask">
  next_action: /coding-python
</PICKUP_CHECKPOINT>
```

6. Runs `spx session handoff`, parses `<HANDOFF_ID>` and `<SESSION_FILE>`.
7. Writes session file:

```text
---
priority: high
tags: [test-harness, python]
---
<metadata>
  timestamp: 2026-03-29T14:22:00Z
  project: my-project
  git_branch: feat/test-harness
  git_status: dirty
  working_directory: /Users/dev/my-project
</metadata>

<nodes>
Spec-tree nodes worked on. The receiving agent should invoke
`/contextualizing` on each before starting work.

- `spx/21-test-harness.enabler/32-temp-files.enabler`
  - Status: tests passing, implementation complete
  - Done: Wrote 3 test files, implemented temp file cleanup with context managers
  - Escape hatches: none

- `spx/21-test-harness.enabler/43-fixtures.enabler`
  - Status: spec authored, tests written but failing (2 of 5 pass)
  - Done: Authored spec with 5 assertions, wrote test stubs
  - Remaining: see PLAN.md
  - Escape hatches: PLAN.md written

</nodes>

<skills>

## Critical — invoke before starting work
- `/understanding` — load spec tree methodology
- `/contextualizing 21-test-harness.enabler/43-fixtures.enabler` — load target context

## Missed — caused problems when skipped
- `/coding-python` — skipped initially, led to import pattern violations. MUST invoke before writing implementation code.

## Next action
- `/coding-python` — continue TDD flow for fixtures enabler
- TDD flow position: step 7 (implement) on `spx/21-test-harness.enabler/43-fixtures.enabler`

</skills>

<persisted>
What was captured durably during session closure.

- Committed: `spx/21-test-harness.enabler/32-temp-files.enabler/` and `spx/21-test-harness.enabler/43-fixtures.enabler/tests/`
- Uncommitted: unrelated foreign changes only
- Insights: Added absolute imports rule to CLAUDE.md; added Windows tempfile caveat to `coding-python/references/`
- Escape hatches: PLAN.md in `spx/21-test-harness.enabler/43-fixtures.enabler/`

</persisted>

<coordination>
Cross-cutting context that doesn't belong to any single node.

- Session ended due to context window pressure
- The fixtures enabler depends on temp-files enabler being complete (it is)
- Python 3.11+ required for ExceptionGroup support used in test assertions

</coordination>
```

8. Archives the claimed doing session from the pickup marker: `spx session archive 2026-03-29_10-15-00`
9. Confirms: "Handoff created: `2026-03-29_14-22-00`. Session-owned work committed. Archived doing session: `2026-03-29_10-15-00`."

</example>
