---
name: handing-off
description: ALWAYS invoke this skill when closing a spec-tree work session, writing a handoff, preparing continuation context for another agent, or releasing work into the shared session queue. NEVER create a spec-tree handoff directly without this skill.
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

Handoff is **proper session closure**, not note-taking. Reflect deeply on what was learned before persisting anything — five structured perspectives force introspection that produces the right persistence decisions. The session file is a thin coordination envelope — the last resort for information that can't live anywhere else.

**Reflect, then persist, then hand off.** The reflection (Step 2) is the most important step. Without it, Claude will dump a narrative instead of making durable persistence decisions. Stale PLAN.md and ISSUES.md files are worse than none — the reflection step catches and fixes them.

</objective>

<persistence_hierarchy>

All information discovered during a session falls into one of four tiers. Persist to the HIGHEST applicable tier.

| Tier | Where                                   | Durability   | When to use                                                                       |
| ---- | --------------------------------------- | ------------ | --------------------------------------------------------------------------------- |
| 1    | Spec tree (`spx/`)                      | Durable      | Spec amendments, test files, assertion updates                                    |
| 2    | Methodology (skills, CLAUDE.md, memory) | Durable      | Reusable patterns, user preferences, coding gotchas                               |
| 3    | Node-local (PLAN.md, ISSUES.md)         | Escape hatch | Remaining steps, known gaps — non-durable but discoverable via `/contextualizing` |
| 4    | Session file (`.spx/sessions/todo/`)    | Ephemeral    | Coordination only: node list, skill checklist, cross-cutting context              |

**Tier 3 is an escape hatch, not a home.** MUST use `AskUserQuestion` before writing PLAN.md or ISSUES.md.

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

**`--no-session`**: Run the full reflection and persistence protocol (steps 1–3) but skip session file creation in step 4. All approved items are persisted to their durable targets (specs, CLAUDE.md, skills, memory, escape hatches). Unapproved items are dropped — there is no session file to hold them.

Use `--no-session` (or the `/release` alias) when closing a session without handing off to another agent — the work is either complete or the durable persistence is sufficient for any future agent to reconstruct context via `/contextualizing`.

**`--prune`**: After successfully writing the new handoff, delete old **archive** sessions to prevent accumulation. Does NOT touch the todo queue. Ignored when `--no-session` is set.

Check for flags: `$ARGUMENTS` will contain `--no-session` and/or `--prune` if present.

**Note:** Prune only affects archive sessions. Todo sessions are the shared work queue for all agents.

</arguments>

<workflow>

## Step 1: Anchor to nodes

Scan the conversation for spec-tree nodes that were worked on. For each node, record:

- Full path (e.g., `spx/21-foo.enabler/32-bar.outcome`)
- What was done (spec authored, tests written, code implemented, etc.)
- Test status (passing, failing, not yet written)
- TDD flow position if applicable (step 1-8 per `/applying` skill)

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

If "Create a node now" → invoke `/authoring` to create the node, then return to this step.

## Step 2: Reflect

**Work through all five perspectives internally before presenting anything to the user.** This is the most important step — it produces the input for everything that follows. Do not rush. Do not skip perspectives.

For each perspective, think about what you learned, what changed, and what the next agent needs. Check existing escape hatches (PLAN.md, ISSUES.md) against current reality — stale escape hatches are worse than none.

### Perspective 1: Lessons learned

What did you learn during this session that changes how future agents should work on this codebase?

- **User corrections** — things the user had to repeat or correct. What rule would have prevented the mistake?
- **Methodology gaps** — skills that were inadequate or missing. What should change?
- **Coding patterns** — patterns that worked or failed. What should be codified?

For each lesson, classify by nature to determine the correct persistence target:

| Lesson nature         | Signal                                                       | Destination                                                                         |
| --------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| **Library / API**     | API change, library behavior, version gotcha                 | Language plugin `coding-*` skill references (e.g., `coding-typescript/references/`) |
| **Methodology**       | Skill invocation order, audit interpretation, process error  | Spec-tree plugin skill (amend skill instructions)                                   |
| **Project rule**      | Convention specific to this codebase, forbidden pattern      | Project `CLAUDE.md`                                                                 |
| **Interaction style** | Response format, verbosity, tone — NOT coding patterns       | Memory (`feedback` type)                                                            |
| **Domain knowledge**  | Who's doing what, external system locations, project context | Memory (`project`/`reference` type)                                                 |
| **Spec correction**   | Assertion was wrong or incomplete                            | Amend the spec file directly                                                        |
| **Task-specific**     | Only relevant to this session's work                         | Session file only                                                                   |

