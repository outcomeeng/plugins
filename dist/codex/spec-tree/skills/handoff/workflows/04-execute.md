<objective>
Execute all approved persistence decisions, commit session-owned work, and either write or omit the canonical continuation. This workflow closes the session — work not committed here is not persisted.

</objective>

<required_reading>
Before writing a Path B or Path C session file, read `references/session-format.md` for the required template.

</required_reading>

<write_approved_items>
For each approved item from workflow 03:

- **Spec amendments**: Edit the spec file directly.
- **CLAUDE.md / memory / skill updates**: Write the insight to the correct target.
- **ISSUES.md**: Write or update in the node directory. Remove fixed items, add new ones.
- **PLAN.md**: Write, update, or remove in the node directory. Never leave a stale plan.

</write_approved_items>

<commit>
Closure is BLOCKED until session-owned files are committed.

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
Read the `<RESOLVED_SCOPE ids="…" artifact_id="…">` marker emitted by workflow 02 (`<perspective_session_scope>`). Use it as the authoritative archive list and artifact identifier for the rest of this workflow.

**If the marker is missing** (workflow 02 did not emit it, or context compaction dropped it): STOP and re-run the scope-resolution algorithm in `references/scope-resolution.md`, then emit a fresh `<RESOLVED_SCOPE>` marker before continuing. Do not proceed without resolved scope.

**Cross-check against workflow 03 approval.** The marker must match the session-disposition header the user approved. If the user named additional sessions during workflow 03, add them before archiving. If any session is classified **ambiguous**, STOP and resolve with the user before proceeding.

The existence of any session is never permission to archive an in-scope session — permission flows from completion of this workflow against the resolved scope.

</resolve_session_scope>

<write_canonical_continuation>
Every closure ends with **zero or one** handoff. Pick the path once and execute it. Zero is correct when no continuation reader exists.

**Worktree precondition:** any path that invokes `spx session handoff` (Path C) requires an allowed git state. From a linked worktree, reach it first — see `<release_work_branch>` below — before running the command.

**Path A — `--no-session` (zero handoffs)**: skip to `<archive_scope>`. All in-scope sessions are archived; no handoff file is created. After archiving, confirm: "Closed without continuation. All approved items persisted and committed. Archived scope: <list>." Do NOT describe this as "released to todo" — it is an archive-and-close, not a return-to-queue.

**Path B — rewrite in place (one handoff, artifact exists)**: a mid-session artifact is still in TODO.

1. Use the artifact id from `<resolve_session_scope>`. Derive its file path from `spx session show <artifact-id>` or the root worktree's `.spx/sessions/todo/<artifact-id>.md`.
2. Do NOT run `spx session handoff` — that would create a second handoff and break the one-handoff end state.
3. Read the artifact frontmatter and preserve its existing `created_at`, `agent_session_id`, and `git_ref` values.
4. Write (overwrite) the artifact file using the template in `references/session-format.md`. The file content is the canonical continuation with cumulative scope from every in-scope session.
5. Omit `result` from the rewritten artifact because it remains an available TODO continuation.
6. Use `<HANDOFF_ID>` = artifact id for the confirmation message.

**Path C — new handoff (one handoff, no artifact)**:

1. Compose the canonical continuation using `references/session-format.md`: a JSON header object of caller fields (non-empty `goal` and `next_step`; omit `result`) and the markdown body.
2. Pipe the JSON header on the first line, then the body bytes verbatim, to `spx session handoff`. Do not run `spx session handoff` with empty stdin, and do not pipe YAML frontmatter — the command rejects input that opens with `---` and prefills `created_at`, `agent_session_id`, and `git_ref` itself.
   ```bash
   # stdin = JSON header on line 1, then the body verbatim; a leading
   # '#' or '---' in the body is literal, never parsed as frontmatter.
   printf '%s\n' '{"priority": "medium", "goal": "...", "next_step": "...", "specs": ["spx/{path-to-node}/{node-file}.md"], "files": ["src/{path-to-file}"]}' '[canonical continuation body — <metadata> through <incorporated_sessions>]' | spx session handoff
   ```
3. Parse output for `<HANDOFF_ID>` and `<SESSION_FILE>`.
4. Read `<SESSION_FILE>` to confirm it exists and contains the CLI-prefilled `created_at`, `agent_session_id` when available, and `git_ref` values.

**Content of the canonical continuation (B and C):**

- Header — for Path C, a JSON header object of caller fields (`priority`, `goal`, `next_step`, optional `specs`, optional `files`); for Path B, the YAML frontmatter with those fields plus the preserved prefilled context fields (`created_at`, `agent_session_id`, `git_ref`)
- `<nodes>` and `<skills>` — from workflow 01 (anchored nodes) and `<perspective_next_context>` in `02-reflect.md`
- `<persisted>` — files committed above, insights written, coordination notes created
- `<state_at_handoff>` (optional) — observable external-infrastructure state from `<perspective_external_state>`; omit when the repository carries every fact the next agent needs
- `<constraints>` (optional) — session-specific normative rules; omit when there are none
- `<coordination>` — unapproved items from workflow 03 that are coordination-only context
- `<incorporated_sessions>` — include ONLY when the in-scope set is non-empty; list each session id with its archive disposition

