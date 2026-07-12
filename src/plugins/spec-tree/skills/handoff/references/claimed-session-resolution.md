<objective>
The authoritative claimed-session set, same-conversation artifact candidates, classifications, and `<RESOLVED_CLAIMED_SESSIONS>` marker consumed by the handoff workflows.

The algorithm also locates any mid-session handoff artifacts (session files this conversation produced by running `spx session handoff` earlier). Workflow 04 reconciles artifacts separately: create a fresh canonical session when continuation remains, then archive every superseded same-conversation artifact.

</objective>

<algorithm>

**Step 1 — Read the running CLAIMED_SESSIONS marker.**

Search the conversation for the most recent `<CLAIMED_SESSIONS ids="a,b,c">` marker. Each id is a user-confirmed pickup Claude must close. If present, that set is the resolved claimed-session set — skip to step 3.

**Step 2 — Fallback when no CLAIMED_SESSIONS marker exists.**

A malformed or otherwise absent marker can drop `<CLAIMED_SESSIONS>`. When compaction occurred, first invoke `/understand` and `/contextualize` for every spec node still in scope; only then recover in this order:

- **Step 2a — checkpoint claimed-sessions attribute (preferred).** If the most recent `<PICKUP_CHECKPOINT id="..." claimed="a,b,c">` exists, parse its `claimed` attribute. That attribute carries the full claimed-session set as of the latest post-context checkpoint — use it as the authoritative resolved claimed-session set. One surviving checkpoint can recover a multi-claimed-session set without needing every earlier claim marker.
- **Step 2b — additive rebuild (no checkpoint claimed attribute available).** If no `<PICKUP_CHECKPOINT>` carries a `claimed` attribute, collect every `<PICKUP_CLAIM id="...">` and `<PICKUP_CHECKPOINT id="...">` emitted since the last closure marker. Deduplicate by id.
- **Validate the recovered set.**
  - **One id** → proceed.
  - **More than one id** → STOP and ask the user to confirm the full claimed-session set before continuing. NEVER silently collapse to the most recent pickup — that is the exact failure mode the additive rule exists to prevent.
  - **Empty** → check for pickup evidence: `spx session list --status doing` showing sessions this worktree may own, or references in the conversation to a claimed session. If any such evidence exists, STOP and ask the user to confirm the claimed-session set. Only declare the set empty when there is clear evidence no pickup happened in this conversation (fresh handoff).

**Step 3 — Claimed-session set growth rule.**

The claimed-session set grows ONLY by user confirmation. Do NOT auto-scan the todo queue to add sessions. Another context may own work that looks related but is not yours to close.

**Step 4 — Locate mid-session artifact candidates.**

Did this conversation run `spx session handoff` earlier? Collect every handoff id printed by `spx session handoff` during this conversation. When compaction or missing conversation history leaves that set incomplete, resolve the current runtime identity verbatim (`printenv CODEX_THREAD_ID` in Codex; `printenv CLAUDE_SESSION_ID` in Claude Code), read `spx session list --status todo --json`, and add every TODO record whose `agent_session_id` exactly equals that identity. Never use a prefix, timestamp, topic, branch, or path heuristic as a substitute for the exact identity. Cross-reference the resulting ids against the TODO list:

- **Zero artifacts in TODO** → no artifact reconciliation needed; workflow 04 creates a fresh continuation when one is required.
- **One or more artifacts in TODO** → they become supersession candidates. The flat candidate set is never an archive list. Workflow 03 partitions candidates against the resolved continuation-thread records, using each artifact's `goal`, `next_step`, `specs`, and `files`. A fresh continuation archives only the artifacts in its selected partition; Path A archives a partition only when no continuation reader remains for that thread or an existing owner already carries it. If an artifact maps to zero threads or multiple threads, STOP and ask the operator to confirm the mapping before creating or archiving any session. Archive only artifacts this conversation created; never touch artifacts created by other conversations.

**Step 5 — Emit the RESOLVED_CLAIMED_SESSIONS marker.**

After steps 1-4 produce the resolved claimed-session set and artifact candidates, emit a marker into the conversation. The `artifact_ids` attribute carries candidates for workflow 03 to partition; no consumer may archive that flat set directly. If another compaction drops the marker, invoke `/understand` and `/contextualize` for every spec node still in scope, then return to workflows 02-03 to reconstruct and approve the marker and partitions before workflow 04 resumes:

```text
<RESOLVED_CLAIMED_SESSIONS ids="id-1,id-2,..." artifact_ids="id-1,id-2,...">
claimed_sessions: id-1, id-2, ...
mid_session_artifact_candidates: id-1, id-2, ...
</RESOLVED_CLAIMED_SESSIONS>
```

Use `ids=""` for a fresh handoff with no prior pickup. Use `artifact_ids=""` when no mid-session artifact exists. Workflow 03 emits one authoritative partition per independent thread in the continuation plan, including threads with an empty artifact set, and assigns every candidate id to exactly one partition.

</algorithm>

<classification>

After resolving the claimed sessions and locating artifacts, every session observed falls into exactly one class:

- **claimed** — named in the resolved claimed-session set. Will be archived after the canonical continuation is verified.
- **mid-session artifact** — created by this conversation's earlier `spx session handoff` and still in TODO. Workflow 04 creates a fresh canonical continuation when needed and archives superseded artifacts after the fresh session is verified.
- **unrelated** — belongs to another context or another conversation. Leave untouched.
- **ambiguous** — STOP and ask the user before creating a handoff.

The existence of a mid-session artifact is never, by itself, permission to archive a claimed session. Permission flows from completing the closure workflow against the resolved claimed-session set.

</classification>

<consumers>

This algorithm has two callers:

- **Workflow 02 (`<perspective_claimed_sessions>`)** — uses the resolved claimed-session set and classification to drive reflection and to feed the session-disposition header in workflow 03. Does not archive or write anything.
- **Workflow 04 (`<resolve_claimed_sessions>`)** — uses the same resolved claimed-session set and classification to drive archival and canonical-continuation selection (Path A — zero-handoff or existing-owner — or the fresh-session path). Cross-references the user-approved disposition from workflow 03; if the user named additional sessions, adds them before archiving.

Both consumers MUST use this algorithm unchanged. Do not inline copies back into workflow files.

</consumers>
