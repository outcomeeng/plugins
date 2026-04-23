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

<create_handoff>
**If `--no-session` is in `$ARGUMENTS`**: skip to `<archive_doing_session>`. After archiving, confirm: "Session released. All approved items persisted and committed. No session file created."

Otherwise:

1. **Check for claimed session**:
   - Search the conversation for the most recent canonical pickup marker:
     - Prefer `<PICKUP_CHECKPOINT id="...">`
     - Fall back to `<PICKUP_CLAIM id="...">` when no checkpoint marker exists
   - Use the `id` attribute from that marker as the doing session to archive after the new handoff is created.
   - Ignore older bare `<PICKUP_ID>` markers when a canonical pickup marker exists. Multiple pickups may have happened in the same conversation; archive the session named by the most recent canonical marker only.

2. **Create the handoff**:

   ```bash
   spx session handoff
   ```

   Parse output for `<HANDOFF_ID>` and `<SESSION_FILE>`.

3. **Read `<SESSION_FILE>`** to confirm it exists and is empty.

4. **Write `<SESSION_FILE>`** using the template in `references/session-format.md`:
   - `<nodes>` and `<skills>` sections — from `<perspective_starting_point>` and `<perspective_skills>` in `02-reflect.md`
   - `<persisted>` section — files committed above, insights written, escape hatches created
   - `<coordination>` section — unapproved items from workflow 03 that are coordination-only context

</create_handoff>

<archive_doing_session>
Archive the claimed doing session (if one was found):

```bash
spx session archive <doing-session-id>
```

**If `--prune` is in `$ARGUMENTS`** (only after the new handoff is successfully written):

```bash
spx session list --status archive --json
spx session delete <archive-session-id>
```

NEVER delete todo or doing sessions. `--prune` only affects archive.

</archive_doing_session>

<confirm>
State:

- Handoff session ID created (or "no session file — released")
- That session-owned work was committed before closure
- Which doing session was archived (if applicable)

</confirm>

<success_criteria>

- All approved persistence items written.
- Session-owned files committed — `git status` shows no session-owned staged or unstaged changes.
- Committed vs uncommitted state recorded for each anchored node.
- Session file created (unless `--no-session`) and written using `references/session-format.md`.
- Claimed doing session archived using the session id from the most recent canonical pickup marker.
- Confirmation output includes handoff session ID.

</success_criteria>
