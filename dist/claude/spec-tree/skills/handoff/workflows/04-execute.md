<objective>
A completed closure execution state: approved persistence written, session-owned work committed, claimed sessions archived, and canonical continuation written, rewritten, or intentionally omitted.
</objective>

Work not committed here is not persisted.

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
4. Invoke `/commit-changes` to create the commit.

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

<resolve_claimed_sessions>
Read the `<RESOLVED_CLAIMED_SESSIONS ids="…" artifact_id="…">` marker emitted by workflow 02 (`<perspective_claimed_sessions>`). Use it as the authoritative archive list and artifact identifier for the rest of this workflow.

**If the marker is missing** (workflow 02 did not emit it, or context compaction dropped it): STOP and re-run the claimed-session-resolution algorithm in `references/claimed-session-resolution.md`, then emit a fresh `<RESOLVED_CLAIMED_SESSIONS>` marker before continuing. Do not proceed without resolved claimed-session set.

**Cross-check against workflow 03 approval.** The marker must match the session-disposition header the user approved. If the user named additional sessions during workflow 03, add them before archiving. If any session is classified **ambiguous**, STOP and resolve with the user before proceeding.

The existence of any session is never permission to archive a claimed session — permission flows from completion of this workflow against the resolved claimed-session set.

</resolve_claimed_sessions>

<resolve_existing_sessions>
Read the `<EXISTING_SESSION_RECONCILIATION status="…">` marker emitted by workflow 02. If the marker is missing, STOP and return to workflow 02; never create or propose a continuation session before the existing `todo` and `doing` queues have been searched by node path and topic.

Act on the marker:

- `status="none"` — Path C may create a new session only when `<CONTINUATION_SIGNAL state="present">` is backed by a real stop condition.
- `status="same-owner-continuation"` — Path B may rewrite the existing artifact, or the workflow may archive a same-owner duplicate according to the claimed-session rules.
- `status="existing-owner"` — Path C is forbidden. Another session already owns the continuation; leave that session untouched and close only if no other blocker remains.
- `status="ambiguous"` — STOP and ask the operator to choose ownership before mutating sessions.

</resolve_existing_sessions>

<write_canonical_continuation>
Every closure ends with **zero, one, or several** session files — one canonical continuation per independent continuation thread in the resolved claimed-session set. Pick the path for each and execute it. Zero is correct when no continuation reader exists.

**Worktree precondition:** any path that invokes `spx session handoff` (Path C) requires an allowed git state. From a linked worktree, reach it first — see `<release_work_branch>` below — before running the command.

**Path A — `--no-session` (zero handoffs)**: valid only when the `<CONTINUATION_SIGNAL>` emitted by workflow 02 is `absent`, or when `status="existing-owner"` confirms another session already owns the only remaining continuation and no local blocker remains. When the signal is `present` and no existing owner exists, `--no-session` contradicts the state — STOP and surface the contradiction through the runtime's structured-question tool (`AskUserQuestion` / `request_user_input`): name the unresolved stop condition and ask whether to create the continuation or confirm there is no continuation. NEVER silently honor `--no-session` against a `present` signal without an existing owner; automation must not skip a session file required by a real stop condition. When the signal is `absent`, `status="existing-owner"` owns the only remaining continuation with no local blocker, or the user explicitly re-confirms omission, skip to `<archive_claimed_sessions>`: all claimed sessions are archived, no handoff file is created. After archiving, confirm: "Closed without continuation. All approved items persisted and committed. Archived: <list>." Do NOT describe this as "released to todo" — it is an archive-and-close, not a return-to-queue.

**Path B — rewrite in place (one handoff, artifact exists)**: a mid-session artifact is still in TODO.

1. Use the artifact id from `<resolve_claimed_sessions>`. Derive its file path from `spx session show <artifact-id>` or the root worktree's `.spx/sessions/todo/<artifact-id>.md`.
2. Do NOT run `spx session handoff` — that would create a second handoff and break the one-handoff end state.
3. Read the artifact frontmatter and preserve its existing `created_at`, `agent_session_id`, and `git_ref` values.
4. Write (overwrite) the artifact file using the template in `references/session-format.md`. The file content is the canonical continuation with cumulative continuation from every claimed session.
5. Use `<HANDOFF_ID>` = artifact id for the confirmation message.

