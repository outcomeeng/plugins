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
2. **Fall back to a single canonical marker**: if no `<SESSION_SCOPE>` exists, use the most recent `<PICKUP_CHECKPOINT id="..." scope="...">` or `<PICKUP_CLAIM id="...">`. The id becomes the one-element scope.
3. **No markers at all**: scope is empty (fresh handoff, no pickup happened).
4. **Locate the mid-session artifact**: did this conversation run `spx session handoff` earlier? Cross-reference its output against `spx session list --status todo`. If that id is still in TODO, it is a workflow artifact to reconcile in `<write_canonical_continuation>`.
5. **Reconcile with workflow 02**: the scope must match `<perspective_session_scope>`. If the user named additional sessions, add them. If any session is **ambiguous**, STOP and resolve with the user before proceeding.

The resolved scope is the authoritative archive list for the rest of this workflow. The mid-session artifact is tracked separately — it may be rewritten in place (becoming the canonical continuation) or archived.

**The existence of the artifact is never permission to archive an in-scope session.** Archival permission flows from the completion of this workflow against the resolved scope.

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
3. Any mid-session artifact scheduled for archival (Path A, or Path C if multiple artifacts existed).

```bash
spx session archive <session-id>
```

Run the command once per id. NEVER archive sessions classified as **unrelated** or **ambiguous**. NEVER archive the session that was just rewritten in place under Path B.

**A handoff is incomplete if it creates or keeps more than one handoff in TODO, or if it leaves an in-scope session in `todo/` or `doing/`.**

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
- Exactly zero or one handoff file exists in TODO after closure. Never two.
- Canonical continuation written via Path A (release), Path B (rewrite in place), or Path C (new handoff).
- `<incorporated_sessions>` section present in the canonical continuation when the in-scope set is non-empty.
- Every in-scope session archived — none left in `todo/` or `doing/`.
- Any mid-session artifact that was NOT rewritten in place has been archived.
- Confirmation output names the continuation path and the archived ids.

</success_criteria>
