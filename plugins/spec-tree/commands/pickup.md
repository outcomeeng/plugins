---
name: pickup
description: Load a handoff document to continue previous work
argument-hint: [--list]
allowed-tools: Read, Bash(spx:*), Bash(git:*), AskUserQuestion, Glob, Skill
---

<context>
**Git status:**
!`git status --short || echo "Not in a git repo"`

**Available sessions:**
!`spx session todo || echo 'Ask user to install spx CLI: "npm install --global @outcomeeng/spx"'`
</context>

<objective>

Load and claim a handoff session to continue work from a previous context. The pickup workflow is structured to ensure the receiving agent does not repeat the previous agent's mistakes:

1. **Skills first** — know what to invoke before touching any code
2. **Nodes second** — understand what was worked on and its current state
3. **Escape hatches** — check for PLAN.md / ISSUES.md in node directories
4. **`/contextualizing` BEFORE any work** — this is non-negotiable, not one option among many

**⚠️ NEVER propose fixing bugs, writing code, or any implementation work before `/contextualizing` has been invoked on the target node.**

</objective>

<session_management>

## Session Commands

All session management uses `spx session` CLI commands:

```bash
# List sessions in status `todo`
spx session todo [--json]

# List sessions by status (includes `todo` and `doing` by default)
spx session list [--status todo|doing|archive] [--json]

# Claim a session (move todo -> doing)
spx session pickup [id] [--auto]

# Show session content
spx session show <id>
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

<workflow>

## Step 1: Claim session

### Default (no arguments)

Claim the **highest priority** (or oldest if same priority) session:

```bash
spx session pickup --auto
```

The `spx` CLI handles:

- Selecting highest priority (or oldest if tied)
- Atomic move from `todo/` to `doing/`
- Outputting `<PICKUP_ID>...</PICKUP_ID>` marker for `/handoff` to find
- Displaying the claimed session content

### With `--list` flag

Check if `$ARGUMENTS` contains `--list` to activate list mode.

1. Get all todo sessions:
   ```bash
   spx session todo --json
   ```

2. Parse each session to extract:
   - Session ID
   - Priority and tags from frontmatter
   - Nodes from `<nodes>` section (or `<original_task>` for legacy sessions)

3. Use `AskUserQuestion` to present options:

   ```json
   {
     "questions": [{
       "question": "Which handoff would you like to load?",
       "header": "Handoff",
       "multiSelect": false,
       "options": [
         { "label": "2026-03-29 14:22 [high] (test-harness)", "description": "TDD step 7 on 43-fixtures.enabler — tests written, implementation needed" },
         { "label": "2026-03-28 09:15 [medium] (auth)", "description": "Spec authoring on 32-auth.outcome — assertions need review" }
       ]
     }]
   }
   ```

4. Claim the chosen session:
   ```bash
   spx session pickup <selected-session-id>
   ```

## Step 2: Present skills checklist

**This step comes BEFORE loading node context.** The skills checklist tells the agent what to invoke and what to avoid.

Read the `<skills>` section from the session file and present it prominently:

### Critical — invoke before starting work

> These skills are REQUIRED. The previous agent identified them as essential.

List each skill with its reasoning.

### Missed — do not repeat these mistakes

> The previous agent skipped these skills and it caused problems. Learn from their experience.

List each missed skill with what went wrong.

### Next action — where to resume

> This is where the previous agent left off.

Show the recommended skill and TDD flow position.

## Step 3: Load node context

For each node in the `<nodes>` section:

1. **Present status**: Show what was done and what remains

2. **Check for escape hatches**:
   ```bash
   Glob: "spx/{node-path}/PLAN.md"
   Glob: "spx/{node-path}/ISSUES.md"
   ```
   If found, read and present them — these contain important non-durable context the previous agent persisted as a hedge.

3. **Suggest context loading**:
   "To load full spec context for this node, invoke `/contextualizing {node-path}`"

## Step 4: Present persisted artifacts

Show the `<persisted>` section:

- What was committed (the agent can trust these are in place)
- What is uncommitted (may need `/commit` before continuing)
- What insights were written to CLAUDE.md/memory/skills
- What escape hatches were written and where

## Step 5: Present coordination context

Show the `<coordination>` section — cross-cutting context that does not belong to any single node. This may include:

- Why the previous session ended
- Dependencies between nodes
- Environment or setup requirements
- Open questions or pending decisions

## Step 6: Invoke /contextualizing (MANDATORY)

**Do NOT offer the user a choice here. Do NOT propose fixing bugs, writing code, or any other work.**

The ONLY valid next action after presenting the session is to invoke `/contextualizing` on the target node. This is a BLOCKING REQUIREMENT — the spec-tree methodology forbids all work without loaded context.

If the session references multiple nodes, ask which node to start with. Otherwise, invoke immediately:

```text
Skill tool → { "skill": "spec-tree:contextualizing", "args": "spx/{node-path}" }
```

After context is loaded, THEN ask how to proceed — the loaded context will inform what options make sense.

## Step 7: Verify coordination claims before triaging

When the coordination section reports failing tests, known bugs, or specific errors, **run them first** before proposing fixes. The coordination section is a point-in-time snapshot; commits may have landed between handoff-write and pickup-claim that resolved listed failures. Running the tests is cheap (one command); triaging a non-existent failure wastes time and risks mis-diagnosis.

This applies after `/contextualizing` (Step 6) completes, as the agent shifts from loading context to proposing action.

</workflow>

<legacy_compatibility>

Sessions created by the legacy `/handoff` command (pre-structured format) use `<original_task>` instead of `<nodes>`. Handle gracefully:

1. If `<nodes>` section is missing, fall back to `<original_task>` + `<work_remaining>`
2. If `<skills>` section is missing, remind the agent to check which skills apply
3. Present legacy sessions with a note: "This session uses the legacy format — skills checklist and node anchoring are not available"

</legacy_compatibility>

<error_handling>

**No sessions directory or empty**:

```
No handoff sessions found in .spx/sessions/todo/
Use `/handoff` to create a handoff document.
```

**Only doing sessions exist**:

```
Found only doing sessions — these are claimed by active agents.
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

