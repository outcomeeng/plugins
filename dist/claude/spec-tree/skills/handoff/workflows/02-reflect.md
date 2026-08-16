<objective>
A complete closure reflection record containing classified imperfections, path-forward persistence targets, next-context notes, external-state notes, claimed-session resolution, and thread-scoped ownership and continuation states.
</objective>

<context>

Lean on the imperfection ledger defined in `/understand` (loaded as a foundation before any spec-tree work). Reflection here classifies ledger items by destination and adds spec-tree-specific concerns the ledger does not cover: path forward, next-context notes, external-infrastructure state, claimed-session set.

</context>

<required_reading>

- `${CLAUDE_SKILL_DIR}/references/claimed-session-resolution.md` before resolving claimed sessions.

</required_reading>

<process>

<perspective_imperfections>
Review remaining imperfections from this session — items observed but not yet resolved. These come from the running imperfection ledger maintained by live `/understand` `<imperfection_protocol>`. When context compaction pruned the ledger, STOP and reconstruct it from recent turns and any coordination notes the reflection reads, invoking `/understand`, then `/contextualize` on the governing node, immediately before it reads or edits those notes or other governed product content. Scan for user corrections, methodology gaps, broken references, stale PLAN.md or ISSUES.md, untestable assertions, missing test coverage, and library or API gotchas.

Classify each imperfection by nature to determine the persistence target. The destination is governed by the imperfection's nature, not its origin:

| Nature                | Signal                                                       | Destination                                                                     |
| --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| **Library / API**     | API change, library behavior, version gotcha                 | Language plugin `code-*` skill references (e.g., `code-typescript/references/`) |
| **Methodology**       | Skill invocation order, audit interpretation, process error  | Spec-tree plugin skill (amend skill instructions)                               |
| **Product rule**      | Convention specific to this codebase, forbidden pattern      | Product `CLAUDE.md`                                                             |
| **Interaction style** | Response format, verbosity, tone — NOT coding patterns       | Memory (`feedback` type)                                                        |
| **Domain knowledge**  | Who's doing what, external system locations, product context | Memory (`product`/`reference` type)                                             |
| **Spec correction**   | Assertion was wrong or incomplete                            | Amend the spec file directly                                                    |
| **Task-specific**     | Only relevant to this session's work                         | Session file only                                                               |

**Fix-now rule**: if Claude can fix the imperfection right now (broken link, stale path, wrong filename, simple correction), inspect and edit the affected files immediately — do not propose it in workflow 03. Note what was fixed for the persisted log.

**Defer rule**: a fix too large for this session becomes a Tier 3 coordination note (PLAN.md or ISSUES.md), proposed in workflow 03 and written in workflow 04, only when the session already has a real stop condition: the user halted the work, context is exhausted, or an external blocker prevents the next action. If Claude can still act, do not defer; continue the work instead of closing.

**Spec correction rule**: a wrong or incomplete assertion is fixed directly in the spec file — Tier 2, governed by the audit gate.

Read existing PLAN.md and ISSUES.md for each anchored node. Check every item against the current specs, decisions, tests, implementation, and user intent — items listed as open may now be fixed; new items may not be listed. A stale coordination note is worse than none. If updates or removals are safe local fixes, record them as fix-now items for workflow 04 and do not create a session file. If an item is actionable and Claude can still do the work, closure is blocked: stop this workflow and return to the governing implementation workflow. If a clearly wrong coordination note outside the original scope is observed, record it in the imperfection ledger and classify it the same way: fix safe local corrections now; ask the operator at the next checkpoint when ownership, scope, cost, or risk changes; never treat it as session-file-only context.

</perspective_imperfections>

<perspective_path_forward>
Identify what is now understood about how the remaining work should proceed:

- Approach decisions and rejected alternatives
- Concrete remaining steps in order
- Dependencies between steps

For each insight, propose the persistence target (workflow 03 confirms; workflow 04 writes):

- Amend a spec (Tier 2, durable) — when the insight changes what the spec says
- Write or update PLAN.md in the node directory (Tier 3 coordination note) — requires `AskUserQuestion` approval and a real stop condition
- Remove PLAN.md (a done plan is a stale plan) — also requires approval
- Session file only — coordination context

</perspective_path_forward>

<perspective_next_context>
Identify exactly where the next Claude context picks up:

- **First action** — the concrete command, inspection, or workflow step the receiving Claude context starts from after `/pickup` completes
- **Node path** — full path to the resumption node (e.g., `spx/55-example.enabler/21-bar.outcome`)
- **TDD flow position** — when applicable, which step (1-8) per the `/apply` skill

</perspective_next_context>

<perspective_external_state>
Identify external-infrastructure state the next session cannot re-derive from the spec tree, PLAN.md/ISSUES.md, or git history: live PR, run, image, or job identifiers and their status; in-flight workflows or deployments; inventory or baseline counts. When such state exists and bears on the next session's first action, capture it for the session file's `<state_at_handoff>` section so the next pickup skips the re-discovery, and note what one read-only command re-confirms it. When every fact the next session needs already lives in the repository, this perspective produces nothing and the handoff stays a thin pointer.

Guide the next pickup from the state in prose. Do not pre-compute fixed if-then branches — the next session decides freely from what it observes.

</perspective_external_state>

<perspective_claimed_sessions>
Resolve which sessions are in this conversation's claimed sessions and locate any mid-session handoff artifact to reconcile.

