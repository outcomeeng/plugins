---
name: handoff
description: Create timestamped handoff document for continuing work in a fresh context
argument-hint: [--prune]
allowed-tools:
  - Read
  - Edit
  - Glob
  - Bash(spx:*)
  - Bash(git:*)
---

<context>
**Working Directory:**
!`pwd`

**Git Status:**
!`git status --short || echo "Not in a git repo"`

**Current Branch:**
!`git branch --show-current || echo "Not in a git repo"`

**Current Sessions:**
!`find .spx/sessions -name '*.md' -type f 2>/dev/null | sort`

Create a comprehensive, detailed handoff document with UTC timestamp that captures all context from the current conversation. This allows continuing the work in a fresh context with complete precision.
</context>

<session_management>

## Session Operations

All session management uses `spx session` CLI commands.

### Directory Structure

```text
.spx/sessions/
├── todo/      # Available for pickup
├── doing/     # Currently claimed
└── archive/   # Completed
```

### CLI Commands

```bash
# Create a new session (returns <HANDOFF_ID> and <SESSION_FILE>)
spx session handoff

# List sessions by status
spx session list [--status todo|doing|archive]

# Archive a doing session
spx session archive <session-id>

# Prune old archive sessions
spx session prune

# Delete a session
spx session delete <session-id>
```

</session_management>

<multi_agent_awareness>

**Multiple agents may be working in parallel.** The todo queue contains work for ALL agents, not just this session. Never archive or delete todo sessions — they belong to the shared work queue.

