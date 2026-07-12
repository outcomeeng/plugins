<objective>
A completed closure execution state: approved persistence written, session-owned work committed, claimed sessions archived, and every thread's canonical continuation created or intentionally omitted.
</objective>

<required_reading>
Before writing a session file, read `${CLAUDE_SKILL_DIR}/references/session-format.md` for the canonical template.

</required_reading>

<process>

Work not committed here is not persisted.

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
Read the `<RESOLVED_CLAIMED_SESSIONS ids="…" artifact_ids="…">` marker emitted by workflow 02 (`<perspective_claimed_sessions>`). The `ids` attribute is the authoritative claimed-session archive set. The `artifact_ids` attribute is a candidate set only.

Require the `<RESOLVED_ARTIFACT_PARTITIONS>` marker emitted by workflow 03 whenever `<RESOLVED_CONTINUATION_THREADS>` is non-empty. Verify that it contains exactly one `partition` for every resolved thread and no extra partition, that its `candidate_ids` equals the flat candidate set, and that every candidate appears in exactly one partition's `archive_ids`. A missing or duplicate thread partition, missing marker, thread-set mismatch, duplicate candidate assignment, absent candidate assignment, or zero/multiple-thread mapping stops the workflow and returns to workflow 03 before creating or archiving a session.

**If the marker is missing**: STOP and return to workflow 02. When context compaction dropped it, first invoke `/understand` followed by `/contextualize` for every spec node still in scope, then rerun workflows 02-03 so the claimed-session marker and artifact partitions are reconstructed and approved before execution resumes. Do not proceed without the reloaded foundation, node contexts, resolved claimed-session set, and matching partitions.

**Cross-check against workflow 03 approval.** The marker must match the session-disposition header the user approved. If the user named additional sessions during workflow 03, add them before archiving. If any session is classified **ambiguous**, STOP and resolve with the user before proceeding.

The existence of any session is never permission to archive a claimed session — permission flows from completion of this workflow against the resolved claimed-session set.

</resolve_claimed_sessions>

<resolve_continuation_threads>
Read `<RESOLVED_CONTINUATION_THREADS>` from workflow 02. If it is missing, contains a duplicate thread id, or its thread-id set differs from `<RESOLVED_ARTIFACT_PARTITIONS>`, STOP and return to workflows 02-03. Never create, omit, or archive a thread before its queue ownership and continuation state are resolved.

Before processing partitions, require every thread record to have a resolved owner status; an `ambiguous` thread record stops all session-state changes and returns to workflow 03 before any partition is processed. For each partition, require the matching thread record and disposition: `fresh-session` requires `continuation="present"`, owner status `none` or `same-owner-continuation`, and a real stop condition; `zero-handoff` requires `continuation="absent"`; `existing-owner` requires owner status `existing-owner`. Process each valid pair independently.

</resolve_continuation_threads>

<write_canonical_continuation>
Every closure ends with **zero, one, or several** session files — one canonical continuation per resolved thread whose partition has a `fresh-session` disposition. Threads are independent of whether the claimed-session set is empty. Process each partition independently: execute its disposition, verify that thread's continuation state, then archive only that record's `archive_ids`. Complete one partition before processing the next. Zero sessions is correct when no continuation reader exists.

**Worktree precondition:** any path that invokes `spx session handoff` requires an allowed git state. From a linked worktree, reach it first — see `<release_work_branch>` below — before running the command.

**Path A — no fresh handoff for this partition**: valid when the matching thread has `continuation="absent"`, or when `owner_status="existing-owner"` confirms another session carries that thread. Plain merge lifecycle invocations need no no-session option when no reader exists. When `<HANDOFF_OPTIONS no_session="true" ... />` meets a thread with `continuation="present"` and no existing owner, STOP and surface that thread-specific contradiction through the runtime's structured-question tool (`AskUserQuestion` / `request_user_input`): name the thread and unresolved stop condition, then ask whether to create its continuation or confirm it has no continuation. NEVER let one valid zero-handoff thread suppress another thread's required fresh session. For a valid `zero-handoff` or `existing-owner` partition, skip to `<archive_claimed_sessions>` and archive only that partition's `archive_ids` after its no-reader or owner state is verified. Do NOT describe this as "released to todo" — it is an archive-and-close, not a return-to-queue.

