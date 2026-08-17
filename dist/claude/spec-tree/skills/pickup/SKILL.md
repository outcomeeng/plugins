---
name: pickup
description: ALWAYS invoke this skill when resuming prior spec-tree work, loading a handoff session, claiming queued session work, or continuing from another saved context. NEVER continue spec-tree handoff work directly without this skill.
argument-hint: "[#N | owner/repo#N | issue-url | session-id | --list] [--auto-continue]"
allowed-tools: Read, Bash(spx session todo:*), Bash(spx session list:*), Bash(spx session pickup:*), Bash(spx session show:*), Bash(spx session release:*), Bash(spx worktree status:*), Bash(git fetch:*), Bash(git switch:*), Bash(git branch --list:*), Bash(git worktree list:*), Bash(gh pr list:*), Bash(gh pr view:*), Bash(gh issue list:*), Bash(gh issue view:*), Bash(gh issue create:*), Bash(gh issue edit:*), Bash(gh issue comment:*), Bash(gh project item-list:*), Bash(gh project view:*), Bash(gh project item-add:*), Bash(gh project item-edit:*), Bash(gh project field-list:*), Bash(gh api repos/*/issues/*/dependencies/blocked_by:*), Bash(gh api repos/*/issues/* --jq .id), Bash(spx session archive:*), Bash(printf:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/verify_session_claims.py":*), AskUserQuestion, Glob, Skill
---

<objective>
A claimed handoff session — or, under `spx/local/coordination.md`, a claimed Change — loaded, reconciled against current repository state, and marked with canonical pickup markers, ready to continue prior work without repeating earlier mistakes.
</objective>

<constraints>

- Pickup opens session responsibility and NEVER releases, archives, deletes, or closes a session — a claimed session remains Claude's responsibility until a later `/handoff` accounts for it explicitly. The single session exception is the legacy-file archive `<change_coordination>` authorizes once the Change carrying that file as received input exists. A Change is not a session: under the overlay, `${CLAUDE_SKILL_DIR}/workflows/change.md` releases a Change — posts a `Handoff:` comment and removes the assignee — when an Executable Frame fails validation against current truth, and that release is the workflow's own step.
- NEVER propose fixing bugs, writing code, or any implementation work before `/contextualize` has been invoked on the target node.
- Before asking the operator to continue, review the loaded session evidence and present a no-surprises proposal: expected outcome, changed product surface, skill path, evidence infrastructure, verification plan, inspection references, and remaining-work expectation.
- If session evidence shows another active context already owns the objective, report the owning session, branch, or PR and stop without archiving, releasing, handing off, or otherwise mutating the claimed session.

</constraints>

<change_coordination>

When `spx/local/coordination.md` exists at the repository root, the repository coordinates work through Changes and Handoffs — GitHub issues in the store that overlay names — and this skill follows `${CLAUDE_SKILL_DIR}/workflows/change.md` in place of `${CLAUDE_SKILL_DIR}/workflows/pickup.md` and the `<claim>` procedure below. A legacy queue file claimed under that overlay becomes a Change carrying the whole file as received input and is archived once the Change exists; that archive is the one session mutation this skill performs, and only there. `<claimed_sessions>` keeps governing any `<CLAIMED_SESSIONS>` marker already present in the conversation. Without the overlay, everything below applies unchanged.

</change_coordination>

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
- The pickup workflow MUST NOT archive, release, delete, or manually move any session, except the legacy-file archive `<change_coordination>` authorizes after its Change exists; a Change release is not a session mutation, per `<constraints>`. After the post-context checkpoint, leave the claimed session in `doing` unless the user explicitly invokes a closure workflow.
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
This whole section is skipped when `spx/local/coordination.md` exists — `${CLAUDE_SKILL_DIR}/workflows/change.md` then owns claiming, per `<change_coordination>`.

**If `$ARGUMENTS` contains `--list`:**

1. Get all todo sessions:
   ```bash
   spx session todo --json
   ```
2. Parse each session to extract session ID, `priority`, `goal`, `next_step`, and `git_ref` from frontmatter, plus nodes from the `<nodes>` section. Limit to most recent 10.
3. Present one single-select question with `AskUserQuestion`:
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

The workflow invokes `/understand` immediately before its first product-content access — the coordination-note path check under `spx/` when the session names a node, otherwise the `/contextualize` invocation for the node the operator names — and at no earlier step; the claim, `spx session show`, checkout, base sync, and claim reconciliation touch no product content and need no reload. Node-local `PLAN.md` and `ISSUES.md` content is read by `/contextualize`, not by pre-context pickup steps.

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

**Change store unreachable or unauthenticated** (`spx/local/coordination.md` present):

```
gh could not reach <store>: <gh error>
Authenticate gh (project scope) or fix the overlay; no Change was claimed or created.
```

**Overlay incomplete**: `spx/local/coordination.md` names no store repository, project owner and number, or Product value — report the missing value and stop; never guess a store.

**Change closed, held elsewhere, or another Product's**: `owned_elsewhere` — report the terminal state, the current holder (assignee, or the winning `Claim:` comment's session id when two sessions raced), or the mismatched `product`, and stop without mutating the Change beyond removing this session's own losing assignee when the winner is a different account.

**Migration interrupted**: when `gh issue create` or `gh project item-add` fails after `spx session pickup <id>`, report the failed command and its output; the legacy file stays in `doing` unarchived and no further Change write is attempted. A lone `gh project item-edit` failure gets one re-read of the item and one retry of the missing field; a second failure is reported the same way, with the created issue named as the Change to resume from.

**Archive failed after the Change exists**: `spx session archive <id>` is retried once; on a second failure the created issue URL is reported beside the file id and the file stays in `doing`; the next pickup of that file finds the issue through the store search and resumes it rather than creating another.

**Several Changes match a legacy file**: the store search finds more than one Change carrying the file as received input — classify `needs_operator_direction`, report every match, create nothing, and leave the file in `doing`.

**Secret detected in legacy file**: report the file id and the kind of content found (never the value); the file stays in `doing` and no Change is created until the operator redacts it — after which the file is re-read and re-inspected — or abandons the migration.

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
Each bullet is tagged `(both)` when it holds under and without `spx/local/coordination.md`, or `(session file only)` when it belongs to the session-file path alone. Under the overlay a successful pickup satisfies `${CLAUDE_SKILL_DIR}/workflows/change.md`'s success criteria — a Change claimed by sole assignee or created from a legacy file that carries no secret, `<PICKUP_CLAIM change="...">` and a cumulative `<CLAIMED_CHANGES urls="...">` emitted, execution only from a validated Executable Change continuing at the Handoff's Next Activity, and a proposal that names the Frame's governing truth first — plus every `(both)` bullet. Without the overlay a successful pickup satisfies every bullet:

- [ ] (session file only) Session claimed via `spx session pickup`
- [ ] (session file only) Canonical pickup claim marker emitted as `<PICKUP_CLAIM id="...">`
- [ ] (session file only) Running CLAIMED_SESSIONS marker emitted as `<CLAIMED_SESSIONS ids="...">` including the newly claimed session id
- [ ] (session file only) Claimed session remains in `doing` after pickup — pickup never archives, releases, or moves any session, except the legacy-file archive `<change_coordination>` authorizes once its Change exists
- [ ] (session file only) No new handoff session is treated as permission to archive, release, or replace a claimed session
- [ ] (both) `/understand` invoked immediately before the workflow's first product-content access — the coordination-note path check or the `/contextualize` invocation on the session-file path, the Change-body read on the Change path — and not before the claim, session presentation, checkout, base sync, or claim reconciliation
- [ ] (session file only) Session `next_step` presented only after `/sync-base` and claim reconciliation, and before node context or continuation work
- [ ] (both) Checkout brought current via `/sync-base` before any session detail is presented, for every `git_ref` kind
- [ ] (both) In a bare-repository worktree pool, the assigned worktree's running claim is verified read-only before the work branch is switched into it, with a missing claim surfaced via `/diagnose` — `spx worktree claim` is not run during pickup, and no other pool worktree is entered or created
- [ ] (session file only) Recorded claims reconciled by running `verify_session_claims.py`, with per-claim `Confirmed` / `Discrepancy` / `Unverifiable` verdicts presented in place of the recorded snapshot before the checkpoint
- [ ] (session file only) PLAN.md / ISSUES.md paths checked before context loading, with note content read by `/contextualize`
- [ ] (session file only) Persisted artifacts acknowledged
- [ ] (both) `/contextualize` invoked on target node — NOT offered as an option, just done
- [ ] (session file only) Session evidence reviewed after `/contextualize`: claim verdicts, persisted artifacts, loaded coordination notes, overlapping `doing` sessions, branch state, PR state, and expected verification
- [ ] (session file only) Session classified as `actionable_here`, `owned_elsewhere`, `stale_or_superseded`, `blocked_on_external_dependency`, or `needs_operator_direction`
- [ ] (both) When classification is `owned_elsewhere`, the owning session, branch, worktree, PR, or commit is reported and pickup stops without archiving, releasing, handing off, or otherwise mutating the claimed session
- [ ] (session file only) When classification is not `owned_elsewhere`, a no-surprises proposal with the same fields as the overlay's proposal above, minus the governing-truth field the Change supplies, is presented before any operator decision
- [ ] (both) Any later unrepresented skill, evidence surface, external dependency, ownership conflict, or verification class stops at a safe checkpoint before continuation
- [ ] (session file only) When the session references multiple nodes, the `/contextualize` target is selected deterministically by the priority order (rule 3 always resolves), so node multiplicity never triggers a user question — the user is asked which node only when `<nodes>` is empty or unreadable
- [ ] (session file only) When classification is not `owned_elsewhere`, canonical post-context marker emitted as `<PICKUP_CHECKPOINT id="..." claimed="...">` carrying the full claimed-session set from the most recent `<CLAIMED_SESSIONS>`
- [ ] (both) When classification is not `owned_elsewhere`, post-context decision captured via `AskUserQuestion` response, or explicit `--auto-continue` override acknowledged
- [ ] (both) No `/apply`, ADR, test, code, or file-editing work starts before the checkpoint or override
- [ ] (session file only) Failures listed in coordination are verified against current state before triaging
- [ ] (session file only) When classification is not `owned_elsewhere`, Claude has the session `next_step`, current claim verdicts, loaded node context, and coordination-note paths needed to choose the next skill from current methodology

</success_criteria>
