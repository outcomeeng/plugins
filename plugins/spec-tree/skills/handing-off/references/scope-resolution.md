<objective>
Resolve the authoritative set of in-scope sessions — every session the agent is responsible for closing. This algorithm is loaded by both workflow 02 (for `<perspective_session_scope>`) and workflow 04 (for `<resolve_session_scope>`). Update this file, not inline copies — both workflows must agree on what "in-scope" means.

The algorithm also locates any mid-session handoff artifact (a session file this conversation produced by running `spx session handoff` earlier). Workflow 04 reconciles artifacts separately — at most one rewrite-in-place, all others archived.

</objective>

<source_of_truth>

The agent's own session directory is the primary source of truth for in-scope sessions:

```
.spx/sessions/$CLAUDE_SESSION_ID/       (Claude Code runtime)
.spx/sessions/$CODEX_THREAD_ID/         (Codex runtime)
```

The CLI populates this directory: `spx session pickup` creates a symlink `<session-id>.md` pointing at `../doing/<session-id>.md` on every successful claim; `spx session archive` removes the symlink on closure. The directory accumulates every session this runtime has claimed — survives `/clear` and `/compact` because it's on disk, not in conversation history.

Conversation markers (`<PICKUP_CLAIM>`, `<PICKUP_CHECKPOINT>`, `<SESSION_SCOPE>`) are a **cross-check**, not an authority. They catch cases where the filesystem and the conversation disagree — e.g. a symlink vanished, a marker was injected without a real claim, or a compaction truncated the marker series. Flag disagreement; never silently prefer one source over the other.

</source_of_truth>

<algorithm>

**Step 1 — Read the filesystem accumulator.**

```bash
ls .spx/sessions/"$CLAUDE_SESSION_ID"/ 2>/dev/null
```

For each entry:

- If the name matches `YYYY-MM-DD_HH-MM-SS.md` and the symlink resolves to a file in `doing/` → **claimed, still open** (in-scope).
- If the symlink resolves to a file in `archive/` → **already archived** (out of scope; workflow 04 does not touch it).
- If the symlink dangles (target missing) → **dangling**. The queue file was removed by another path; record it and flag to the user. Do not silently skip.

For Codex, substitute `$CODEX_THREAD_ID`. If neither variable is set (the agent is running outside a session context that the hook covers), skip the filesystem step and fall through to Step 2's marker path — note the degraded mode in the verdict output.

If the directory exists but is empty → no sessions claimed by this runtime. Proceed to Step 2 to cross-check; a fresh handoff is the expected case.

If the directory does not exist → either no claim happened or the CLI is older than the accumulator change. Fall through to Step 2 and note the degraded mode.

**Step 2 — Cross-check against conversation markers.**

Walk the conversation for the most recent `<SESSION_SCOPE ids="a,b,c">` marker. If missing, recover in this order:

- **Step 2a — checkpoint scope attribute (preferred).** If a `<PICKUP_CHECKPOINT id="..." scope="a,b,c">` exists, parse its `scope` attribute. One surviving checkpoint recovers a multi-session scope without every earlier claim marker.
- **Step 2b — additive rebuild.** Otherwise collect every `<PICKUP_CLAIM id="...">` and `<PICKUP_CHECKPOINT id="...">` since the last closure marker. Deduplicate by id.

Compare the marker-derived set against the filesystem-derived set:

- **Sets agree** → the resolved scope is their common value.
- **Filesystem is a superset of markers** → conversation markers were dropped (compaction) but the filesystem survived. The filesystem set is authoritative; include the extra ids.
- **Markers are a superset of filesystem** → a claim marker was emitted but the symlink was never created (older CLI, bug, or manual intervention). STOP and ask the user before proceeding — one of the claims may be fictitious.
- **Sets disjoint** → both sources are partial. STOP and ask the user.

Never silently prefer one source. Disagreement is a signal that something upstream is wrong.

**Step 3 — Scope growth rule.**

Scope grows ONLY by user confirmation. A session's presence in `doing/` without a symlink in the runtime's accumulator is NOT permission to claim it as in-scope — another agent may own that work.

**Step 4 — Locate mid-session artifacts.**

Did this conversation run `spx session handoff` earlier? Collect every handoff id printed by `spx session handoff` during this conversation (these ids are ephemeral to the current conversation and are tracked in the transcript, not on disk). Cross-reference against `spx session list --status todo`:

- **Zero artifacts in TODO** → no reconciliation needed; workflow 04 will use Path A or C.
- **Exactly one artifact in TODO** → it becomes the rewrite-in-place candidate for Path B.
- **More than one artifact in TODO** → STOP. Present the list to the user and ask which is the canonical continuation. Archive only the artifacts this conversation created; never touch artifacts created by other conversations.

</algorithm>

<classification>

After resolving scope and locating artifacts, every session observed falls into exactly one class:

- **in-scope** — present in the runtime accumulator AND (reconciled with markers when available) confirmed by user action. Will be archived after the canonical continuation is verified.
- **mid-session artifact** — created by this conversation's earlier `spx session handoff` and still in TODO. Workflow 04 will either rewrite it in place as the canonical continuation or archive it.
- **unrelated** — belongs to another agent or another conversation. Leave untouched.
- **dangling** — symlink present in the runtime accumulator but target missing. Flag for the user; do not archive or close based on a dangling link.
- **ambiguous** — filesystem and markers disagree. STOP and ask the user before creating a handoff.

The existence of a mid-session artifact is never, by itself, permission to archive an in-scope session. Permission flows from completing the closure workflow against the resolved scope.

</classification>

<consumers>

This algorithm has two callers:

- **Workflow 02 (`<perspective_session_scope>`)** — uses the resolved scope and classification to drive reflection and to feed the session-disposition header in workflow 03. Does not archive or write anything.
- **Workflow 04 (`<resolve_session_scope>`)** — uses the same resolved scope and classification to drive archival and canonical-continuation selection (Paths A/B/C). Cross-references the user-approved disposition from workflow 03; if the user named additional sessions during reflection, adds them before archiving.

Both consumers MUST use this algorithm unchanged. Do not inline copies back into workflow files.

</consumers>
