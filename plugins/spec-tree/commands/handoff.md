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

Handoff is **proper session closure**, not note-taking. The goal is to persist everything the agent learned into durable structures BEFORE creating the session file. The session file is a thin coordination envelope — the last resort for information that can't live anywhere else.

The receiving agent benefits from durable persistence even if the session is never picked up: insights in skills help all future agents, PLAN.md in a node is discoverable via `/contextualizing`, and spec amendments are permanent product truth.

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

## Phase 2: Persist durable artifacts (tier 1)

For each anchored node, check:

- Are there uncommitted spec amendments or test files?
- Are there assertion updates that should be written to the spec?
- Is the test status consistent with the spec assertions?

**Do NOT commit** — that is `/commit`'s job. Record what is committed vs uncommitted so the receiving agent knows the state.

## Phase 3: Persist reusable insights (tier 2)

Scan the conversation for insights that belong in durable methodology:

- **User corrections** — things the user had to repeat or correct → CLAUDE.md or memory
- **Pattern discoveries** — coding patterns, testing patterns, tooling gotchas → relevant skill or CLAUDE.md
- **Skill gaps** — skills that were missing or inadequate → note for skill improvement

Collect all insights, then propose them to the user in a single `AskUserQuestion` with `multiSelect: true`:

```json
{
  "questions": [{
    "question": "Which insights should be persisted durably?",
    "header": "Insights",
    "multiSelect": true,
    "options": [
      { "label": "[Insight summary]", "description": "→ CLAUDE.md: [why this is a project-wide rule]" },
      { "label": "[Insight summary]", "description": "→ Memory: [why this is a user preference]" },
      { "label": "[Insight summary]", "description": "→ Skip: task-specific, include in handoff only" }
    ]
  }]
}
```

Write approved insights BEFORE creating the session file. Record what was persisted in the `<persisted>` section.

## Phase 4: Handle remaining non-durable information (tier 3/4)

Remaining context not captured in tiers 1-2 includes: implementation plans, known gaps, dead ends, environment notes, approach-level mistakes.

**Batch related items by node**, then ask the user for each batch:

```json
{
  "questions": [{
    "question": "Where should the remaining context for `spx/{node}` go?",
    "header": "Disposition",
    "multiSelect": false,
    "options": [
      { "label": "Include in handoff", "description": "Ephemeral — goes in the session file's coordination section" },
      { "label": "Write to PLAN.md", "description": "Escape hatch — remaining steps, written to spx/{node}/PLAN.md" },
      { "label": "Write to DEFICIENCIES.md", "description": "Escape hatch — known gaps or weaknesses, written to spx/{node}/DEFICIENCIES.md" }
    ]
  }]
}
```

Write escape-hatch files if chosen. These are discoverable by `/contextualizing` but are NOT durable spec-tree artifacts.

## Phase 5: Skills audit

Review the conversation and document three categories:

**Critical skills** — essential for the receiving agent:

- Always include `/understanding` and `/contextualizing {target-node}` for each anchored node
- Include language-specific skills that were used (e.g., `/testing-python`, `/coding-python`)

**Missed skills** — skills that SHOULD have been invoked but were not:

- What problems did skipping them cause?
- Why are they crucial? (This prevents the next agent from repeating the mistake)

**Next action** — what the receiving agent should do first:

- Which skill to invoke (e.g., `/reviewing-python` if implementation is complete)
- TDD flow position: which phase (1-8) on which node

## Phase 6: Create session file

1. **Check for claimed session**: Search conversation for `<PICKUP_ID>` marker from `spx session pickup`. This is the doing session to archive after creating the new handoff.

2. **Create handoff session**:
   ```bash
   spx session handoff
   ```
   Parse output for `<HANDOFF_ID>` and `<SESSION_FILE>`.

3. **Read the session file** to confirm it exists and is empty.

4. **Write the session file** using the format in the `<session_format>` section.

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

**Phase 2: Check durable artifacts**

- `32-temp-files.enabler`: 3 test files committed, spec has linked assertions
- `43-fixtures.enabler`: spec committed, 2 test files uncommitted in `tests/`

**Phase 3: Persist insights**

Agent proposes: "Python tempfile.NamedTemporaryFile needs `delete=False` on Windows"
User approves → written to CLAUDE.md

**Phase 4: Disposition of remaining context**

Agent asks about remaining implementation steps for `43-fixtures.enabler`.
User chooses → Write to PLAN.md in `spx/21-test-harness.enabler/43-fixtures.enabler/`

**Phase 5: Skills audit**

- Critical: `/understanding`, `/contextualizing`, `/testing-python`
- Missed: `/coding-python` — skipped in first attempt, led to import pattern violations
- Next: `/coding-python` on `43-fixtures.enabler` (TDD phase 7)

**Phase 6: Create session file**

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
- [ ] Durable artifacts checked — committed vs uncommitted recorded
- [ ] Reusable insights proposed to user and persisted if approved
- [ ] Remaining non-durable context dispositioned via `AskUserQuestion`
- [ ] Skills audit complete — critical, missed, and next action documented
- [ ] Session file created via `spx session handoff`
- [ ] Claimed doing session archived (if applicable)
- [ ] Session file is a thin coordination envelope, not a narrative dump

</success_criteria>