</error_handling>

<implementation_notes>

- Session IDs use format: `YYYY-MM-DD_HH-MM-SS`
- Sessions organized in subdirectories: `todo/`, `doing/`, `archive/`
- Extract sections using pseudo-XML tags: `<nodes>`, `<skills>`, `<persisted>`, `<coordination>`
- Handle missing sections gracefully (especially for legacy sessions)
- Priority order: high > medium > low (oldest first within same priority)
- Limit list to most recent 10 sessions to keep UI manageable
- `spx` CLI handles atomic operations — never touch any session files manually except to read them

</implementation_notes>

<system_description>

This command works with `/handoff` to create a self-organizing handoff system:

1. **`/pickup`** claims a session: moves from `todo` to `doing`
2. Agent works on the claimed task, guided by the skills checklist and node context
3. **`/handoff`** creates new session in `todo` AND moves the `doing` session to `archive`
4. Result: Only available `todo` sessions remain, no manual cleanup needed

**Parallel agents**: Multiple agents can run `/pickup` simultaneously — the `spx` CLI ensures atomic operations and no race conditions.

</system_description>

<success_criteria>

A successful pickup:

- [ ] Session claimed via `spx session pickup`
- [ ] `<PICKUP_ID>` marker present in conversation for `/handoff` to find later
- [ ] Skills checklist presented BEFORE any work starts
- [ ] Each anchored node's status presented
- [ ] PLAN.md / ISSUES.md checked and read if present
- [ ] Persisted artifacts acknowledged
- [ ] `/contextualizing` invoked on target node — NOT offered as an option, just done
- [ ] Failures listed in coordination are verified against current state before triaging
- [ ] Agent knows which skills to invoke and which to avoid

</success_criteria>
