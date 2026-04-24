<objective>
Resolve the authoritative set of in-scope sessions — every session the agent is responsible for closing. This algorithm is loaded by both workflow 02 (for `<perspective_session_scope>`) and workflow 04 (for `<resolve_session_scope>`). Update this file, not inline copies — both workflows must agree on what "in-scope" means.

The algorithm also locates any mid-session handoff artifact (a session file this conversation produced by running `spx session handoff` earlier). Workflow 04 reconciles artifacts separately — at most one rewrite-in-place, all others archived.

</objective>

<algorithm>

**Step 1 — Read the running scope marker.**

Search the conversation for the most recent `<SESSION_SCOPE ids="a,b,c">` marker. Each id is a user-confirmed pickup the agent must close. If present, that set is the resolved scope — skip to step 3.

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
