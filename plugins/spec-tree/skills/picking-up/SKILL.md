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

**Pickup opens session responsibility. It never releases, archives, deletes, or closes a session.** A claimed session remains the agent's responsibility until a later `/handing-off` or `/release` workflow accounts for it explicitly.

**⚠️ NEVER propose fixing bugs, writing code, or any implementation work before `/contextualizing` has been invoked on the target node.**
</objective>

<session_scope>
Three rules govern a conversation's session scope:

1. **Scope grows only by user confirmation.** A session enters scope when the user instructs the agent via `/picking-up`, or when the user confirms an agent-suggested pickup. Nothing else extends scope.

2. **Closure has exactly one acceptable end state.** Every in-scope session becomes the agent's sole responsibility. The agent reflects, persists remaining validated relevant context, and ends with either zero or one handoff that incorporates everything from the in-scope sessions. No supplemental, sidecar, or parallel handoff is ever valid at closure.

3. **Quick-release escape hatch.** If, within a few turns of pickup, the agent realizes the pickup was wrong and the user confirms release, the session leaves scope via `/release` without counting toward the closure workload.

**Consequences of the three rules:**

- Every successful `spx session pickup` adds that session id to the SESSION_SCOPE marker for this conversation. A later pickup does not replace earlier entries — scope is additive.
- The pickup workflow MUST NOT archive, release, delete, or manually move any session. After the post-context checkpoint, leave the claimed session in `doing` unless the user explicitly invokes a closure workflow.
- A newly created handoff session is a workflow artifact, not a substitute for the claimed session. Its existence never grants permission to close any in-scope session.
- Queue inspection alone is never permission. Archival comes from completing the handing-off workflow against the in-scope set named in SESSION_SCOPE.

</session_scope>

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

Then emit (or extend) the running session-scope marker. Scan the conversation for the most recent `<SESSION_SCOPE ids="...">` marker:

- **No prior scope marker** → emit `<SESSION_SCOPE ids="[claimed-session-id]">`.
- **Prior scope marker exists** → emit a new marker whose `ids` attribute is the prior list with `[claimed-session-id]` appended (comma-separated, order preserved).

```text
<SESSION_SCOPE ids="[first-pickup],[second-pickup],...,[claimed-session-id]">
scope
</SESSION_SCOPE>
```

The scope marker names every in-conversation pickup that is the agent's responsibility to close. Handoff workflows read the MOST RECENT `<SESSION_SCOPE>` to determine which sessions to archive at closure. If multiple pickups happen in one conversation, later steps MUST key off this scope, not a single-session marker.

Use the `id` attribute on `<PICKUP_CLAIM>` as the canonical identifier for the current pickup (checkpoints, markers, error messages).

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

**Failure 2: Later handoff archived only the most recent doing session, orphaning earlier pickups**

Claude picked up more than one session in the same conversation. The later handoff workflow archived only the most recent pickup, leaving earlier in-conversation pickups stranded in `doing/`. A receiving agent then had to read multiple handoff files to reconstruct the continuation.

How to avoid: Emit (or extend) `<SESSION_SCOPE ids="...">` on every pickup so the latest marker names the full scope. Handoff workflow 04 reads the scope and archives every id. Closure ends with zero or one handoff incorporating everything — never a sidecar.

**Failure 3: Treated the existence of a new handoff session as permission to close a claimed session**

Claude picked up session A, then ran `spx session handoff` mid-work to create session B, then proposed archiving A because B existed. The queue state was treated as the permission source, not the completion of the reflection workflow.

How to avoid: The existence of any session — whether self-created or left by another agent — never grants permission to archive an in-scope session. Permission flows from the three scope rules: scope grows only by user confirmation; closure ends with zero or one handoff; a quick-release escape hatch exists only within a few turns of pickup. Pickup never archives.

</failure_modes>

<success_criteria>
A successful pickup:

- [ ] Session claimed via `spx session pickup`
- [ ] Canonical pickup claim marker emitted as `<PICKUP_CLAIM id="...">`
- [ ] Running session-scope marker emitted as `<SESSION_SCOPE ids="...">` including the newly claimed session id
- [ ] Claimed session remains in `doing` after pickup — pickup never archives, releases, or moves any session
- [ ] No new handoff session is treated as permission to archive, release, or replace an in-scope session
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