**Fresh session path — new handoff**:

0. Confirm the matching thread record has `continuation="present"`, owner status `none` or `same-owner-continuation`, and a real stop condition. Creating a fresh session is forbidden for ordinary actionable coordination notes and for a thread another `todo` or `doing` session owns.
1. Compose the canonical continuation using the JSON-header, body, and field contract in `${CLAUDE_SKILL_DIR}/references/session-format.md`.
2. Resolve and record the exact expected pickup anchor before filing: the supplied pushed work branch; otherwise `git branch --show-current` for a named default-branch checkout; otherwise the full `git rev-parse HEAD` SHA for a detached checkout. Resolve the current runtime identity verbatim (`printenv CODEX_THREAD_ID` in Codex; `printenv CLAUDE_SESSION_ID` in Claude Code) and STOP when it is empty. Invoke the harness-specific stdin form from `${CLAUDE_SKILL_DIR}/references/session-format.md` exactly. Do not run `spx session handoff` with empty stdin or YAML frontmatter.
3. Parse output for `<HANDOFF_ID>` and `<SESSION_FILE>`.
4. Run `spx session show --json <HANDOFF_ID>` and require the stored `git_ref` to equal the expected pickup anchor recorded before filing, whether that anchor was supplied or derived. Require the stored `agent_session_id` to equal the runtime identity recorded before filing and require a non-empty `created_at`. A missing or different anchor or identity leaves the fresh-session partition unverified: archive no artifact from that partition and stop with the mismatch.

Populate the canonical fields from workflow 01 and workflow 02 using `${CLAUDE_SKILL_DIR}/references/session-format.md`; that reference is the sole payload-content contract.

</write_canonical_continuation>

<release_work_branch>
A handoff frees the work branch for a future checkout, and it is valid only when the work it points at is recoverable from origin. The precondition is: every session-owned change is committed, the work branch is published to origin, its `@{upstream}` exists, and the branch is not ahead. When that does not hold, commit the work (the `<commit>` step) and push the work branch to origin **before** writing the session document. Unrelated dirty worktree changes are handled by the `<commit>` dirty-worktree rules; they do not make session-owned work uncommitted, but if they prevent the checkout transition or the CLI git-context gate, STOP and ask the owner to resolve them before writing a fresh session document. A chat-only or local-only handoff is never valid.

**Why this precondition exists.** A handoff promises cold Claude two things — the work is safe, and Claude can claim it — and running the handoff from the worktree that holds the work, stepped off the work branch, enforces both at once:

1. **The work is really pushed.** Detaching a pool worktree onto `origin/<default-branch>` is lossless only because the commits live on the branch ref and on origin, so the branch handoff step forces the push — turning the promise from a claim into a proof. An unpushed branch is invisible to every other checkout and machine; a session document pointing at it dangles.
2. **The branch is free to claim.** `/pickup` checks the work branch out in a pool worktree, and git refuses a branch already checked out elsewhere. A branch left occupied is precisely the one the next agent cannot use.

Run the handoff FROM the worktree that holds the work and step THAT worktree off the work branch; passing the work branch as `git_ref` then anchors the recorded ref to where the work actually is — the branch `/pickup` fetches and checks out.

**Two seductive instincts that each break a guarantee — act on neither:**

- *"Run the handoff from a worktree that's already clean."* It records `git_ref` at unrelated state and leaves the work branch occupied — the relocation bypass `SKILL.md` `<no_excuses>` forbids.
- *"Keep the work worktree on its branch so it's ready to continue."* The "ready to continue" worktree is exactly the one the next agent cannot use — `/pickup` cannot claim a branch this context still holds.