**Path C — new handoff (one handoff, no artifact)**:

0. Confirm `<EXISTING_SESSION_RECONCILIATION status="none">` and a real stop condition. Path C is forbidden for ordinary actionable coordination notes and forbidden when another `todo` or `doing` session already owns the same node/topic continuation.
1. Compose the canonical continuation using `references/session-format.md`: a JSON header object of caller fields (non-empty `goal` and `next_step`, plus `git_ref` naming the pushed work branch) and the markdown body.
2. Pipe the JSON header on the first line, then the body bytes verbatim, to `spx session handoff`. Do not run `spx session handoff` with empty stdin, and do not pipe YAML frontmatter — the command rejects input that opens with `---`. It prefills `created_at` and `agent_session_id`, and records the header's `git_ref` as the work branch after verifying that branch exists on `origin`; omit `git_ref` only when the work landed on the default branch with no feature branch, in which case the command derives the base from the git context.

   **Choose the stdin form by harness.**

   Interactive Claude Code or Codex sessions use a quoted heredoc. This keeps the canonical body readable and preserves apostrophes, `$`, backticks, and backslashes literally:

   ```bash
   spx session handoff <<'SPX_SESSION_HANDOFF'
   {"priority": "medium", "goal": "...", "next_step": "...", "git_ref": "<work-branch>", "specs": ["spx/{path-to-node}/{node-file}.md"], "files": ["src/{path-to-file}"]}
   <metadata>
     timestamp: [UTC timestamp]
     product: [Product name from cwd]
     git_ref: [work branch]
     git_status: clean
   </metadata>
   SPX_SESSION_HANDOFF
   ```

   Programmatic runners that require one physical command line use `printf` with one argument per output line, piped to stdin. The command below may wrap visually in a rendered view; keep it as one physical shell line. Literal apostrophes inside a line use the standard single-quote splice `'"'"'`. Do not use temporary files, helper files, command substitution, heredocs, backslash-newline continuations, `sed`, or `perl` to assemble or repair the body:

   ```bash
   printf '%s\n' '{"priority": "medium", "goal": "...", "next_step": "...", "git_ref": "<work-branch>", "specs": ["spx/{path-to-node}/{node-file}.md"], "files": ["src/{path-to-file}"]}' '<metadata>' '  timestamp: [UTC timestamp]' '  product: [Product name from cwd]' '  git_ref: [work branch]' '  git_status: clean' '</metadata>' | spx session handoff
   ```
3. Parse output for `<HANDOFF_ID>` and `<SESSION_FILE>`.
4. Read `<SESSION_FILE>` to confirm it exists and contains the prefilled `created_at` and `agent_session_id` when available, and the `git_ref` work branch.

**Content of the canonical continuation (B and C):**

- Header — for Path C, a JSON header object of caller fields (`priority`, `goal`, `next_step`, `git_ref` naming the pushed work branch, optional `specs`, optional `files`); for Path B, the YAML frontmatter with those fields plus the preserved prefilled context fields (`created_at`, `agent_session_id`, `git_ref`)
- `<nodes>` and `<skills>` — from workflow 01 (anchored nodes) and `<perspective_next_context>` in `02-reflect.md`
- `<persisted>` — files committed above, insights written, coordination notes created
- `<state_at_handoff>` (optional) — observable external-infrastructure state from `<perspective_external_state>`; omit when the repository carries every fact the next session needs
- `<constraints>` (optional) — session-specific normative rules; omit when there are none
- `<coordination>` — unapproved items from workflow 03 that are coordination-only context
- `<incorporated_sessions>` — include ONLY when the claimed-session set is non-empty; list each session id with its archive disposition

</write_canonical_continuation>

<release_work_branch>
A handoff frees the work branch for a future checkout, and it is valid only when the work it points at is recoverable from origin. The precondition is: every session-owned change is committed, the work branch is published to origin, its `@{upstream}` exists, and the branch is not ahead of it. When that does not hold, commit the work (the `<commit>` step) and push the work branch to origin **before** writing the session document. Unrelated dirty worktree changes are handled by the `<commit>` dirty-worktree rules; they do not make session-owned work uncommitted, but if they prevent the checkout transition or the CLI git-context gate, STOP and ask the owner to resolve them before writing a Path C session document. A chat-only or local-only handoff is never valid.

