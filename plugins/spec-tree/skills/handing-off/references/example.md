<example>

**Workflow 01 output — anchored nodes**

- `spx/21-test-harness.enabler/32-temp-files.enabler` — tests written and passing, implementation complete
- `spx/21-test-harness.enabler/43-fixtures.enabler` — spec authored, tests written but failing

**Workflow 02 output — six perspectives**

- **Lessons**: User corrected import pattern twice — relative imports where absolute were required. Rule: "always use absolute imports from the package root." Also: `tempfile.NamedTemporaryFile` needs `delete=False` on Windows — a library gotcha.
- **Issues**: No existing ISSUES.md. The `43-fixtures.enabler` spec has 5 assertions but 2 are untestable without the implementation — not an issue, just TDD sequence.
- **Path forward**: Existing PLAN.md in `43-fixtures.enabler` is stale — steps 1-3 are complete, only steps 4-5 remain. The approach (context managers over explicit cleanup) was validated.
- **Skills**: Used `/testing-python`, skipped `/coding-python` on first attempt which caused import violations. Next agent must invoke `/coding-python` before writing implementation.
- **Starting point**: `43-fixtures.enabler`, TDD step 7 (implement), invoke `/coding-python`.
- **Session scope**: `<SESSION_SCOPE ids="2026-03-29_09-05-00,2026-03-29_10-15-00">` names two user-confirmed pickups. Both will be archived after the canonical continuation is written. No mid-session artifact exists — Path C (new handoff) applies.

**Workflow 03 output — session-disposition header plus approved persistence items**

```text
Canonical continuation: new handoff (Path C)
Sessions to archive after closure: 2026-03-29_09-05-00, 2026-03-29_10-15-00

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
5. Resolves session scope from the most recent markers in conversation. No mid-session artifact exists — Path C (new handoff):

```text
<SESSION_SCOPE ids="2026-03-29_09-05-00,2026-03-29_10-15-00">
scope
</SESSION_SCOPE>

<PICKUP_CHECKPOINT id="2026-03-29_10-15-00" scope="2026-03-29_09-05-00,2026-03-29_10-15-00" target="spx/21-test-harness.enabler/43-fixtures.enabler" mode="ask">
  next_action: /coding-python
</PICKUP_CHECKPOINT>
```

6. Runs `spx session handoff`, parses `<HANDOFF_ID>` and `<SESSION_FILE>`.
7. Writes session file:

```text
---
priority: high
tags: [test-harness, fixtures, python]
agent_session_id: 019dbf37-84b9-7473-8ca2-752c96a767f1
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

<incorporated_sessions>
- 2026-03-29_09-05-00 — archived after this handoff
- 2026-03-29_10-15-00 — archived after this handoff
</incorporated_sessions>
```

8. Archives the resolved scope in order (earlier pickups first, claimed last):

   ```bash
   spx session archive 2026-03-29_09-05-00
   spx session archive 2026-03-29_10-15-00
   ```

9. Confirms: "Canonical continuation: new handoff `2026-03-29_14-22-00` (Path C). Session-owned work committed. Archived scope: `2026-03-29_09-05-00`, `2026-03-29_10-15-00`."

</example>

<example_rewrite_in_place>

**Path B scenario — a mid-session artifact exists**

Earlier in the conversation, context pressure prompted the agent to run `spx session handoff`, creating session `2026-04-24_08-10-44` in TODO as a safety net. Work continued afterward. At final closure, session `2026-04-24_02-11-00` is in DOING (the original pickup), and `2026-04-24_08-10-44` is still in TODO.

Workflow 02 classifies:

- **in-scope**: `2026-04-24_02-11-00` — named in `<SESSION_SCOPE>`.
- **mid-session artifact**: `2026-04-24_08-10-44` — created by this conversation's earlier `spx session handoff`, still in TODO.

Workflow 03 prints:

```text
Canonical continuation: rewrite 2026-04-24_08-10-44 in place (Path B)
Sessions to archive after closure: 2026-04-24_02-11-00
```

Workflow 04 under Path B:

1. Resolves the artifact id as `2026-04-24_08-10-44`.
2. Does NOT run `spx session handoff` — a second handoff would violate the one-handoff end state.
3. Writes (overwrites) `.spx/sessions/todo/2026-04-24_08-10-44.md` with cumulative scope: the claimed session's remaining context, the ten unpushed commits, the four committed `PLAN.md` escape hatches, the live verification facts, and the remaining deploy path.
4. Archives the in-scope set:

   ```bash
   spx session archive 2026-04-24_02-11-00
   ```

5. Confirms: "Canonical continuation: rewrote `2026-04-24_08-10-44` in place (Path B). Session-owned work committed. Archived scope: `2026-04-24_02-11-00`."

End state: DOING is empty; TODO contains exactly one handoff (`2026-04-24_08-10-44`, the rewritten canonical).

</example_rewrite_in_place>
