---
name: pickup
description: Load a handoff document to continue previous work
argument-hint: [--list]
allowed-tools: Read, Bash(spx:*), Bash(git:*), AskUserQuestion
---

## Current Context

**Git status:**
!`git status --short || echo "Not in a git repo"`

**Available sessions:**
!`spx session list`

Load a handoff document from `.spx/sessions/todo/` to continue previous work in the current context.

## Session Commands

All session management uses `spx session` CLI commands:

```bash
# List sessions by status
spx session list [--status todo|doing|archive] [--json]

# Claim a session (move todo -> doing)
spx session pickup [id] [--auto]

# Show session content
spx session show <id>
```

## Behavior

### Default (no arguments)

Claim and load the **highest priority** (or oldest if same priority) session using `--auto`.

### With `--list` flag

Check if `$ARGUMENTS` contains `--list` to activate list mode.

Present all available todo sessions and use `AskUserQuestion` tool to let the user select which one to load.

## Workflow

### 1. List Available Sessions

```bash
# List all todo sessions
spx session list --status todo

# Or get JSON for parsing
spx session list --status todo --json
```

### 2a. Default Mode (auto-claim)

1. Claim the highest priority available session:
   ```bash
   spx session pickup --auto
   ```
   The CLI handles:
   - Selecting highest priority (or oldest if tied)
   - Atomic move from `todo/` to `doing/`
   - Outputting `<PICKUP_ID>...</PICKUP_ID>` marker for `/handoff` to find
   - Displaying the claimed session content

2. Present formatted summary including:
   - Metadata (timestamp, branch, project)
   - Original task
   - Work remaining
   - Note that this session has been claimed for this session

3. Offer to read files mentioned in the handoff if they exist

### 2b. List Mode (`--list` flag)

1. Get all todo sessions:
   ```bash
   spx session list --status todo --json
   ```

2. Parse each session to extract:
   - Session ID (e.g., `2026-01-08_16-30-22`)
   - Priority and tags from metadata
   - Original task from `<original_task>` section

3. Use `AskUserQuestion` tool to present options:
   - **Question**: "Which handoff would you like to load?"
   - **Header**: "Handoff"
   - **Options**: Each session with format:
     - **Label**: `YYYY-MM-DD HH:MM [priority] (tags)`
     - **Description**: First 100 chars of original task

Example `AskUserQuestion` call:

```json
{
  "questions": [
    {
      "question": "Which handoff would you like to load?",
      "header": "Handoff",
      "multiSelect": false,
      "options": [
        {
          "label": "2026-01-08 16:30 [high] (refactor)",
          "description": "Implement /handoff and /pickup commands for context preservation"
        },
        {
          "label": "2026-01-08 14:15 [medium] (auth)",
          "description": "Add OAuth2 authentication flow with token refresh"
        },
        {
          "label": "2026-01-07 22:45 [low]",
          "description": "Debug performance issues in API gateway"
        }
      ]
    }
  ]
}
```

1. After user selection, claim the chosen session:
   ```bash
   spx session pickup <selected-session-id>
   ```

2. Present the claimed session content

### 3. Present Handoff Content

Format the handoff in a clear, readable way:

```markdown
# Handoff: [Session ID]

**Project**: [project name]
**Branch**: [branch name]
**Status**: [git status]
**Priority**: [priority]
**Tags**: [tags]

## Original Task

[Original task description]

## Work Completed

[Summary of completed work]

## Work Remaining

[List of remaining tasks]

## Attempted Approaches

[Failed approaches and learnings]

## Critical Context

[Important context to preserve]

## Current State

[Current state of deliverables]
```

### 4. Offer Next Steps

After presenting the handoff, use the `AskUserQuestion` to ask the user:

- "Would you like me to read any files mentioned in the handoff?"
- "Should I continue with the work remaining?"
- "Do you want to modify the plan?"

---

## Error Handling

**No sessions directory or empty**:

```
No handoff sessions found in .spx/sessions/todo/
Use `/handoff` to create a handoff document.
```

**Only doing sessions exist**:

```
Found only doing sessions - these are claimed by active sessions.

Current doing sessions:
[list from: spx session list --status doing]
```

Present options via `AskUserQuestion`:

- Wait for other sessions to complete
- Check if doing sessions are orphaned (from abandoned sessions)

**Invalid session format**:

```
Warning: Session [id] appears to be corrupted or incomplete.
Showing raw content:
[show file content via spx session show <id>]
```

## Examples

### Load highest priority session

```bash
/pickup
```

### Select from list

```bash
/pickup --list
```

## Implementation Notes

- Session IDs use format: `YYYY-MM-DD_HH-MM-SS`
- Sessions organized in subdirectories: `todo/`, `doing/`, `archive/`
- Extract sections using XML tags: `<metadata>`, `<original_task>`, etc.
- Handle missing sections gracefully
- Priority order: high > medium > low (oldest first within same priority)
- Limit list to most recent 10 sessions to keep UI manageable
- CLI handles atomic operations - no manual file moves needed

## Self-Organizing Handoff System

This command works with `/handoff` to create a self-organizing handoff workflow:

**The Claim Mechanism:**

1. `/pickup` claims a session using `spx session pickup`
2. CLI atomically moves session from `todo/` to `doing/`
3. Only one agent can successfully claim each session
4. Agent works on the claimed session throughout the conversation

**Automatic Cleanup:**

- When the session ends with `/handoff`, it:
  - Creates a new session in `todo/`
  - Deletes the `doing/` session (superseded by new handoff)
  - Leaves only available `todo/` sessions

**Parallel Agent Safety:**

- Multiple agents can run `/pickup` simultaneously
- CLI ensures atomic operations - no race conditions
- Priority-based selection with FIFO within same priority
- No duplicate work

**Visual Status:**

- `todo/*.md` = Available for pickup
- `doing/*.md` = Currently being worked on
- `archive/*.md` = Completed (future)
