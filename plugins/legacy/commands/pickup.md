---
name: pickup
description: Load a handoff document to continue previous work
argument-hint: [--list]
allowed-tools:
  - Read
  - Glob
  - Bash(mv:*)
  - Bash(mkdir:*)
  - Bash(find:*)
  - Bash(git:*)
  - AskUserQuestion
---

## Current Context

**Git status:**
!`git status --short || echo "Not in a git repo"`

**Available sessions:**
!`find .spx/sessions/todo -name '*.md' -type f 2>/dev/null | sort`

Load a handoff document from `.spx/sessions/todo/` to continue previous work in the current context.

## Session Operations

All session management uses direct filesystem operations — no external CLI required.

### Directory Structure

```
.spx/sessions/
├── todo/      # Available for pickup
├── doing/     # Currently claimed
└── archive/   # Completed
```

### Listing Sessions

```bash
# Todo sessions (available for pickup)
find .spx/sessions/todo -name '*.md' -type f 2>/dev/null | sort

# Doing sessions (currently claimed)
find .spx/sessions/doing -name '*.md' -type f 2>/dev/null | sort
```

### Claiming a Session

```bash
# Move from todo to doing (use -i to avoid clobbering)
mkdir -p .spx/sessions/doing
mv -i .spx/sessions/todo/<session-id>.md .spx/sessions/doing/<session-id>.md
```

### Reading Session Content

Use the **Read** tool on the session file to view its content.

## Behavior

### Default (no arguments)

Claim and load the **highest priority** (or oldest if same priority) session.

### With `--list` flag

Check if `$ARGUMENTS` contains `--list` to activate list mode.

Present all available todo sessions and use `AskUserQuestion` tool to let the user select which one to load.

## Workflow

### 1. Find Available Sessions

Use Glob to find all todo sessions:

```
Glob: .spx/sessions/todo/*.md
```

If no sessions found, report "No handoff sessions found" and suggest using `/handoff`.

### 2a. Default Mode (auto-claim)

1. **Read each todo session** to extract priority from YAML frontmatter:
   - Look for `priority:` in the `---` frontmatter block
   - Priority values: `high`, `medium`, `low` (default: `medium`)

2. **Select the best session**:
   - Sort by priority: `high` > `medium` > `low`
   - Within same priority, pick the oldest (earliest timestamp in filename)

3. **Claim the session** by moving it to `doing/`:
   ```bash
   mkdir -p .spx/sessions/doing
   mv -i .spx/sessions/todo/<session-id>.md .spx/sessions/doing/<session-id>.md
   ```

4. **Emit the pickup marker** for `/handoff` to find later:
   `<PICKUP_ID><session-id></PICKUP_ID>`

5. **Read the claimed session** using the Read tool on `.spx/sessions/doing/<session-id>.md`

6. **Present formatted summary** including:
   - Metadata (timestamp, branch, project)
   - Original task
   - Work remaining
   - Note that this session has been claimed for this conversation

7. **Offer to read files** mentioned in the handoff if they exist

### 2b. List Mode (`--list` flag)

1. **Find all todo sessions** using Glob: `.spx/sessions/todo/*.md`

2. **Read each session** to extract:
   - Session ID from filename (e.g., `2026-01-08_16-30-22`)
   - Priority and tags from YAML frontmatter
   - Original task from `<original_task>` section

3. **Use `AskUserQuestion` tool** to present options:
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

4. **Claim the selected session**:
   ```bash
   mkdir -p .spx/sessions/doing
   mv -i .spx/sessions/todo/<selected-session-id>.md .spx/sessions/doing/<selected-session-id>.md
   ```

5. **Emit the pickup marker**: `<PICKUP_ID><session-id></PICKUP_ID>`

6. **Present the claimed session content**

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

### 4. Build Proposals with Skill Plans

After presenting the handoff, build concrete proposals that tell the user exactly what the agent will do. Each proposal must name the skills the agent will invoke, so the user can evaluate the approach before work begins.

**Step 4a: Inventory available skills**

Read the list of available skills from the system prompt (the `Available skills` section). Note which skills are relevant to the handoff's remaining work.

**Step 4b: For each proposal, plan the skill sequence**

For each possible next step, determine:

1. What is the goal? (one sentence)
2. Which skills will be invoked, in what order?
3. What will each skill produce?

Write this out as a chain: `/skill-1` → `/skill-2` → `/skill-3`

**Step 4c: Format proposals for `AskUserQuestion`**

Each option's `description` field must contain the skill chain. Use the arrow format:

```text
{what will be done} → /skill-1, /skill-2, /skill-3
```

**Step 4d: Present using `AskUserQuestion`**

```json
{
  "questions": [
    {
      "question": "How would you like to proceed?",
      "header": "Next steps",
      "multiSelect": false,
      "options": [
        {
          "label": "Continue remaining work",
          "description": "Implement the status rollup feature → /understanding, /contextualizing, /coding-typescript"
        },
        {
          "label": "Review what changed",
          "description": "Read files from the handoff and assess current state → /contextualizing"
        },
        {
          "label": "Adjust the plan",
          "description": "Discuss changes to scope or approach before starting work"
        }
      ]
    }
  ]
}
```

**Validation before presenting:** Check each proposal. If any option's description does NOT contain a `/skill-name`, go back to Step 4b and add the skill chain. The only exception is purely conversational options like "Adjust the plan" that don't invoke skills.

---

## Error Handling

**No sessions directory or empty**:

```
No handoff sessions found in .spx/sessions/todo/
Use `/handoff` to create a handoff document.
```

**Only doing sessions exist**:

```
Found only doing sessions — these are claimed by active sessions.
```

List doing sessions:

```bash
find .spx/sessions/doing -name '*.md' -type f 2>/dev/null | sort
```

Present options via `AskUserQuestion`:

- Wait for other sessions to complete
- Check if doing sessions are orphaned (from abandoned sessions)

**Invalid session format**:

```
Warning: Session [id] appears to be corrupted or incomplete.
Showing raw content:
```

Read the file directly with the Read tool.

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
- POSIX `mv` is atomic at the filesystem level — safe for parallel agents

## Self-Organizing Handoff System

This command works with `/handoff` to create a self-organizing handoff workflow:

**The Claim Mechanism:**

1. `/pickup` claims a session by moving it from `todo/` to `doing/`
2. POSIX `mv` is atomic — only one agent can successfully claim each session
3. Agent works on the claimed session throughout the conversation

**Automatic Cleanup:**

- When the session ends with `/handoff`, it:
  - Creates a new session in `todo/`
  - Archives the `doing/` session (superseded by new handoff)
  - Leaves only available `todo/` sessions

**Parallel Agent Safety:**

- Multiple agents can run `/pickup` simultaneously
- `mv -i` prevents clobbering if two agents race for the same session
- Priority-based selection with FIFO within same priority
- No duplicate work

**Visual Status:**

- `todo/*.md` = Available for pickup
- `doing/*.md` = Currently being worked on
- `archive/*.md` = Completed
