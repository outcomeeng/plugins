---
name: pickup
description: ALWAYS invoke this skill when resuming prior spec-tree work, loading a handoff session, claiming queued session work, or continuing from another saved context. NEVER continue spec-tree handoff work directly without this skill.
argument-hint: "[session-id | --list] [--auto-continue]"
allowed-tools: Read, Bash(spx spec status:*), Bash(spx session todo:*), Bash(spx session list:*), Bash(spx session pickup:*), Bash(spx session show:*), Bash(spx worktree status:*), Bash(git fetch:*), Bash(git switch:*), Bash(git branch --list:*), Bash(git worktree list:*), Bash(gh pr list:*), Bash(gh pr view:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/verify_session_claims.py":*), {{! tool('ask_user') !}}, Glob, Skill
---

<objective>
A claimed handoff session — loaded, reconciled against current repository state, and marked with canonical pickup markers — ready to continue prior work without repeating earlier mistakes.
</objective>

<constraints>

- Pickup opens session responsibility and NEVER releases, archives, deletes, or closes a session — a claimed session remains Claude's responsibility until a later `/handoff` accounts for it explicitly.
- NEVER propose fixing bugs, writing code, or any implementation work before `/contextualize` has been invoked on the target node.
- Before asking the operator to continue, review the loaded session evidence and present a no-surprises proposal: expected outcome, changed product surface, skill path, evidence infrastructure, verification plan, inspection references, and remaining-work expectation.
- If session evidence shows another active context already owns the objective, report the owning session, branch, or PR and stop without archiving, releasing, handing off, or otherwise mutating the claimed session.

</constraints>

<claimed_sessions>
Three rules govern a conversation's claimed-session set:

1. **The claimed-session set grows only by user confirmation.** A session joins the set when the user instructs Claude via `/pickup`, or when the user confirms a suggested pickup. Nothing else adds to it.

2. **Closure has acceptable end states only through `/handoff`.** Every claimed session becomes Claude's sole responsibility. Reflect, persist remaining validated relevant context, and end with zero, one, or several session files — one canonical continuation per independent continuation thread in the resolved claimed-session set. Supplemental or sidecar handoffs for the same thread are never valid at closure.

3. **Quick-exit shortcut.** If, within a few turns of pickup, Claude realizes the pickup was wrong, the user has two options — only the user can choose:
   - Invoke `/handoff --no-session` to archive the wrongly-claimed session immediately. The session leaves the claimed-session set but is archived, not returned to the todo queue.
   - Run `spx session release <id>` to move the session from `doing/` back to `todo/` for another context to claim.

   Neither action counts toward the closure workload for the claimed-session set — the wrongly-claimed session leaves the set the moment the user confirms the quick exit.

**Consequences of the three rules:**

- Every successful `spx session pickup` adds that session id to the CLAIMED_SESSIONS marker for this conversation. A later pickup does not replace earlier entries — the set is additive.
- The pickup workflow MUST NOT archive, release, delete, or manually move any session. After the post-context checkpoint, leave the claimed session in `doing` unless the user explicitly invokes a closure workflow.
- A newly created handoff session is a workflow artifact, not a substitute for the claimed session. Its existence never grants permission to close any claimed session.
- Queue inspection alone is never permission. Archival comes from completing the handoff workflow against the claimed-session set named in CLAIMED_SESSIONS.

</claimed_sessions>

<session_management>
All session management uses `spx session` CLI commands:

```bash
# List sessions in status `todo`
spx session todo [--json]

# List sessions by status (includes `todo` and `doing` by default)
spx session list [--status todo|doing|archive] [--json]

# Claim one or more sessions (move todo -> doing)
spx session pickup [ids...] [--auto]

# Show session content
spx session show <id...>

# Return claimed sessions to the todo queue (move doing -> todo)
spx session release [ids...]

# Create a handoff session (JSON header + body on stdin)
spx session handoff

# Move sessions to archive
spx session archive <id...>

# Remove old todo sessions, keeping the most recent N
spx session prune [--keep <count>] [--dry-run]

# Delete sessions permanently
spx session delete <id...>
```

Sessions are organized in `.spx/sessions/` in the **root worktree** (gitignored, sibling to `.git`):

```
.spx/sessions/
├── todo/      # Available for pickup
├── doing/     # Currently claimed
└── archive/   # Completed
```

Session IDs use format `YYYY-MM-DD_HH-MM-SS`. If the user message or `$ARGUMENTS` includes a token in this format (or with a trailing `.md` suffix as in `YYYY-MM-DD_HH-MM-SS.md`), treat that token as the session identifier and act on it with `spx session show <id>` or `spx session pickup <id>` before validating any accompanying cache paths or markdown link targets. Priority order: `high` > `medium` > `low` (oldest first within same priority). The CLI handles atomic operations — NEVER touch session files manually except to read them. Multiple Claude sessions can run `/pickup` simultaneously; the CLI prevents race conditions.

</session_management>

<claim>
**If `$ARGUMENTS` contains `--list`:**

1. Get all todo sessions:
   ```bash
   spx session todo --json
   ```
2. Parse each session to extract session ID, `priority`, `goal`, `next_step`, and `git_ref` from frontmatter, plus nodes from the `<nodes>` section. Limit to most recent 10.
3. Present one single-select question with `{{! tool('ask_user') !}}`:
   - Stable question id when the runtime schema exposes one: `handoff`
   - Header: `Handoff`
   - Question: `Which handoff would you like to load?`
   - Options: 2-3 mutually exclusive sessions, each labeled with its full session id, priority, and branch context and described by its goal and next step
4. Claim the chosen session:
   ```bash
   spx session pickup <selected-session-id>
   ```

**If `$ARGUMENTS` contains a session id:** Strip an optional trailing `.md` suffix and claim that exact session:

```bash
spx session pickup <session-id>
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

Then emit (or extend) the running CLAIMED_SESSIONS marker. Scan the conversation for the most recent `<CLAIMED_SESSIONS ids="...">` marker:

- **No prior CLAIMED_SESSIONS marker** → emit `<CLAIMED_SESSIONS ids="[claimed-session-id]">`.
- **Prior CLAIMED_SESSIONS marker exists** → emit a new marker whose `ids` attribute is the prior list with `[claimed-session-id]` appended (comma-separated, order preserved).

```text
<CLAIMED_SESSIONS ids="[first-pickup],[second-pickup],...,[claimed-session-id]">
the claimed sessions this conversation must close
</CLAIMED_SESSIONS>
```

The CLAIMED_SESSIONS marker names every in-conversation pickup that Claude is responsible for closing. Handoff workflows read the MOST RECENT `<CLAIMED_SESSIONS>` to determine which sessions to archive at closure. If multiple pickups happen in one conversation, later steps MUST key off this set, not a single-session marker.

Use the `id` attribute on `<PICKUP_CLAIM>` as the canonical identifier for the current pickup (checkpoints, markers, error messages).

Once claimed, follow `${CLAUDE_SKILL_DIR}/workflows/pickup.md` to process the session.

The workflow invokes `/understand` immediately after claim markers and before it processes session details. Node-local `PLAN.md` and `ISSUES.md` content is read by `/contextualize`, not by pre-context pickup steps.

</claim>

<error_handling>
**No sessions directory or empty**:

```
No handoff sessions found in .spx/sessions/todo/
Use `/handoff` to create a handoff document.
```

**Only doing sessions exist**:

```
Found only doing sessions — these are claimed by active Claude sessions.
```

Present options via `{{! tool('ask_user') !}}`:

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

**Failure 1: Claude resumed implementation immediately after `/contextualize`**

What happened: Claude loaded `/contextualize`, then invoked `/apply` or started writing ADRs, tests, or code without a user checkpoint.

Why it failed: Claude treated successful context loading as continuation authority because the post-context checkpoint was expressed as guidance instead of a required transition.

How to avoid: After `/contextualize`, present the loaded state and stop. Use `{{! tool('ask_user') !}}` unless `$ARGUMENTS` explicitly includes `--auto-continue`. Do not invoke `/apply` or edit files before that checkpoint completes.

**Failure 2: Claude orphaned earlier pickups by archiving only the most recent doing session at handoff**

What happened: Claude picked up more than one session in the same conversation. The later handoff workflow archived only the most recent pickup, leaving earlier in-conversation pickups stranded in `doing/`.

Why it failed: Claude keyed closure to one current session id instead of the additive claimed-session set, so the next context had to reconstruct one continuation from several session files.

How to avoid: Emit (or extend) `<CLAIMED_SESSIONS ids="...">` on every pickup so the latest marker names the full claimed-session set. Handoff workflow 04 reads the set and archives every id. Closure writes one canonical continuation per independent thread — never a sidecar for the same thread.

**Failure 3: Claude treated the existence of a new handoff session as permission to close a claimed session**

What happened: Claude picked up session A, ran `spx session handoff` mid-work to create session B, then proposed archiving A because B existed.

Why it failed: Claude treated queue state as closure authority and bypassed the reflection and claimed-session accounting owned by `/handoff`.

How to avoid: The existence of any session — whether self-created or left by another context — never grants permission to archive a claimed session. Permission flows from the three claimed-session rules: the set grows only by user confirmation; closure writes one canonical continuation per independent thread; a quick-release shortcut exists only within a few turns of pickup. Pickup never archives.

**Failure 4: Claude asked the operator to choose without reviewing session evidence**

What happened: Claude loaded context, then asked the operator whether to continue, review artifacts, or take a different approach before classifying the session from claim verdicts, persisted artifacts, coordination notes, overlapping `doing` sessions, branch state, PR state, and expected verification.

Why it failed: Claude presented raw session metadata as a decision surface, leaving the operator to perform the evidence review and classification the pickup workflow owns.

How to avoid: Review the session evidence after `/contextualize`, classify the session, and present a no-surprises proposal before asking. The operator approves a represented course of work; if a new skill, evidence surface, external dependency, ownership conflict, or verification class appears later that the proposal did not represent, stop at the next safe checkpoint and present the delta.

**Failure 5: Claude tried to close a session whose work was owned elsewhere**

What happened: Claude picked up a duplicate session, saw evidence that another active `doing` session, branch, or PR already owned the objective, then drifted toward archive, release, or handoff.

Why it failed: Claude treated `owned_elsewhere` as an intermediate observation instead of a terminal classification that forbids further session mutation.

How to avoid: Classify the session as `owned_elsewhere`, report the owning session, branch, or PR, and stop without archiving, releasing, handing off, or moving any session.

**Failure 6: Claude made an empty node list operator homework**

What happened: Claude claimed a valid session whose `<nodes>` section was empty, then asked the operator to find and supply a node path even though the goal, `next_step`, and affected skill name identified the product area.

Why it failed: Claude treated missing recorded nodes as missing product context and failed to query the current node projection through `spx spec status`.

How to avoid: Run `spx spec status --format json` and traverse its projected tree from the root downward. Contextualize session-relevant nodes as encountered until authoritative context identifies the next workflow with no relevant branch unresolved. Never ask the operator to search the tree, choose a node, or provide a raw path.

</failure_modes>

<success_criteria>

- The claimed session remains in `doing`, and canonical claim, claimed-set, and post-context markers identify the exact sessions this conversation owns.
- The report presents synchronized current state, one verdict per recorded claim, persisted artifacts, loaded coordination context, and the handoff's recommended first action.
- The selected context target comes from recorded nodes or complete top-down projection traversal; projection failure preserves its exact diagnostic, and exhausted traversal yields `stale_or_superseded` without operator node-search work.
- The post-context output names the session classification, evidence-based continuation proposal, selected or automatically resumed action, and every known owner or blocker.
- Pickup itself performs no implementation edit and never archives, releases, replaces, or otherwise closes a claimed session.

</success_criteria>
