<objective>
Resolve the authoritative set of in-scope sessions — every session Claude is responsible for closing. This algorithm is the canonical source of truth for "in-scope". Workflow 02 runs it in `<perspective_session_scope>` and emits a `<RESOLVED_SCOPE>` marker into the conversation. Workflow 04 reads the marker rather than re-running the algorithm; if the marker is missing (context compaction or workflow 02 skipped), workflow 04 re-runs the algorithm here.

The algorithm also locates any mid-session handoff artifact (a session file this conversation produced by running `spx session handoff` earlier). Workflow 04 reconciles artifacts separately — at most one rewrite-in-place, all others archived.

</objective>

<algorithm>

**Step 1 — Read the running scope marker.**

Search the conversation for the most recent `<SESSION_SCOPE ids="a,b,c">` marker. Each id is a user-confirmed pickup Claude must close. If present, that set is the resolved scope — skip to step 3.

**Step 2 — Fallback when no scope marker exists.**

Context compaction or a malformed marker can drop `<SESSION_SCOPE>`. Recover in this order:

- **Step 2a — checkpoint scope attribute (preferred).** If the most recent `<PICKUP_CHECKPOINT id="..." scope="a,b,c">` exists, parse its `scope` attribute. That attribute carries the full scope as of the latest post-context checkpoint — use it as the authoritative resolved scope. One surviving checkpoint can recover a multi-session scope without needing every earlier claim marker.
- **Step 2b — additive rebuild (no checkpoint scope available).** If no `<PICKUP_CHECKPOINT>` carries a `scope` attribute, collect every `<PICKUP_CLAIM id="...">` and `<PICKUP_CHECKPOINT id="...">` emitted since the last closure marker. Deduplicate by id.
- **Validate the recovered set.**
  - **One id** → proceed.
  - **More than one id** → STOP and ask the user to confirm the full scope before continuing. NEVER silently collapse to the most recent pickup — that is the exact failure mode the additive rule exists to prevent.
  - **Empty** → check for pickup evidence: `spx session list --status doing` showing sessions this worktree may own, or references in the conversation to a claimed session. If any such evidence exists, STOP and ask the user to confirm scope. Only declare scope empty when there is clear evidence no pickup happened in this conversation (fresh handoff).

**Step 3 — Scope growth rule.**

Scope grows ONLY by user confirmation. Do NOT auto-scan the todo queue to add sessions. Another agent may own work that looks related but is not yours to close.

**Step 4 — Locate mid-session artifacts.**

Did this conversation run `spx session handoff` earlier? Collect every handoff id printed by `spx session handoff` during this conversation. Cross-reference against `spx session list --status todo`:

- **Zero artifacts in TODO** → no reconciliation needed; workflow 04 will use Path A or C.
- **Exactly one artifact in TODO** → it becomes the rewrite-in-place candidate for Path B.
- **More than one artifact in TODO** → STOP. Present the list to the user and ask which is the canonical continuation. Archive only the artifacts this conversation created; never touch artifacts created by other conversations.

**Step 5 — Emit the resolved-scope marker.**

After steps 1-4 produce the resolved scope and artifact id, emit a marker into the conversation so workflow 04 reads from context rather than re-running the algorithm:

```text
<RESOLVED_SCOPE ids="id-1,id-2,..." artifact_id="id-or-none">
in_scope: id-1, id-2, ...
mid_session_artifact: id-or-none
</RESOLVED_SCOPE>
```

Use `ids=""` for a fresh handoff with no prior pickup. Use `artifact_id="none"` when no mid-session artifact exists.

</algorithm>

<classification>

After resolving scope and locating artifacts, every session observed falls into exactly one class:

- **in-scope** — named in the resolved scope. Will be archived after the canonical continuation is verified.
- **mid-session artifact** — created by this conversation's earlier `spx session handoff` and still in TODO. Workflow 04 will either rewrite it in place as the canonical continuation or archive it.
- **unrelated** — belongs to another agent or another conversation. Leave untouched.
- **ambiguous** — STOP and ask the user before creating a handoff.

The existence of a mid-session artifact is never, by itself, permission to archive an in-scope session. Permission flows from completing the closure workflow against the resolved scope.

</classification>

<consumers>

This algorithm has two callers:

- **Workflow 02 (`<perspective_session_scope>`)** — uses the resolved scope and classification to drive reflection and to feed the session-disposition header in workflow 03. Does not archive or write anything.
- **Workflow 04 (`<resolve_session_scope>`)** — uses the same resolved scope and classification to drive archival and canonical-continuation selection (Paths A/B/C). Cross-references the user-approved disposition from workflow 03; if the user named additional sessions, adds them before archiving.

Both consumers MUST use this algorithm unchanged. Do not inline copies back into workflow files.

</consumers>
