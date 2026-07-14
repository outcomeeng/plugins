---
name: pickup
description: ALWAYS invoke this skill when resuming prior spec-tree work, loading a handoff session, claiming queued session work, or continuing from another saved context. NEVER continue spec-tree handoff work directly without this skill.
argument-hint: "[--list] [--auto-continue]"
allowed-tools: Read, Bash(spx session todo:*), Bash(spx session list:*), Bash(spx session pickup:*), Bash(spx session show:*), Bash(spx session release:*), Bash(spx worktree status:*), Bash(git fetch:*), Bash(git switch:*), Bash(git status:*), Bash(git branch:*), Bash(git worktree list:*), Bash(gh pr list:*), Bash(gh pr view:*), Bash(python3:*verify_session_claims.py*), AskUserQuestion, Glob, Skill
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
3. Present options with `AskUserQuestion`:
   ```json
   {
     "questions": [
       {
         "question": "Which handoff would you like to load?",
         "header": "Handoff",
         "multiSelect": false,
         "options": [
           { "label": "2026-03-29 14:22 [high] work/session-frontmatter", "description": "Goal: roll out structured session metadata. Next: update dependent skills." },
           { "label": "2026-03-28 09:15 [medium] main checkout", "description": "Goal: complete auth assertions. Next: review the outcome spec." }
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

**Failure 1: Claude resumed implementation immediately after `/contextualize`**

Claude loaded `/contextualize`, then invoked `/apply` or started writing ADRs, tests, or code without a user checkpoint. The pre-context gate passed, but the workflow left the post-context transition as a suggestion instead of a requirement.

How to avoid: After `/contextualize`, present the loaded state and stop. Use `AskUserQuestion` unless `$ARGUMENTS` explicitly includes `--auto-continue`. Do not invoke `/apply` or edit files before that checkpoint completes.

**Failure 2: Claude orphaned earlier pickups by archiving only the most recent doing session at handoff**

Claude picked up more than one session in the same conversation. The later handoff workflow archived only the most recent pickup, leaving earlier in-conversation pickups stranded in `doing/`. The next Claude context then had to read multiple handoff files to reconstruct the continuation.

How to avoid: Emit (or extend) `<CLAIMED_SESSIONS ids="...">` on every pickup so the latest marker names the full claimed-session set. Handoff workflow 04 reads the set and archives every id. Closure writes one canonical continuation per independent thread — never a sidecar for the same thread.

**Failure 3: Claude treated the existence of a new handoff session as permission to close a claimed session**

Claude picked up session A, then ran `spx session handoff` mid-work to create session B, then proposed archiving A because B existed. The queue state was treated as the permission source, not the completion of the reflection workflow.

How to avoid: The existence of any session — whether self-created or left by another context — never grants permission to archive a claimed session. Permission flows from the three claimed-session rules: the set grows only by user confirmation; closure writes one canonical continuation per independent thread; a quick-release shortcut exists only within a few turns of pickup. Pickup never archives.

**Failure 4: Claude asked the operator to choose without reviewing session evidence**

Claude loaded context, then asked the operator whether to continue, review artifacts, or take a different approach before classifying the session from claim verdicts, persisted artifacts, coordination notes, overlapping `doing` sessions, branch state, PR state, and expected verification. The operator had to choose from raw session metadata rather than an evaluated proposal.

How to avoid: Review the session evidence after `/contextualize`, classify the session, and present a no-surprises proposal before asking. The operator approves a represented course of work; if a new skill, evidence surface, external dependency, ownership conflict, or verification class appears later that the proposal did not represent, stop at the next safe checkpoint and present the delta.

**Failure 5: Claude tried to close a session whose work was owned elsewhere**

Claude picked up a duplicate session, saw evidence that another active `doing` session, branch, or PR already owned the objective, then drifted toward archive, release, or handoff because the workflow only modeled "wrongly claimed" as the current context's own session to close.

How to avoid: Classify the session as `owned_elsewhere`, report the owning session, branch, or PR, and stop without archiving, releasing, handing off, or moving any session.

</failure_modes>

<success_criteria>
A successful pickup:

- [ ] Session claimed via `spx session pickup`
- [ ] Canonical pickup claim marker emitted as `<PICKUP_CLAIM id="...">`
- [ ] Running CLAIMED_SESSIONS marker emitted as `<CLAIMED_SESSIONS ids="...">` including the newly claimed session id
- [ ] Claimed session remains in `doing` after pickup — pickup never archives, releases, or moves any session
- [ ] No new handoff session is treated as permission to archive, release, or replace a claimed session
- [ ] `/understand` invoked immediately after claim markers and before session details are processed
- [ ] Session `next_step` presented BEFORE any work starts beyond foundation loading
- [ ] Checkout brought current via `/sync-base` before any session detail is presented, for every `git_ref` kind
- [ ] In a bare-repository worktree pool, the assigned worktree's running claim is verified read-only before the work branch is switched into it, with a missing claim surfaced via `/diagnose` — `spx worktree claim` is not run during pickup, and no other pool worktree is entered or created
- [ ] Recorded claims reconciled by running `verify_session_claims.py`, with per-claim `Confirmed` / `Discrepancy` / `Unverifiable` verdicts presented in place of the recorded snapshot before the checkpoint
- [ ] PLAN.md / ISSUES.md paths checked before context loading, with note content read by `/contextualize`
- [ ] Persisted artifacts acknowledged
- [ ] `/contextualize` invoked on target node — NOT offered as an option, just done
- [ ] Session evidence reviewed after `/contextualize`: claim verdicts, persisted artifacts, loaded coordination notes, overlapping `doing` sessions, branch state, PR state, and expected verification
- [ ] Session classified as `actionable_here`, `owned_elsewhere`, `stale_or_superseded`, `blocked_on_external_dependency`, or `needs_operator_direction`
- [ ] When classification is `owned_elsewhere`, the owning session, branch, worktree, PR, or commit is reported and pickup stops without archiving, releasing, handing off, or otherwise mutating the claimed session
- [ ] When classification is not `owned_elsewhere`, a no-surprises proposal is presented before any operator decision: expected outcome, changed product surface, skill path, evidence infrastructure, verification plan, inspection references, and remaining-work expectation
- [ ] Any later unrepresented skill, evidence surface, external dependency, ownership conflict, or verification class stops at a safe checkpoint before continuation
- [ ] When the session references multiple nodes, the `/contextualize` target is selected deterministically by the priority order (rule 3 always resolves), so node multiplicity never triggers a user question — the user is asked which node only when `<nodes>` is empty or unreadable
- [ ] When classification is not `owned_elsewhere`, canonical post-context marker emitted as `<PICKUP_CHECKPOINT id="..." claimed="...">` carrying the full claimed-session set from the most recent `<CLAIMED_SESSIONS>`
- [ ] When classification is not `owned_elsewhere`, post-context decision captured via `AskUserQuestion` response, or explicit `--auto-continue` override acknowledged
- [ ] No `/apply`, ADR, test, code, or file-editing work starts before the checkpoint or override
- [ ] Failures listed in coordination are verified against current state before triaging
- [ ] When classification is not `owned_elsewhere`, Claude has the session `next_step`, current claim verdicts, loaded node context, and coordination-note paths needed to choose the next skill from current methodology

</success_criteria>