**Release mechanics by checkout kind.** First ensure the work branch is committed and pushed — `git push -u origin HEAD:refs/heads/<branch>` when `@{upstream}` is absent, else `git push` — then run `git fetch origin` so `refs/remotes/origin/HEAD` and its target are current before satisfying the `spx session handoff` git-context gate and stepping off:

- **Main checkout on a named branch** — the CLI records the branch name; no detach is needed before filing. After the handoff, detach at the remote base tip so the feature branch is unoccupied:

  ```bash
  git switch --detach "$(git symbolic-ref --short refs/remotes/origin/HEAD)"
  ```

- **Linked (pool) worktree** — the CLI's git-context gate accepts only a clean tree detached at the `origin/<default-branch>` tip and refuses any other linked-worktree state, so detach there after pushing; the commits persist on the branch ref in the shared `.git`, so detaching loses nothing. Pass the pushed work branch as the header's `git_ref` so the recorded ref is the branch (not the base tip the gate would otherwise record) — the gate still runs on the detached tip and is never bypassed. `/pickup` checks out the branch `git_ref` names. Leave the worktree detached afterward.

  ```bash
  git switch --detach "$(git symbolic-ref --short refs/remotes/origin/HEAD)"
  # then run spx session handoff with "git_ref": "<work-branch>" in the JSON header
  ```

NEVER re-check-out the handed-off branch "to return to the prior spot." Re-occupying it strands the queued continuation: another context cannot claim a branch this one still holds (and git refuses a branch already checked out in another worktree). `/pickup` checks the branch out when the session is claimed.
</release_work_branch>

<archive_claimed_sessions>
After each canonical continuation is written and verified, archive only that thread partition's `archive_ids`. Under Path A, archive that partition after zero-handoff is confirmed valid for its thread: no replacement reader remains, or the named existing owner carries that thread's continuation. Archive the resolved claimed-session set after every artifact partition has reached its verified disposition, so one failed partition leaves the remaining thread artifacts untouched.

Leave the running worktree's occupancy claim intact. Handoff creates fresh session documents, archives session documents, and may step off a Git branch, but the runtime worktree claim belongs to the live process and remains until a later claim replaces it or liveness marks it free.

Archive selected superseded artifacts only after the fresh session has been verified, or after Path A is confirmed valid for that partition. A failed fresh-session creation leaves every artifact candidate untouched.

Archive order:

1. After each partition reaches its verified disposition, archive that partition's `archive_ids`.
2. After every partition succeeds, archive earlier in-conversation pickups still in `doing/`.
3. Archive the most recently claimed doing session, if any.

```bash
spx session archive <session-id>
```

Run the command once per id. NEVER archive sessions classified as **unrelated** or **ambiguous**. NEVER archive TODO sessions created by other conversations — the TODO queue is shared across agents.

**Closure is incomplete if it creates or keeps more than one canonical continuation per thread in TODO, or if it leaves a claimed session in `todo/` or `doing/`.** Unrelated TODO sessions owned by other contexts are not this closure's concern and must be left untouched.

**If `<HANDOFF_OPTIONS prune="true" ... />` was emitted** (only after at least one fresh continuation is successfully written), require the `<APPROVED_PRUNE ids="...">` marker from workflow 03 and delete only its exact ids. A missing marker means deletion was not approved; preserve every archived session and stop prune processing. An empty approved set is a no-op.

```bash
spx session delete <archive-session-id>
```

NEVER delete todo or doing sessions. `--prune` only affects archive.

</archive_claimed_sessions>

<confirm>
State a human-readable closeout first, then the session mechanics. The operator has not read the command output, changed files, rendered result, logs, or external records. A merge receipt or archive receipt alone is not enough.

The closeout MUST include:

