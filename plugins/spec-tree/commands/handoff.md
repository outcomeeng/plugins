---
name: handoff
description: Create timestamped handoff document for continuing work in a fresh context
argument-hint: [--prune]
allowed-tools:
  - Read
  - Write
  - Bash(spx:*)
  - Bash(git:*)
  - Glob
  - AskUserQuestion
  - Skill
---

<context>
**Working Directory:**
!`pwd`

**Git Status:**
!`git status --short || echo "Not in a git repo"`

**Current Branch:**
!`git branch --show-current || echo "Not in a git repo"`

**Current Sessions:**
!`spx session list || echo 'Ask user to install spx CLI: "npm install --global @outcomeeng/spx"'`

**Spec Tree:**
!`ls spx/*.product.md 2>/dev/null || echo "No spec tree found"`
</context>

<objective>

Handoff is **proper session closure**, not note-taking. The agent must reflect deeply on what it learned before persisting anything — five structured perspectives force introspection that produces the right persistence decisions. The session file is a thin coordination envelope — the last resort for information that can't live anywhere else.

**Reflect, then persist, then hand off.** The reflection (Phase 2) is the most important phase. Without it, the agent will dump a narrative instead of making durable persistence decisions. Stale PLAN.md and DEFICIENCIES.md files are worse than none — the reflection phase catches and fixes them.

</objective>

<persistence_hierarchy>

All information discovered during a session falls into one of four tiers. Persist to the HIGHEST applicable tier.

| Tier | Where                                   | Durability   | When to use                                                                       |
| ---- | --------------------------------------- | ------------ | --------------------------------------------------------------------------------- |
| 1    | Spec tree (`spx/`)                      | Durable      | Spec amendments, test files, assertion updates                                    |
| 2    | Methodology (skills, CLAUDE.md, memory) | Durable      | Reusable patterns, user preferences, coding gotchas                               |
| 3    | Node-local (PLAN.md, DEFICIENCIES.md)   | Escape hatch | Remaining steps, known gaps — non-durable but discoverable via `/contextualizing` |
| 4    | Session file (`.spx/sessions/todo/`)    | Ephemeral    | Coordination only: node list, skill checklist, cross-cutting context              |

**Tier 3 is an escape hatch, not a home.** The agent MUST use `AskUserQuestion` before writing PLAN.md or DEFICIENCIES.md.

</persistence_hierarchy>

<session_management>

## Session Commands

All session management uses `spx session` CLI commands:

```bash
# Create new session (returns file path to edit)
spx session handoff
# Output:
#   <HANDOFF_ID>2026-01-17_15-11-02</HANDOFF_ID>
#   <SESSION_FILE>/path/to/.spx/sessions/todo/2026-01-17_15-11-02.md</SESSION_FILE>

# Then ensure it is empty using the Read tool with <SESSION_FILE> path.
# Then use the Write tool to write content to <SESSION_FILE> path

# List sessions by status (includes `todo` and `doing` by default)
spx session list [--status todo|doing|archive] [--json]

# Archive a session
spx session archive <session-id>
```

## Session Directory Structure

Sessions are organized by status in the **root worktree.**
**IMPORTANT:** The `spx` CLI is aware of Git worktrees and manages all session state in a gitignored directory in the root worktree (i.e., as a sibling to the actual `.git` directory).

The session files are Markdown files within subdirectories of the base `.spx/sessions` directory:

```
.spx/sessions/
├── todo/      # Available for pickup
├── doing/     # Currently claimed
└── archive/   # Completed
```

</session_management>

<multi_agent_awareness>

**Multiple agents may be working in parallel.** The todo queue contains work for ALL agents across ALL worktrees, not just this session. Never archive or even delete todo sessions — they belong to the shared work queue.