- `todo/` = Shared work queue (DO NOT archive others' work)
- `doing/` = Claimed by active agents (only archive YOUR claimed session)
- `archive/` = Completed work (safe to prune old entries)

</multi_agent_awareness>

<arguments>
**`--prune`**: After successfully writing the new handoff, delete old **archive** sessions to prevent accumulation. Does NOT touch the todo queue.

Check for prune flag: `$ARGUMENTS` will contain `--prune` if present.

**Note:** Prune only affects archive sessions. Todo sessions are the shared work queue for all agents.

</arguments>

<instructions>
**PRIORITY: Comprehensive detail and precision over brevity.** The goal is to enable someone (or a fresh Claude instance) to pick up exactly where you left off with zero information loss.

Adapt the level of detail to the task type (coding, research, analysis, writing, configuration, etc.) but maintain comprehensive coverage:

1. **Original Task**: Identify what was initially requested (not new scope or side tasks)

2. **Work Completed**: Document everything accomplished in detail
   - All artifacts created, modified, or analyzed (files, documents, research findings, etc.)
   - Specific changes made (code with line numbers, content written, data analyzed, etc.)
   - Actions taken (commands run, APIs called, searches performed, tools used, etc.)
   - Findings discovered (insights, patterns, answers, data points, etc.)
   - Decisions made and the reasoning behind them

3. **Work Remaining**: Specify exactly what still needs to be done
   - Break down remaining work into specific, actionable steps
   - Include precise locations, references, or targets (file paths, URLs, data sources, etc.)
   - Note dependencies, prerequisites, or ordering requirements
   - Specify validation or verification steps needed

4. **Attempted Approaches**: Capture everything tried, including failures
   - Approaches that didn't work and why they failed
   - Errors encountered, blockers hit, or limitations discovered
   - Dead ends to avoid repeating
   - Alternative approaches considered but not pursued

5. **Critical Context**: Preserve all essential knowledge
   - Key decisions and trade-offs considered
   - Constraints, requirements, or boundaries
   - Important discoveries, gotchas, edge cases, or non-obvious behaviors
   - Relevant environment, configuration, or setup details
   - Assumptions made that need validation
   - References to documentation, sources, or resources consulted

6. **Current State**: Document the exact current state
   - Status of deliverables (complete, in-progress, not started)
   - What's committed, saved, or finalized vs. what's temporary or draft
   - Any temporary changes, workarounds, or open questions
   - Current position in the workflow or process

</instructions>

<output_format>

Write this content to `.spx/sessions/todo/<session-id>.md` using the Write tool:

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

<original_task>
[The specific task that was initially requested - be precise about scope]
</original_task>

<work_completed>
[Comprehensive detail of everything accomplished:
- Artifacts created/modified/analyzed (with specific references)
- Specific changes, additions, or findings (with details and locations)
- Actions taken (commands, searches, API calls, tool usage, etc.)
- Key discoveries or insights
- Decisions made and reasoning
- Side tasks completed]

</work_completed>

<work_remaining>
[Detailed breakdown of what needs to be done:
- Specific tasks with precise locations or references
- Exact targets to create, modify, or analyze
- Dependencies and ordering
- Validation or verification steps needed]

</work_remaining>

<attempted_approaches>
[Everything tried, including failures:
- Approaches that didn't work and why
- Errors, blockers, or limitations encountered
- Dead ends to avoid
- Alternative approaches considered but not pursued]

</attempted_approaches>

<critical_context>
[All essential knowledge for continuing:
- Key decisions and trade-offs
- Constraints, requirements, or boundaries
- Important discoveries, gotchas, or edge cases
- Environment, configuration, or setup details
- Assumptions requiring validation
- References to documentation, sources, or resources]

</critical_context>

<current_state>
[Exact state of the work:
- Status of deliverables (complete/in-progress/not started)
- What's finalized vs. what's temporary or draft
- Temporary changes or workarounds in place
- Current position in workflow or process
- Any open questions or pending decisions]

</current_state>
```

</output_format>

<workflow>

1. **Check for claimed session to cleanup**: Search conversation history for `<PICKUP_ID>` marker from a previous `/pickup`. This is the doing session to archive after creating the new handoff.

2. **Gather context**: Collect all information from current conversation for the handoff content. Compose the full handoff text in your working memory following the `<output_format>` section — you will need it in step 4.

3. **Create the session file using `spx session handoff`**:

   Run the CLI command. It creates the file and outputs two markers:
   ```bash
   spx session handoff
   ```
   Parse the output for:
   - `<HANDOFF_ID>session-id</HANDOFF_ID>` — the session identifier
   - `<SESSION_FILE>/path/to/file</SESSION_FILE>` — the absolute path to the created file

   **Save both values.** You need the file path for the next two steps.

4. **Read the created file, then edit it with handoff content**:

   **Step 4a: Read the file** using the Read tool on the `<SESSION_FILE>` path from step 3. You MUST read it before editing — the Edit tool requires a prior read.

   **Step 4b: Edit the file** using the Edit tool. Replace the file's content with your composed handoff text from step 2:
   - YAML frontmatter with priority and tags
   - All sections from `<output_format>`: metadata, original_task, work_completed, work_remaining, attempted_approaches, critical_context, current_state

   **DO NOT use the Write tool.** The file already exists from step 3. Use Edit to replace its content.

5. **Cleanup claimed session**: If a doing session was found in step 1, archive it:
   ```bash
   spx session archive <doing-session-id>
   ```
   Report: "Cleaned up claimed session: [session-id]"

6. **If `--prune` flag is present**:
   ```bash
   spx session prune
   ```
   Report what was deleted. **Never delete todo or doing sessions** — they are the shared work queue.

7. **Confirm handoff created** with session ID.

</workflow>

<example>

**Step 1: Search conversation for `<PICKUP_ID>` from earlier pickup**

Found in conversation: `<PICKUP_ID>2026-01-08_14-59-03</PICKUP_ID>`

**Step 2: Gather context and compose handoff text**

Compose the full handoff content in working memory (all sections from output_format).

**Step 3: Create the session file**

```bash
spx session handoff
```

Output:

```text
<HANDOFF_ID>2026-01-08_16-30-22</HANDOFF_ID>
<SESSION_FILE>/Users/dev/claude/.spx/sessions/todo/2026-01-08_16-30-22.md</SESSION_FILE>
```

**Step 4a: Read the created file**

```
Read: /Users/dev/claude/.spx/sessions/todo/2026-01-08_16-30-22.md
```

**Step 4b: Edit the file with handoff content**

```
Edit: /Users/dev/claude/.spx/sessions/todo/2026-01-08_16-30-22.md
old_string: (the default content from the created file)
new_string: (full handoff content — frontmatter + all sections)
```

The file now contains:

```text
---
priority: medium
tags: [refactor, testing]
---
<metadata>
  timestamp: 2026-01-08T16:30:22Z
  project: claude
  git_branch: main
  git_status: dirty
  working_directory: /Users/dev/claude
</metadata>

<original_task>
Refactor session management to use filesystem operations
</original_task>

<work_completed>
- Updated /handoff command to use direct filesystem operations
- Updated /pickup command to use direct filesystem operations
- Tested full workflow: create -> pickup -> handoff cycle
</work_completed>

<work_remaining>
- Update documentation
- Test parallel agent scenarios
</work_remaining>

<attempted_approaches>
- Tried using ls for listing - find is more robust for missing directories
</attempted_approaches>

<critical_context>
- Session IDs use YYYY-MM-DD_HH-MM-SS format
- Sessions organized in subdirectories: todo/, doing/, archive/
- POSIX mv is atomic at the filesystem level
</critical_context>

<current_state>
- /handoff and /pickup updated and tested
- Missing: documentation updates
</current_state>
```

**Step 5: Cleanup claimed session**

```bash
spx session archive 2026-01-08_14-59-03
```

**Step 6: Confirm to user**

"Handoff created: `2026-01-08_16-30-22`. Cleaned up claimed session: `2026-01-08_14-59-03`"

</example>

<system_description>
This command works with `/pickup` to create a self-organizing handoff system:

1. **`/pickup`** claims a session: moves from `todo/` to `doing/`
2. Agent works on the claimed task throughout the session
3. **`/handoff`** creates new session in `todo/` AND archives the `doing/` session
4. Result: Only available `todo/` sessions remain, no manual cleanup needed

**Parallel agents**: Multiple agents can run `/pickup` simultaneously — POSIX `mv` is atomic at the filesystem level, preventing race conditions.

**Visual Status**:

- `todo/*.md` = Available for pickup (queue of work)
- `doing/*.md` = Currently being worked on (claimed by active session)
- New handoffs are created in `todo/` (ready for next session)

</system_description>