**Why this precondition exists.** A handoff promises cold Claude two things — the work is safe, and Claude can claim it — and running the handoff from the worktree that holds the work, stepped off the work branch, enforces both at once:

1. **The work is really pushed.** Detaching a pool worktree onto `origin/<default-branch>` is lossless only because the commits live on the branch ref and on origin, so the branch handoff step forces the push — turning the promise from a claim into a proof. An unpushed branch is invisible to every other checkout and machine; a session document pointing at it dangles.
2. **The branch is free to claim.** `/pickup` checks the work branch out in a pool worktree, and git refuses a branch already checked out elsewhere. A branch left occupied is precisely the one the next agent cannot use.

Run the handoff FROM the worktree that holds the work and step THAT worktree off the work branch; passing the work branch as `git_ref` then anchors the recorded ref to where the work actually is — the branch `/pickup` fetches and checks out.

**Two seductive instincts that each break a guarantee — act on neither:**

- *"Run the handoff from a worktree that's already clean."* It records `git_ref` at unrelated state and leaves the work branch occupied — the relocation bypass `SKILL.md` `<no_excuses>` forbids.
- *"Keep the work worktree on its branch so it's ready to continue."* The "ready to continue" worktree is exactly the one the next agent cannot use — `/pickup` cannot claim a branch this context still holds.

**Release mechanics by checkout kind.** First ensure the work branch is committed and pushed — `git push -u origin HEAD:refs/heads/<branch>` when `@{upstream}` is absent, else `git push` — then satisfy the `spx session handoff` git-context gate and step off:

- **Main checkout on a named branch** — the CLI records the branch name; no detach is needed. After the handoff, switch back to the base branch so the feature branch is unoccupied:

  ```bash
  git switch "$(basename "$(git symbolic-ref --short refs/remotes/origin/HEAD)")"   # e.g. main
  ```

- **Linked (pool) worktree** — the CLI's git-context gate accepts only a clean tree detached at the `origin/<default-branch>` tip and refuses any other linked-worktree state, so detach there after pushing; the commits persist on the branch ref in the shared `.git`, so detaching loses nothing. Pass the pushed work branch as the header's `git_ref` so the recorded ref is the branch (not the base tip the gate would otherwise record) — the gate still runs on the detached tip and is never bypassed. `/pickup` checks out the branch `git_ref` names. Leave the worktree detached afterward.

  ```bash
  git switch --detach "$(git symbolic-ref --short refs/remotes/origin/HEAD)"
  # then run spx session handoff with "git_ref": "<work-branch>" in the JSON header
  ```

NEVER re-check-out the handed-off branch "to return to the prior spot." Re-occupying it strands the queued continuation: another context cannot claim a branch this one still holds (and git refuses a branch already checked out in another worktree). `/pickup` checks the branch out when the session is claimed.
</release_work_branch>

<archive_claimed_sessions>
After the canonical continuation is written and verified (Path B or C), or immediately under Path A, archive every session in the resolved claimed-session set plus any mid-session artifact that was NOT rewritten in place.

Leave the running worktree's occupancy claim intact. Handoff archives or rewrites session documents and may step off a Git branch, but the runtime worktree claim belongs to the live process and remains until a later claim replaces it or liveness marks it free.

Archive order:

1. Earlier in-conversation pickups still in `doing/`.
2. The most recently claimed doing session, if any.
3. Any mid-session artifact this conversation created that is NOT the rewrite-in-place canonical (Path A archives all artifacts; Path C archives all when no rewrite happened).

```bash
spx session archive <session-id>
```

Run the command once per id. NEVER archive sessions classified as **unrelated** or **ambiguous**. NEVER archive the session that was just rewritten in place under Path B. NEVER archive TODO sessions created by other conversations — the TODO queue is shared across agents.

