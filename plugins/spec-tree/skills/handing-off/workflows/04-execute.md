<objective>
Execute all approved persistence decisions, commit session-owned work, and create the handoff session file. This workflow closes the session — work not committed here is not persisted.

</objective>

<required_reading>
Before writing the session file, read `references/session-format.md` for the required template.

</required_reading>

<write_approved_items>
For each approved item from workflow 03:

- **Spec amendments**: Edit the spec file directly.
- **CLAUDE.md / memory / skill updates**: Write the insight to the correct target.
- **ISSUES.md**: Write or update in the node directory. Remove fixed items, add new ones.
- **PLAN.md**: Write, update, or remove in the node directory. Never leave a stale plan.

</write_approved_items>

<commit>
Handoff is BLOCKED until session-owned files are committed.

1. Enumerate every file changed during this session that belongs to the session:
   - spec files, tests, implementation code
   - PLAN.md / ISSUES.md
   - methodology files approved in workflow 03
2. Compare that list against `git status --short`.
3. Stage only the session-owned files.
4. Invoke `/committing-changes` to create the commit.

**Dirty worktree rules**:

- Unrelated changes present but session-owned files clearly identifiable → stage and commit only session-owned files.
- Ownership ambiguous → STOP and ask the user. Do not create a handoff that implies closure.
- User instructs not to commit → STOP and ask whether to abort handoff or convert to a non-closing status update. Session closure requires a commit.

</commit>

<record_state>
For each anchored node, check `git status` and record:

- **Committed**: session-owned work should appear here after the commit above.
- **Uncommitted**: only foreign or intentionally untouched work should remain here.

</record_state>

<resolve_session_scope>
Determine the authoritative set of in-scope sessions plus any mid-session artifact to reconcile.

1. **Read the running scope marker**: search the conversation for the most recent `<SESSION_SCOPE ids="a,b,c">` marker. Each id is a user-confirmed pickup the agent must close.
2. **Fallback when no scope marker exists**: context compaction or a malformed marker can drop `<SESSION_SCOPE>`. Rebuild additively:
   - Collect every `<PICKUP_CLAIM id="...">` and `<PICKUP_CHECKPOINT id="...">` emitted since the last closure marker in the conversation.
   - Deduplicate by id; the resulting set is the resolved scope.
   - If the set has **one** id, proceed.
   - If the set has **more than one** id, present the list to the user and ask them to confirm the full scope before continuing. NEVER silently collapse to the most recent pickup.
   - If the set is **empty**, check for pickup evidence: `spx session list --status doing` showing sessions this worktree may own, or references in the conversation to a claimed session. If any such evidence exists, STOP and ask the user to confirm scope. Only declare scope empty when there is clear evidence no pickup happened in this conversation (fresh handoff).
3. **Locate mid-session artifacts**: did this conversation run `spx session handoff` earlier? Collect every handoff id printed by `spx session handoff` during this conversation. Cross-reference against `spx session list --status todo`:
   - **Zero artifacts in TODO** → no reconciliation needed; Path A or C will apply.
   - **Exactly one artifact in TODO** → it becomes the rewrite-in-place candidate for Path B.
   - **More than one artifact in TODO** → STOP. Present the list to the user and ask which is the canonical continuation. Archive only the artifacts this conversation created; never touch artifacts created by other conversations.
4. **Reconcile with workflow 02**: the scope must match `<perspective_session_scope>`. If the user named additional sessions, add them. If any session is **ambiguous**, STOP and resolve with the user before proceeding.

The resolved scope is the authoritative archive list for the rest of this workflow. Mid-session artifacts are tracked separately — at most one is rewritten in place; the rest are archived only if this conversation created them.

**The existence of any session is never permission to archive an in-scope session.** Archival permission flows from the completion of this workflow against the resolved scope.

</resolve_session_scope>

<write_canonical_continuation>
Every closure ends with **zero or one** handoff. Pick the path once and execute it.