**The nature determines the target — not the other way around.** A library API change belongs in a coding skill reference even if you discovered it in this project. A coding pattern the auditor would reject belongs in `standardizing-*`, not `coding-*`.

### Perspective 2: Deficiencies identified

What is broken, missing, or wrong?

- **Spec deficiencies** — assertions that are wrong, missing, or untestable
- **Implementation gaps** — known bugs, missing edge cases, incomplete features
- **Test gaps** — assertions without test coverage, tests that don't test what they claim
- **Stale references** — old paths, renamed nodes, broken links anywhere in the tree

**Fix it now or defer it — never propose fixing something you can fix right now.**

For each deficiency:

1. **Can you fix it right now?** Stale references, broken links, wrong paths, simple corrections — fix them immediately using Edit/Grep. Do not propose them in Step 3. Do not ask the user. Just fix them and note what you fixed.
2. **Is the fix too large for this session?** Write or update ISSUES.md in the node directory.
3. **Is a spec assertion wrong?** Fix the spec directly — this is a durable fix.

**Critical**: Read any existing ISSUES.md for each anchored node. Check every item — are items listed as open now fixed? Are there new deficiencies not yet listed? A stale ISSUES.md will mislead the next agent.

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
- **TDD flow position** — which step (1-8) per the `/applying` skill
- **First action** — the specific skill invocation that resumes work

## Step 3: Propose persistence plan

**Only items that require user approval appear here.** Deficiencies you already fixed in Step 2 are done — report them as completed work, not as proposals. The proposal contains lessons (methodology/CLAUDE.md/memory changes), deferred issues (ISSUES.md), and plan updates (PLAN.md) — things where the user should verify the target is correct.

Present the combined output of all five perspectives as a single `AskUserQuestion` with `multiSelect: true`. Group items by type:

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

**Lesson labels MUST include the destination type** from the Perspective 1 taxonomy. Examples:

```text
☑ [Lesson → coding-typescript refs] fast-check v4: fc.stringOf → fc.string({ unit: ... })
☑ [Lesson → standardizing-typescript-arch] ADR audit: 'no ADR exists' is REJECT, not N/A
☑ [Lesson → spec-tree plugin] Invoke /contextualizing before suggesting handoff
☑ [Lesson → CLAUDE.md] Require git mv for file moves
```

This lets the user verify at a glance that each lesson is going to the right place.

Items the user selects are written in Step 4. Items the user does not select are included in the session file's `<coordination>` section as ephemeral context — or dropped entirely if `--no-session` is set.

**AskUserQuestion is limited to 4 options.** If there are more than 3 actionable items, batch them by perspective (one question per perspective with items as options). The "[Skip]" option always appears as the last option in the last question.

## Step 4: Execute and hand off

### Step 1: Write approved persistence items

For each approved item from Step 3:

- **Spec amendments**: Edit the spec file directly
- **CLAUDE.md / memory / skill updates**: Write the insight
- **ISSUES.md**: Write or update in the node directory. Remove fixed items, add new ones.
- **PLAN.md**: Write, update, or remove in the node directory. Never leave a stale plan.

### Step 2: Record committed vs uncommitted state

For each anchored node, check `git status` and record what is committed vs uncommitted. Do NOT commit — that is `/commit`'s job.

### Step 3: Create session file (skip if `--no-session`)

**If `--no-session` is set:** Skip this entire step. Archive any claimed doing session (step 3.5 below), then confirm: "Session released. All approved items persisted to durable targets. No session file created."

**Otherwise, proceed with session file creation:**

1. **Check for claimed session**: Search conversation for `<PICKUP_ID>` marker from `spx session pickup`. This is the doing session to archive after creating the new handoff.