**Closure is incomplete if it creates or keeps more than one canonical continuation in TODO, or if it leaves a claimed session in `todo/` or `doing/`.** Unrelated TODO sessions owned by other contexts are not this closure's concern and must be left untouched.

**If `--prune` is in `$session_mode` or `$prune_mode`** (only after the canonical continuation is successfully written):

```bash
spx session list --status archive --json
spx session delete <archive-session-id>
```

NEVER delete todo or doing sessions. `--prune` only affects archive.

</archive_claimed_sessions>

<confirm>
State a human-readable closeout first, then the session mechanics. The operator has not read the command output, the PR page, or the changed files. A merge receipt or archive receipt alone is not enough.

The closeout MUST include:

- **Product outcome**: what capability, behavior, document, skill, page, test, or infrastructure state is now true in product terms. Say what changed for the user or maintainer, not only which branch or session changed.
- **Changed surface**: the meaningful files, sections, generated outputs, running service, or deployed surface. For skill and plugin work, name authored source and generated runtime output when both changed. For web app work, name the page or flow and the running URL when one exists. For pull-request work, include the PR URL.
- **Human-readable change summary**: the key sections, controls, behaviors, checks, or workflow rules changed, written so the operator can inspect the result without reconstructing it from the diff.
- **Verification evidence**: commands, audits, reviews, CI checks, screenshots, or manual inspections that passed, including exact session ids, run ids, PR numbers, or commit SHAs verbatim when they are part of the evidence.
- **Inspection surface**: a PR URL, merged commit, local file path, running URL, screenshot path, generated artifact path, or other place the operator can inspect the result. Include whichever surfaces apply; omit unavailable surfaces rather than inventing one.
- **Delivered state**: where the work now lives — default branch on origin, local branch, running dev server, generated plugin install, archived session state, or intentionally local output.
- **Remaining work**: open follow-up only when one exists, with its owner or tracking location. Say when none remains for this closure.

Use domain-specific closeout content. In a plugin marketplace repository, a useful closeout usually names the skill or spec-tree behavior changed, authored source paths, generated `dist/` paths when regenerated, verification commands, auditor or reviewer verdict ids, PR URL, merged commit, marketplace sync status, and any active PLAN.md or ISSUES.md continuation. In a web app, a useful closeout usually names the changed page or flow, the running URL, the test page or route, browser verification, screenshots if captured, and any known UI follow-up.

Put session mechanics only after the product summary:

- Canonical continuation: "new handoff <id>" | "rewrote <artifact-id> in place" | "no handoff (--no-session)"
- Session-owned work was committed before closure
- Every session id archived from the resolved claimed-session set (and any artifact NOT rewritten in place)
- Checkout state: the releasing context has stepped off the handed-off branch — a main checkout switched back to the base branch, a linked worktree left detached at the `origin/<default-branch>` tip — and the branch is unoccupied
- Worktree occupancy claim preserved for the live process; session-store cleanup used `spx session archive` for claimed sessions and `spx session release` only for verified stale `doing/` records

</confirm>

<success_criteria>

- All approved persistence items written.
- Session-owned files committed — `git status` shows no session-owned staged or unstaged changes.
- Committed vs uncommitted state recorded for each anchored node.
- Existing `todo` and `doing` sessions searched by node path and topic before any Path C handoff, with `<EXISTING_SESSION_RECONCILIATION>` present.
- Exactly zero or one canonical continuation per independent continuation thread created, rewritten, or intentionally omitted by THIS closure exists in TODO — never two for the same thread. Unrelated TODO sessions owned by other contexts are out of scope and untouched.
- Continuation path executed via Path A (--no-session), Path B (rewrite in place), or Path C (new handoff).
- `<incorporated_sessions>` section present in the canonical continuation when a Path B or Path C handoff is written and the claimed-session set is non-empty.
- Every claimed session archived — none left in `todo/` or `doing/`.
- Every mid-session artifact this conversation created is reconciled: at most one rewritten in place, all others archived.
- Confirmation output names the continuation path and the archived ids.
- The releasing context has stepped off the handed-off branch — a main checkout switched back to the base branch, a linked worktree left detached at the `origin/<default-branch>` tip — and the branch is not re-checked-out.

</success_criteria>