- **Product outcome**: answer, in plain English, why the operator should be glad about the work's delivered or parked state. For a default-branch merge closeout, explain why the merged work is valuable. For a continuation handoff before default-branch delivery, explain what useful product state is preserved for pickup without claiming the work is merged. Use the loaded Spec Tree ancestry to translate the payload into the product benefit at the right scale. A small bug fix or technical-debt cleanup may be described plainly as a bug fix or debt cleanup. Keep lifecycle mechanics and repository identifiers out of this value field.
- **Changed product surface**: name the user-facing, operator-facing, methodology-facing, command, workflow, document, API, page, data projection, configuration, generated contract, skill contract, or other shipped behavior that improved or is being preserved for pickup. Use product language from the loaded ancestry rather than filenames, file paths, generated-output paths, or transport records.
- **Human-readable change summary**: answer what changed, why it matters to the operator, and what additional benefit continuing would create when follow-up remains. Write the summary so the operator can understand the result from product language alone, without reconstructing it from a diff, branch, pull request, file list, generated tree, installed version, or archive receipt.
- **Verification evidence**: commands, audits, reviews, CI checks, screenshots, manual inspections, run ids, session ids, PR numbers, commit SHAs, or other proof that passed. Reproduce identity values verbatim when they are part of the evidence.
- **Inspection references**: places the operator can inspect the result or its evidence: local file paths, generated artifact paths, rendered pages, running URLs, deployed URLs, PR URLs, merged commits, screenshots, journal runs, logs, or external records. Include whichever references apply; omit unavailable references rather than inventing one.
- **Delivered state**: one concise field naming where the work now lives — default branch on origin, local branch, running service, deployed environment, generated install, archived session state, or intentionally local output. This field never becomes the closeout title or first section.
- **Remaining work**: open follow-up only when one exists, with its owner or tracking location. Say when none remains for this closure.
- **Remaining Branches**: for merge lifecycle closeout, group branch state under exactly four labels — **Deleted locally**, **Deleted remotely**, **Retained, with reason**, and **Needs operator decision, with exact evidence**. Include full branch names and full commit SHAs.

When closing after a default-branch merge, compute or preserve the merge transport's branch-state closeout record from `/merging-standards` `<branch_state_closeout>` before final confirmation. The record includes PR number and merge commit SHA when applicable, merged branch name, remote branch existence, local branch existence, local fully-merged status against `origin/<base>`, gone-upstream tracking status, preservation branch existence, preservation branch ancestry or `git cherry -v --abbrev=40 origin/<base> <branch>` patch-equivalence evidence, final worktree state, and release-source state when a post-merge release used one.

Classify default-branch merge state, installed location, and generated install state under **Delivered state**. Classify release-source refresh, installed artifact version, CI/check state, audit/review outputs, and command evidence under **Verification evidence** or **Inspection references** when they prove the delivered state. Classify branch cleanup under **Remaining Branches**. Classify session archival and handoff state under the session-mechanics block.

Apply the cleanup policy before writing the closeout: delete a still-existing remote feature branch through the approved merge lifecycle deletion command; delete a local feature branch only when it exists, tracks a gone upstream, and is fully merged into `origin/<base>`; delete a no-remote preservation branch when all substantive commits are present on `origin/<base>` by ancestry or patch equivalence unless the branch name or operator instruction marks retained evidence. Never delete a branch checked out in another live worktree; report the exact worktree path and branch. Never delete a branch whose commits are neither ancestors nor patch-equivalent to `origin/<base>`; report the unmatched full SHAs and keep it.

Adapt the closeout to the product domain. Use the loaded Spec Tree ancestry as the source vocabulary for the value fields while keeping the outcome proportional to the change. Examples: an application change explains the improved page, flow, API, service, or deployment behavior and keeps the runtime URL or screenshot in inspection references; a library or CLI change explains the improved command, projection, schema, output contract, or public API and keeps command evidence in verification evidence; a documentation or methodology change explains the improved document, workflow, skill, or generated contract and keeps file paths and audit or review evidence in their mechanical fields.

<rejected_repository_inventory_surface>