2. **Create handoff session**:
   ```bash
   spx session handoff
   ```
   Parse output for `<HANDOFF_ID>` and `<SESSION_FILE>`.

3. **Read the session file** to confirm it exists and is empty.

4. **Write the session file** using the format in the `<session_format>` section. The `<skills>` section comes from Perspective 4, the `<nodes>` section from Perspective 5, and the `<coordination>` section from unapproved items in Step 3.

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
  - Escape hatches: [PLAN.md written | ISSUES.md written | none]

</nodes>

<skills>

## Critical — invoke before starting work
- `/understanding` — load spec tree methodology
- `/contextualizing {node-path}` — load target context for each node above

## Missed — caused problems when skipped
- [skill name] — [what went wrong and why it matters]

## Next action
- [skill to invoke] — [what to do and why]
- TDD flow position: step [N] ([step name]) on `spx/{node-path}`

</skills>

<persisted>
What was captured durably during session closure.

- Committed: [files committed during this session]
- Uncommitted: [files modified but not yet committed — may need `/commit`]
- Insights: [what was written to CLAUDE.md, memory, or skills]
- Escape hatches: [PLAN.md / ISSUES.md written and in which nodes]

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

**Step 1: Identify anchored nodes**

Nodes worked on:

- `spx/21-test-harness.enabler/32-temp-files.enabler` — tests written and passing, implementation complete
- `spx/21-test-harness.enabler/43-fixtures.enabler` — spec authored, tests written but failing

**Step 2: Reflect**

Agent works through all five perspectives internally:

1. **Lessons**: User corrected import pattern twice — relative imports where absolute were required. Rule: "always use absolute imports from the package root." Also: `tempfile.NamedTemporaryFile` needs `delete=False` on Windows — a library gotcha worth persisting.
2. **Deficiencies**: No existing ISSUES.md. The `43-fixtures.enabler` spec has 5 assertions but 2 are untestable without the implementation — not a deficiency, just the TDD sequence.
3. **Insights**: Existing PLAN.md in `43-fixtures.enabler` is stale — steps 1-3 are complete, only steps 4-5 remain. The approach (context managers over explicit cleanup) was validated and should stay.
4. **Skills**: Used `/testing-python`, skipped `/coding-python` on first attempt which caused import violations. Next agent must invoke `/coding-python` before writing implementation.
5. **Starting point**: `43-fixtures.enabler`, TDD step 7 (implement), invoke `/coding-python`.

**Step 3: Propose persistence plan**

Agent presents:

```text
AskUserQuestion (multiSelect: true):
"Review persistence proposal — select items to approve:"

☑ [Lesson → CLAUDE.md] Always use absolute imports from package root
☑ [Lesson → coding-python refs] tempfile.NamedTemporaryFile needs delete=False on Windows
☑ [Insight] Update PLAN.md in 43-fixtures.enabler: remove completed steps 1-3, keep 4-5
☐ [Skip] 2 items → session file only (skills audit, coordination)
```

User approves first three items.

**Step 4: Execute and hand off**

1. Writes CLAUDE.md entry (absolute imports), adds tempfile caveat to `coding-python/references/`
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
- TDD flow position: step 7 (implement) on `spx/21-test-harness.enabler/43-fixtures.enabler`

</skills>

<persisted>
What was captured durably during session closure.

- Committed: `spx/21-test-harness.enabler/32-temp-files.enabler/` (spec + tests + implementation)
- Uncommitted: `spx/21-test-harness.enabler/43-fixtures.enabler/tests/` (2 test files)
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
- PLAN.md / ISSUES.md in nodes, discoverable via `/contextualizing` (tier 3)

</system_description>

<success_criteria>

A successful handoff:

- [ ] All anchored nodes identified with status and TDD position
- [ ] All five reflection perspectives worked through (lessons, deficiencies, insights, skills, starting point)
- [ ] Existing PLAN.md and ISSUES.md checked for staleness — updated or removed if stale
- [ ] Combined persistence proposal presented to user and approved items written
- [ ] Committed vs uncommitted state recorded for each node
- [ ] Session file created via `spx session handoff`
- [ ] Claimed doing session archived (if applicable)
- [ ] Session file is a thin coordination envelope — bulk of value persisted durably

</success_criteria>