- `todo` = Shared work queue (DO NOT archive others' work)
- `doing` = Claimed by active agents (only archive YOUR claimed session)
- `archive` = Completed work (safe to prune old entries)

</multi_agent_awareness>

<arguments>

**`--prune`**: After successfully writing the new handoff, delete old **archive** sessions to prevent accumulation. Does NOT touch the todo queue.

Check for prune flag: `$ARGUMENTS` will contain `--prune` if present.

**Note:** Prune only affects archive sessions. Todo sessions are the shared work queue for all agents.

</arguments>

<workflow>

## Phase 1: Anchor to nodes

Scan the conversation for spec-tree nodes that were worked on. For each node, record:

- Full path (e.g., `spx/21-foo.enabler/32-bar.outcome`)
- What was done (spec authored, tests written, code implemented, etc.)
- Test status (passing, failing, not yet written)
- TDD flow position if applicable (phase 1-8 per `/coding` skill)

**If NO spec-tree nodes were involved in this session**, use `AskUserQuestion`:

```json
{
  "questions": [{
    "question": "This session's work isn't anchored to any spec-tree node. Why?",
    "header": "Node anchor",
    "multiSelect": false,
    "options": [
      { "label": "Create a node now", "description": "Pause handoff to author a node that captures this work, then resume." },
      { "label": "Exploratory / cross-cutting", "description": "Work doesn't belong to a specific node (infrastructure, tooling, research). Proceed with justification." },
      { "label": "Plugin / methodology work", "description": "Work was on the plugin or methodology itself, not on product specs." }
    ]
  }]
}
```

If "Create a node now" → invoke `/authoring` to create the node, then return to this phase.

## Phase 2: Reflect

**Work through all five perspectives internally before presenting anything to the user.** This is the most important phase — it produces the input for everything that follows. Do not rush. Do not skip perspectives.

For each perspective, think about what you learned, what changed, and what the next agent needs. Check existing escape hatches (PLAN.md, DEFICIENCIES.md) against current reality — stale escape hatches are worse than none.

### Perspective 1: Lessons learned

What did you learn during this session that changes how future agents should work on this codebase?

- **User corrections** — things the user had to repeat or correct. What rule would have prevented the mistake?
- **Methodology gaps** — skills that were inadequate or missing. What should change?
- **Coding patterns** — patterns that worked or failed. What should be codified?

For each lesson, determine persistence target:

- Amend a spec (if a spec was wrong or incomplete)
- Update CLAUDE.md (if it's a project-wide rule)
- Update a skill (if it's a methodology gap)
- Session file only (if it's task-specific)

### Perspective 2: Deficiencies identified

What is broken, missing, or wrong that you did not fix?

- **Spec deficiencies** — assertions that are wrong, missing, or untestable
- **Implementation gaps** — known bugs, missing edge cases, incomplete features
- **Test gaps** — assertions without test coverage, tests that don't test what they claim

For each deficiency, determine persistence target:

- Fix the spec directly (if an assertion is wrong — this is a durable fix)
- Write or update DEFICIENCIES.md in the node directory (if the fix is deferred)

**Critical**: Read any existing DEFICIENCIES.md for each anchored node. Check every item — are items listed as open now fixed? Are there new deficiencies not yet listed? A stale DEFICIENCIES.md will mislead the next agent.

### Perspective 3: Insights about the path forward

What do you now understand about how the remaining work should proceed?

- **Approach decisions** — what approach was chosen and why alternatives were rejected
- **Remaining steps** — what concrete steps remain, in what order
- **Dependencies** — what must happen before what

For each insight, determine persistence target:

- Amend a spec (if the insight changes what the spec says)
- Write or update PLAN.md in the node directory (if it's a concrete plan for remaining work)
- Remove PLAN.md (if all planned steps are now complete — a done plan is a stale plan)
- Session file only (if it's coordination context)

**Critical**: Read any existing PLAN.md for each anchored node. Are steps listed as remaining now complete? Is the plan still the right approach? Update or remove — never leave a stale plan.

### Perspective 4: Skills used

Which skills did you invoke, which should you have invoked, and which does the next agent need?

- **Critical skills** — always include `/understanding` and `/contextualizing {node}` for each anchored node, plus language-specific skills that were used
- **Missed skills** — skills that SHOULD have been invoked but were not. What problems did skipping them cause?
- **Next skill** — what specific skill should the receiving agent invoke first, and why

### Perspective 5: Starting point

Where exactly should the next agent begin?

- **Node path** — full path to the node (e.g., `spx/21-foo.enabler/32-bar.outcome`)
- **TDD flow position** — which phase (1-8) per the `/coding` skill
- **First action** — the specific skill invocation that resumes work

## Phase 3: Propose persistence plan

Present the combined output of all five perspectives as a single `AskUserQuestion` with `multiSelect: true`. Group items by type:

```json
{
  "questions": [{
    "question": "Review persistence proposal — select items to approve:",
    "header": "Persist",
    "multiSelect": true,
    "options": [
      { "label": "[Lesson] summary", "description": "→ target: CLAUDE.md / spec / skill (with reason)" },
      { "label": "[Deficiency] summary", "description": "→ target: fix spec / DEFICIENCIES.md in spx/{node}" },
      { "label": "[Insight] summary", "description": "→ target: amend spec / PLAN.md in spx/{node} / remove stale PLAN.md" },
      { "label": "[Skip] N items", "description": "→ session file only (coordination context)" }
    ]
  }]
}
```

Items the user does not select are included in the session file's `<coordination>` section as ephemeral context. Items the user selects are written in Phase 4.

**AskUserQuestion is limited to 4 options.** If there are more than 3 actionable items, batch them by perspective (one question per perspective with items as options). The "[Skip]" option always appears as the last option in the last question.

## Phase 4: Execute and hand off

### Step 1: Write approved persistence items

For each approved item from Phase 3:

- **Spec amendments**: Edit the spec file directly
- **CLAUDE.md / memory / skill updates**: Write the insight
- **DEFICIENCIES.md**: Write or update in the node directory. Remove fixed items, add new ones.
- **PLAN.md**: Write, update, or remove in the node directory. Never leave a stale plan.

### Step 2: Record committed vs uncommitted state

For each anchored node, check `git status` and record what is committed vs uncommitted. Do NOT commit — that is `/commit`'s job.

### Step 3: Create session file

1. **Check for claimed session**: Search conversation for `<PICKUP_ID>` marker from `spx session pickup`. This is the doing session to archive after creating the new handoff.

2. **Create handoff session**:
   ```bash
   spx session handoff
   ```
   Parse output for `<HANDOFF_ID>` and `<SESSION_FILE>`.

3. **Read the session file** to confirm it exists and is empty.

4. **Write the session file** using the format in the `<session_format>` section. The `<skills>` section comes from Perspective 4, the `<nodes>` section from Perspective 5, and the `<coordination>` section from unapproved items in Phase 3.

5. **Archive claimed session** (if found in step 1):
   ```bash
   spx session archive <doing-session-id>
   ```

6. **If `--prune` flag is present**:
   ```bash
   spx session list --status archive --json
   spx session delete <archive-session-id>
   ```
   **Never delete todo or doing sessions.**

7. **Confirm** handoff created with session ID.

</workflow>

<session_format>

Write this content to `<SESSION_FILE>` using the Write tool:

```text
---
priority: medium
tags: [optional, tags]
---
<metadata>
  timestamp: [UTC timestamp]
  project: [Project name from cwd]
  git_branch: [Current branch]
  git_status: [clean | dirty]
  working_directory: [Full path]
</metadata>

<nodes>
Spec-tree nodes worked on. The receiving agent should invoke
`/contextualizing` on each before starting work.

- `spx/{path-to-node}`
  - Status: [tests passing | partially implemented | spec only | architected | etc.]
  - Done: [What was accomplished on this node]
  - Remaining: [What's left — omit if captured in PLAN.md]
  - Escape hatches: [PLAN.md written | DEFICIENCIES.md written | none]

</nodes>

<skills>

## Critical — invoke before starting work
- `/understanding` — load spec tree methodology
- `/contextualizing {node-path}` — load target context for each node above

## Missed — caused problems when skipped
- [skill name] — [what went wrong and why it matters]

## Next action
- [skill to invoke] — [what to do and why]
- TDD flow position: phase [N] ([phase name]) on `spx/{node-path}`

</skills>

<persisted>
What was captured durably during session closure.

- Committed: [files committed during this session]
- Uncommitted: [files modified but not yet committed — may need `/commit`]
- Insights: [what was written to CLAUDE.md, memory, or skills]
- Escape hatches: [PLAN.md / DEFICIENCIES.md written and in which nodes]

</persisted>

<coordination>
Cross-cutting context that doesn't belong to any single node.
Only include information that CANNOT be derived from the spec tree or git history.

- [Why the session ended]
- [Dependencies between nodes being worked on]
- [Environment or setup notes]
- [Open questions or pending decisions]

</coordination>
```

</session_format>

<example>

**Phase 1: Identify anchored nodes**

Nodes worked on:

- `spx/21-test-harness.enabler/32-temp-files.enabler` — tests written and passing, implementation complete
- `spx/21-test-harness.enabler/43-fixtures.enabler` — spec authored, tests written but failing

**Phase 2: Reflect**

Agent works through all five perspectives internally:

1. **Lessons**: User corrected import pattern twice — relative imports where absolute were required. Rule: "always use absolute imports from the package root." Also: `tempfile.NamedTemporaryFile` needs `delete=False` on Windows — a coding pattern worth codifying.
2. **Deficiencies**: No existing DEFICIENCIES.md. The `43-fixtures.enabler` spec has 5 assertions but 2 are untestable without the implementation — not a deficiency, just the TDD sequence.
3. **Insights**: Existing PLAN.md in `43-fixtures.enabler` is stale — steps 1-3 are complete, only steps 4-5 remain. The approach (context managers over explicit cleanup) was validated and should stay.
4. **Skills**: Used `/testing-python`, skipped `/coding-python` on first attempt which caused import violations. Next agent must invoke `/coding-python` before writing implementation.
5. **Starting point**: `43-fixtures.enabler`, TDD phase 7 (implement), invoke `/coding-python`.

**Phase 3: Propose persistence plan**

Agent presents:

```text
AskUserQuestion (multiSelect: true):
"Review persistence proposal — select items to approve:"

☑ [Lesson] Add to CLAUDE.md: "always use absolute imports from package root"
☑ [Lesson] Add to CLAUDE.md: "tempfile.NamedTemporaryFile needs delete=False on Windows"
☑ [Insight] Update PLAN.md in 43-fixtures.enabler: remove completed steps 1-3, keep 4-5
☐ [Skip] 2 items → session file only (skills audit, coordination)
```

User approves first three items.

**Phase 4: Execute and hand off**

1. Writes both CLAUDE.md entries
2. Updates PLAN.md — removes steps 1-3, keeps steps 4-5
3. Records git state: `32-temp-files.enabler` committed, `43-fixtures.enabler/tests/` uncommitted
4. Creates session file:

```bash
spx session handoff
```

Write to `<SESSION_FILE>`:

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
- `/coding-python` — skipped initially, led to import pattern violations (relative imports where absolute were required). MUST invoke before writing implementation code.

## Next action
- `/coding-python` — continue TDD flow for fixtures enabler
- TDD flow position: phase 7 (implement) on `spx/21-test-harness.enabler/43-fixtures.enabler`

</skills>

<persisted>
What was captured durably during session closure.

- Committed: `spx/21-test-harness.enabler/32-temp-files.enabler/` (spec + tests + implementation)
- Uncommitted: `spx/21-test-harness.enabler/43-fixtures.enabler/tests/` (2 test files)
- Insights: Added Windows tempfile caveat to CLAUDE.md
- Escape hatches: PLAN.md in `spx/21-test-harness.enabler/43-fixtures.enabler/`

</persisted>

<coordination>
Cross-cutting context that doesn't belong to any single node.

- Session ended due to context window pressure
- The fixtures enabler depends on temp-files enabler being complete (it is)
- Python 3.11+ required for ExceptionGroup support used in test assertions

</coordination>
```

Archive claimed session:

```bash
spx session archive 2026-03-29_10-15-00
```

Output: `Archived session: 2026-03-29_10-15-00`

Confirm: "Handoff created: `2026-03-29_14-22-00`. Cleaned up claimed session: `2026-03-29_10-15-00`"

</example>

<system_description>

This command works with `/pickup` to create a self-organizing handoff system:

1. **`/handoff`** closes the session: persists to durable tiers first, then creates a thin session file in `todo`
2. **`/pickup`** claims a session: moves from `todo` to `doing`, presents skills checklist and node context
3. **`/handoff`** archives the old `doing` session when creating the new one

**Parallel agents**: Multiple agents can run `/pickup` simultaneously — the CLI handles atomic operations to prevent conflicts.

**Defense in depth**: If a session is never picked up, work survives through:

- Spec amendments and test files in the spec tree (tier 1)
- Insights persisted to skills/CLAUDE.md/memory (tier 2)
- PLAN.md / DEFICIENCIES.md in nodes, discoverable via `/contextualizing` (tier 3)

</system_description>

<success_criteria>

A successful handoff:

- [ ] All anchored nodes identified with status and TDD position
- [ ] All five reflection perspectives worked through (lessons, deficiencies, insights, skills, starting point)
- [ ] Existing PLAN.md and DEFICIENCIES.md checked for staleness — updated or removed if stale
- [ ] Combined persistence proposal presented to user and approved items written
- [ ] Committed vs uncommitted state recorded for each node
- [ ] Session file created via `spx session handoff`
- [ ] Claimed doing session archived (if applicable)
- [ ] Session file is a thin coordination envelope — bulk of value persisted durably

</success_criteria>