NEVER fill **Changed product surface** or **Human-readable change summary** with a repository inventory. This shape is the anti-pattern:

```text
Changed product surface:
- the handoff workflow file
- the generated runtime copy
- the sessions specification
```

Why it fails: the operator still has to infer the product benefit from storage locations. Translate those locations into product language, then put their paths under **Inspection references**.

</rejected_repository_inventory_surface>

<rejected_delivered_state_receipt>

NEVER replace the product closeout with a section headed `Delivered state` whose bullets only report transport, branch, sync, or session mechanics. This receipt shape is the anti-pattern:

```text
Delivered state:
- Merge commit: <full-sha>
- PR head merged: <full-sha>
- Default branch fast-forwarded
- Sync command passed
- Session <session-id> archived
```

Why it fails: the operator still has to reconstruct the product outcome, changed product surface, workflow behavior, verification meaning, inspection references, and remaining-work state from mechanics. If these facts matter, place them under **Verification evidence**, **Inspection references**, **Delivered state**, **Remaining work**, **Remaining Branches**, or the session-mechanics block after the product summary.

</rejected_delivered_state_receipt>

<rejected_misclassified_product_outcome>

NEVER put delivery, release, branch, version, or session mechanics under **Product outcome**. This sentence shape is the anti-pattern:

```text
Product outcome: the changes are now on origin/main, and the release source was refreshed so the installed artifact is current.
```

Why it fails: the label is filled with lifecycle evidence rather than the payload's changed behavior or shipped product surface. First name what changed in the product, skill, command, workflow, document, or generated artifact contract; then place default-branch, release-source, installed-version, PR, branch, and session facts under the matching evidence, state, reference, branches, or mechanics field.

</rejected_misclassified_product_outcome>

Put session mechanics only after the product summary:

- Continuation threads: one row per thread with "new handoff <id>", "no handoff (no continuation reader needed)", or "existing owner <session-id>"
- Session-owned work was committed before closure
- Every session id archived from the resolved claimed-session set and selected artifact partition
- Checkout state: the releasing context has stepped off the handed-off branch and is detached at the current `origin/<default-branch>` tip, so the branch is unoccupied
- Worktree occupancy claim preserved for the live process; session-store cleanup used `spx session archive` only for the closure's claimed sessions and selected same-conversation artifacts

</confirm>

</process>

<success_criteria>

- All approved persistence items written.
- Session-owned files committed — `git status` shows no session-owned staged or unstaged changes.
- Committed vs uncommitted state recorded for each anchored node.
- Existing `todo` and `doing` sessions searched by node path and topic before any fresh handoff, with one `<RESOLVED_CONTINUATION_THREADS>` record per independent thread.
- Exactly zero or one canonical continuation per independent continuation thread created or intentionally omitted by THIS closure exists in TODO — never two for the same thread. Unrelated TODO sessions owned by other contexts are out of scope and untouched.
- Every partition executed through its matching no-fresh-handoff or fresh-session path.
- `<incorporated_sessions>` section present in the canonical continuation when a fresh handoff is written and the claimed-session set or superseded same-conversation artifact set is non-empty.
- Every claimed session archived — none left in `todo/` or `doing/`.
- Every mid-session artifact this conversation created is reconciled: a fresh session replaces it when continuation remains, and superseded artifacts are archived.
- Confirmation output names every thread disposition and the archived ids.
- Default-branch merge closeout includes the branch-state closeout record fields from `/merging-standards` `<branch_state_closeout>` or an explicitly preserved record from the merge transport.
- Merge lifecycle final output includes `Remaining Branches` grouped under **Deleted locally**, **Deleted remotely**, **Retained, with reason**, and **Needs operator decision, with exact evidence**.
- Confirmation output never uses a top-level `Delivered state` receipt as a substitute for the product-first closeout fields.
- The releasing context has stepped off the handed-off branch — both a main checkout and a linked worktree are left detached at the `origin/<default-branch>` tip — and the branch is not re-checked-out.

</success_criteria>
