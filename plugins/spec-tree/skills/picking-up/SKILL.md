---
name: picking-up
description: ALWAYS invoke this skill when resuming prior spec-tree work, loading a handoff session, claiming queued session work, or continuing from another agent's saved context. NEVER continue spec-tree handoff work directly without this skill.
allowed-tools: Read, Bash(spx:*), Bash(git:*), AskUserQuestion, Glob, Skill
---

<context>
**Git status:**
!`git status --short || echo "Not in a git repo"`

**Available sessions:**
!`spx session todo || echo 'Ask user to install spx CLI: "npm install --global @outcomeeng/spx"'`
</context>

<objective>
Load and claim a handoff session to continue work from a previous context without repeating the previous agent's mistakes.

After `/contextualizing`, stop at a post-context checkpoint before any new work starts unless `$ARGUMENTS` explicitly includes `--auto-continue`.

Emit canonical pickup markers keyed by the claimed session id so later workflows can distinguish repeated pickups in the same conversation.

**⚠️ NEVER propose fixing bugs, writing code, or any implementation work before `/contextualizing` has been invoked on the target node.**
</objective>

<session_management>
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

Sessions are organized in `.spx/sessions/` in the **root worktree** (gitignored, sibling to `.git`):

```
.spx/sessions/
├── todo/      # Available for pickup
├── doing/     # Currently claimed
└── archive/   # Completed
```

Session IDs use format `YYYY-MM-DD_HH-MM-SS`. If the user message or `$ARGUMENTS` includes a token in this format (or with a trailing `.md` suffix as in `YYYY-MM-DD_HH-MM-SS.md`), treat that token as the session identifier and act on it with `spx session show <id>` or `spx session pickup <id>` before validating any accompanying cache paths or markdown link targets. Priority order: `high` > `medium` > `low` (oldest first within same priority). The CLI handles atomic operations — NEVER touch session files manually except to read them. Multiple agents can run `/pickup` simultaneously; the CLI prevents race conditions.

</session_management>

<claim>
**If `$ARGUMENTS` contains `--list`:**

1. Get all todo sessions:
   ```bash
   spx session todo --json
   ```
2. Parse each session to extract session ID, priority and tags from frontmatter, nodes from `<nodes>` section. Limit to most recent 10.
3. Present options with `AskUserQuestion`:
   ```json
   {
     "questions": [
       {
         "question": "Which handoff would you like to load?",
         "header": "Handoff",
         "multiSelect": false,
         "options": [
           { "label": "2026-03-29 14:22 [high] (test-harness)", "description": "TDD step 7 on 43-fixtures.enabler — tests written, implementation needed" },
           { "label": "2026-03-28 09:15 [medium] (auth)", "description": "Spec authoring on 32-auth.outcome — assertions need review" }
         ]
       }
     ]
   }
   ```
4. Claim the chosen session:
   ```bash
   spx session pickup <selected-session-id>
   ```

**Otherwise (default):** Claim the highest priority (or oldest if tied) session:

```bash
spx session pickup --auto
```

The CLI selects by priority, moves `todo/` → `doing/` atomically, outputs the `<PICKUP_ID>...</PICKUP_ID>` marker, and displays the claimed session content.

Parse the claimed session id from `<PICKUP_ID>` and immediately emit the canonical claim marker:

```text
<PICKUP_CLAIM id="[claimed-session-id]">
claimed
</PICKUP_CLAIM>
```

Use the `id` attribute as the canonical session identifier for all later pickup and handoff markers. If multiple pickups happen in one conversation, later steps MUST key off this `id` value.

Once claimed, follow `${CLAUDE_SKILL_DIR}/workflows/pickup.md` to process the session.

</claim>

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

<failure_modes>

**Failure 1: Claude resumed implementation immediately after `/contextualizing`**

Claude loaded `/contextualizing`, then invoked `/applying` or started writing ADRs, tests, or code without a user checkpoint. The pre-context gate passed, but the workflow left the post-context transition as a suggestion instead of a requirement.

How to avoid: After `/contextualizing`, present the loaded state and stop. Use `AskUserQuestion` unless `$ARGUMENTS` explicitly includes `--auto-continue`. Do not invoke `/applying` or edit files before that checkpoint completes.

**Failure 2: Later handoff archived the wrong doing session**

Claude picked up more than one session in the same conversation, and the later handoff workflow searched for a generic pickup marker without tying it to a specific claim. The archive step then targeted the wrong doing session.

How to avoid: Emit canonical pickup markers with the claimed session id and carry that same `id` through the post-context checkpoint. Later workflows must archive from the most recent canonical pickup marker, not from a bare `<PICKUP_ID>` scan.

</failure_modes>

<success_criteria>
A successful pickup:

- [ ] Session claimed via `spx session pickup`
- [ ] Canonical pickup claim marker emitted as `<PICKUP_CLAIM id="...">`
- [ ] Skills checklist presented BEFORE any work starts
- [ ] Each anchored node's status presented
- [ ] PLAN.md / ISSUES.md checked and read if present
- [ ] Persisted artifacts acknowledged
- [ ] `/contextualizing` invoked on target node — NOT offered as an option, just done
- [ ] Canonical post-context marker emitted with the same session id
- [ ] Post-context decision captured via `AskUserQuestion` response, or explicit `--auto-continue` override acknowledged
- [ ] No `/applying`, ADR, test, code, or file-editing work starts before the checkpoint or override
- [ ] Failures listed in coordination are verified against current state before triaging
- [ ] Agent knows which skills to invoke and which to avoid

</success_criteria>