</write_canonical_continuation>

<release_work_branch>
A handoff RELEASES the work branch. The committed branch ref — not any checkout — carries the work forward, so after the handoff the releasing context steps off the branch and leaves it unoccupied for the next worktree or agent to claim via `/pickup`. This holds for every checkout kind; only the git mechanics differ. It is a post-handoff hygiene rule, not a worktree-only concern.

**Pre-handoff CLI precondition.** `spx session handoff` (Path C) requires an allowed git state before it will record the handoff, and that precondition differs by checkout kind:

- **Main checkout on a named branch** — already allowed; the CLI records the branch name. No pre-handoff detach is needed.
- **Linked (pool) worktree** — allowed only as a clean tree detached at the `origin/<default-branch>` tip; the CLI records that base SHA and REFUSES a linked worktree in any other state. When the committed work sits on a feature branch checked out in a linked worktree, detach to `origin/<default-branch>` before invoking the handoff. The commits persist on the branch ref in the shared `.git`, so detaching loses nothing:

  ```bash
  git switch --detach "$(git symbolic-ref --short refs/remotes/origin/HEAD)"
  ```

**Post-handoff step-off.** After the handoff is written, step off the released branch. The form follows the checkout kind:

- **Main checkout** — switch back to the base branch (the repository's default branch) so the feature branch is unoccupied:

  ```bash
  git switch "$(basename "$(git symbolic-ref --short refs/remotes/origin/HEAD)")"   # e.g. main
  ```

- **Linked (pool) worktree** — LEAVE it detached at the `origin/<default-branch>` tip.

NEVER re-check-out the handed-off branch "to return to where you were." Re-occupying it strands the queued continuation: another context cannot claim a branch this one still holds (and git refuses a branch already checked out in another worktree). `/pickup` checks the branch out when the session is claimed.
</release_work_branch>

<archive_scope>
After the canonical continuation is written and verified (Path B or C), or immediately under Path A, archive every session in the resolved scope plus any mid-session artifact that was NOT rewritten in place.

Archive order:

1. Earlier in-conversation pickups still in `doing/`.
2. The most recently claimed doing session, if any.
3. Any mid-session artifact this conversation created that is NOT the rewrite-in-place canonical (Path A archives all artifacts; Path C archives all when no rewrite happened).

Before each archive command, edit the session file being archived and add or update frontmatter `result` with a non-empty completion summary:

- For in-scope picked-up sessions: summarize what the closure persisted for that session and name the canonical continuation id when Path B or C created one.
- For mid-session artifacts being archived instead of rewritten: use a result such as `Reconciled into canonical continuation <id>.` or `Closed without continuation under --no-session.`
- Preserve existing frontmatter fields while adding `result`; do not add `tags` or `working_directory`.

```bash
spx session archive <session-id>
```

Run the command once per id. NEVER archive sessions classified as **unrelated** or **ambiguous**. NEVER archive the session that was just rewritten in place under Path B. NEVER archive TODO sessions created by other conversations — the TODO queue is shared across agents.

**Closure is incomplete if it creates or keeps more than one canonical continuation in TODO, or if it leaves an in-scope session in `todo/` or `doing/`.** Unrelated TODO sessions owned by other contexts are not this closure's concern and must be left untouched.

**If `--prune` is in `$ARGUMENTS`** (only after the canonical continuation is successfully written):

```bash
spx session list --status archive --json
spx session delete <archive-session-id>
```

NEVER delete todo or doing sessions. `--prune` only affects archive.

</archive_scope>

<confirm>
State:

- Canonical continuation: "new handoff <id>" | "rewrote <artifact-id> in place" | "no handoff (--no-session)"
- Session-owned work was committed before closure
- Every session id archived from the resolved scope (and any artifact NOT rewritten in place)
- Checkout state: the releasing context has stepped off the handed-off branch — a main checkout switched back to the base branch, a linked worktree left detached at the `origin/<default-branch>` tip — and the branch is unoccupied

</confirm>

<success_criteria>

- All approved persistence items written.
- Session-owned files committed — `git status` shows no session-owned staged or unstaged changes.
- Committed vs uncommitted state recorded for each anchored node.
- Exactly zero or one canonical continuation created, rewritten, or intentionally omitted by THIS closure exists in TODO — never two. Unrelated TODO sessions owned by other contexts are out of scope and untouched.
- Continuation path executed via Path A (--no-session), Path B (rewrite in place), or Path C (new handoff).
- `<incorporated_sessions>` section present in the canonical continuation when a Path B or Path C handoff is written and the in-scope set is non-empty.
- Every in-scope session archived — none left in `todo/` or `doing/`.
- Every mid-session artifact this conversation created is reconciled: at most one rewritten in place, all others archived.
- Confirmation output names the continuation path and the archived ids.
- The releasing context has stepped off the handed-off branch — a main checkout switched back to the base branch, a linked worktree left detached at the `origin/<default-branch>` tip — and the branch is not re-checked-out.

</success_criteria>