**Path A — `--no-session` (zero handoffs, a.k.a. `/release`)**: skip to `<archive_scope>`. After archiving, confirm: "Session released. All approved items persisted and committed. No continuation handoff. Archived scope: <list>."

**Path B — rewrite in place (one handoff, artifact exists)**: a mid-session artifact is still in TODO.

1. Use the artifact id from `<resolve_session_scope>`. Derive its file path from `spx session show <artifact-id>` or the root worktree's `.spx/sessions/todo/<artifact-id>.md`.
2. Do NOT run `spx session handoff` — that would create a second handoff and break the one-handoff end state.
3. Write (overwrite) the artifact file using the template in `references/session-format.md`. The file content is the canonical continuation with cumulative scope from every in-scope session.
4. Use `<HANDOFF_ID>` = artifact id for the confirmation message.

**Path C — new handoff (one handoff, no artifact)**:

1. Run `spx session handoff`. Parse output for `<HANDOFF_ID>` and `<SESSION_FILE>`.
2. Read `<SESSION_FILE>` to confirm it exists and is empty.
3. Write `<SESSION_FILE>` using the template in `references/session-format.md`.

**Content of the canonical continuation (B and C):**

- `<nodes>` and `<skills>` — from `<perspective_starting_point>` and `<perspective_skills>` in `02-reflect.md`
- `<persisted>` — files committed above, insights written, escape hatches created
- `<coordination>` — unapproved items from workflow 03 that are coordination-only context
- `<incorporated_sessions>` — include ONLY when the in-scope set is non-empty; list each session id with its archive disposition

</write_canonical_continuation>

<archive_scope>
After the canonical continuation is written and verified (Path B or C), or immediately under Path A, archive every session in the resolved scope plus any mid-session artifact that was NOT rewritten in place.

Archive order:

1. Earlier in-conversation pickups still in `doing/`.
2. The most recently claimed doing session, if any.
3. Any mid-session artifact this conversation created that is NOT the rewrite-in-place canonical (Path A archives all artifacts; Path C archives all when no rewrite happened).

```bash
spx session archive <session-id>
```

Run the command once per id. NEVER archive sessions classified as **unrelated** or **ambiguous**. NEVER archive the session that was just rewritten in place under Path B. NEVER archive TODO sessions created by other conversations — the TODO queue is shared across agents.

**A handoff is incomplete if this closure creates or keeps more than one canonical continuation in TODO, or if it leaves an in-scope session in `todo/` or `doing/`.** Unrelated TODO sessions owned by other agents are not this closure's concern and must be left untouched.

**If `--prune` is in `$ARGUMENTS`** (only after the canonical continuation is successfully written):

```bash
spx session list --status archive --json
spx session delete <archive-session-id>
```

NEVER delete todo or doing sessions. `--prune` only affects archive.

</archive_scope>

<confirm>
State:

- Canonical continuation: "new handoff <id>" | "rewrote <artifact-id> in place" | "released (no handoff)"
- Session-owned work was committed before closure
- Every session id archived from the resolved scope (and any artifact NOT rewritten in place)

</confirm>

<success_criteria>

- All approved persistence items written.
- Session-owned files committed — `git status` shows no session-owned staged or unstaged changes.
- Committed vs uncommitted state recorded for each anchored node.
- Exactly zero or one canonical continuation created or rewritten by THIS closure exists in TODO — never two. Unrelated TODO sessions owned by other agents are out of scope and untouched.
- Canonical continuation written via Path A (release), Path B (rewrite in place), or Path C (new handoff).
- `<incorporated_sessions>` section present in the canonical continuation when the in-scope set is non-empty.
- Every in-scope session archived — none left in `todo/` or `doing/`.
- Every mid-session artifact this conversation created is reconciled: at most one rewritten in place, all others archived.
- Confirmation output names the continuation path and the archived ids.

</success_criteria>