Read `${CLAUDE_SKILL_DIR}/references/claimed-session-resolution.md` and follow every step of the algorithm. After resolving, emit a marker into the conversation so workflow 04 reads the claimed sessions from context rather than re-running the algorithm:

```text
<RESOLVED_CLAIMED_SESSIONS ids="id-1,id-2,..." artifact_ids="id-1,id-2,...">
claimed_sessions: id-1, id-2, ...
mid_session_artifact_candidates: id-1, id-2, ...
</RESOLVED_CLAIMED_SESSIONS>
```

Use `ids=""` (empty) for a fresh handoff with no prior pickup. Use `artifact_ids=""` when no mid-session artifact exists. The artifact ids are candidates only; workflow 03 partitions them against the resolved continuation-thread records.

For each claimed session, fold every still-relevant fact into durable targets first (spec tree, skills, CLAUDE.md, memory), then into the canonical continuation's coordination section only when no higher tier fits. Mid-session artifacts are reconciled in workflow 04 by creating a fresh continuation when one is needed, then archiving superseded same-conversation artifacts after the fresh session is verified.

A handoff replaces incorporated context. The existence of any session is not, by itself, permission to archive a claimed session — permission flows from completing this workflow.

</perspective_claimed_sessions>

<perspective_existing_sessions>
Before proposing or creating any continuation session, inspect the existing session queue:

```bash
spx session list --status todo --json
spx session list --status doing --json
```

Group the anchored work and same-conversation artifact candidates into independent closure threads. Compare every `todo` and `doing` session against each thread's node paths and topic terms:

- Node overlap: any `specs` or `files` path under the same anchored node, or a `goal` / `next_step` naming the same full node path.
- Topic overlap: meaningful terms from the unresolved note, blocker, or external state appear in the existing session's `goal` or `next_step`.
- Ownership: whether the overlapping session is in this conversation's claimed-session set, a mid-session artifact created by this conversation, or another context's session.

Classify overlaps:

- **same-owner-continuation** — this conversation created the TODO artifact or claimed the doing session; workflow 04 may create a fresh continuation and archive superseded same-conversation artifacts according to the claimed-session rules.
- **existing-owner** — another `todo` or `doing` session already owns the continuation; do not create another session. Reconcile any facts into durable artifacts if needed, then leave the existing session untouched and close only if no other blocker remains.
- **unrelated** — no overlapping node and topic.
- **ambiguous** — overlap exists but ownership or topic match is unclear; STOP and ask the operator before any continuation session is proposed.

Record one ownership classification per independent closure thread for the thread marker emitted after continuation-state derivation. `none` permits a fresh session only when continuation by Claude is impossible now; `existing-owner` blocks a fresh session for that thread because another queue entry carries it.

</perspective_existing_sessions>

<continuation_signal>
Compute the continuation state workflow 04 reads for every independent closure thread — the check that makes `<HANDOFF_OPTIONS no_session="true" ... />` answerable to each thread's state rather than an unconditional global skip.

**The signal ranges over the nodes in scope this session (the anchored nodes from workflow 01), independently of `CLAIMED_SESSIONS`.** The claimed-session set decides only what gets archived; it never decides whether to hand off. An empty claimed-session set (no `/pickup` this conversation) therefore NEVER implies an absent signal.

A thread's state is `present` when any of these holds for one of its anchored nodes:

- a node-local `PLAN.md` exists and its item is not already satisfied;
- a node-local `ISSUES.md` carries an unresolved entry;
- an `spx/EXCLUDE` entry names an anchored node (specified but unimplemented);
- a spec assertion touched this session is declared but not yet satisfied (no passing `[test]`/`[eval]`, or an unmet `[audit]`);
- the path-forward perspective named concrete remaining steps.

A `present` state blocks that thread's closure while Claude can still act. It permits a session file only when continuation by Claude is impossible now: the user halted the work, context is exhausted, or an external blocker prevents the next action. There is no "deferred notes but no session" state: if a note carries no future work, it is removed during closure, not kept while the session file is skipped. Small imperfections are fixed in-session, not deferred into a note.

Emit one record for every independent thread represented by anchored work or same-conversation artifact candidates:

```text
<RESOLVED_CONTINUATION_THREADS>
<thread thread_id="thread-1" owner_status="none|same-owner-continuation|existing-owner|ambiguous" continuation="present|absent">
owner: [what the queue search found]
continuation: [the unresolved work, or "no continuation remains"]
</thread>
</RESOLVED_CONTINUATION_THREADS>
```

Every independent thread appears exactly once. An `existing-owner` record carries `continuation="present"`; an `ambiguous` owner status stops before disposition. `<HANDOFF_OPTIONS no_session="true" ... />` is valid per record only when `continuation="absent"` or `owner_status="existing-owner"` with no local blocker. Workflow 04 surfaces a contradiction for each record with `continuation="present"` and no existing owner rather than silently omitting its session file.

</continuation_signal>

</process>

<success_criteria>

- The imperfections, path-forward, next-context, external-state, claimed-sessions, and existing-sessions perspectives are complete before proceeding to workflow 03.
- `<RESOLVED_CONTINUATION_THREADS>` is derived after those six perspectives rather than counted as another perspective.
- `<RESOLVED_CLAIMED_SESSIONS>` marker emitted into the conversation.
- `<RESOLVED_CONTINUATION_THREADS>` contains exactly one ownership and continuation-state record per independent closure thread before any continuation proposal.
- Stale PLAN.md or ISSUES.md items identified as fix-now work, closure blockers, or operator decisions; no actionable coordination note is converted into a session-only continuation while Claude can still act.

</success_criteria>
