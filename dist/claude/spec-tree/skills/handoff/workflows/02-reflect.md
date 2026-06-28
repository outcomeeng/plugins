<objective>
A complete closure reflection record containing classified imperfections, path-forward persistence targets, next-context notes, external-state notes, claimed-session resolution, existing-session reconciliation, and continuation signal.
</objective>

Lean on the imperfection ledger defined in `/understand` (loaded as a foundation before any spec-tree work). Reflection here classifies ledger items by destination and adds spec-tree-specific concerns the ledger does not cover: path forward, next-context notes, external-infrastructure state, claimed-session set.

<required_reading>

- `references/claimed-session-resolution.md` before resolving claimed sessions.

</required_reading>

<perspective_imperfections>
Review remaining imperfections from this session — items observed but not yet resolved. These come from the running imperfection ledger maintained per `/understand`'s `references/imperfection-protocol.md`. If for any reason the ledger has been pruned (e.g., context compaction), reconstruct by scanning recent turns for: user corrections, methodology gaps, broken references, stale PLAN.md or ISSUES.md, untestable assertions, missing test coverage, library or API gotchas.

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

**Fix-now rule**: if Claude can fix the imperfection right now (broken link, stale path, wrong filename, simple correction), fix it immediately using Edit/Grep — do not propose it in workflow 03. Note what was fixed for the persisted log.

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

- **Critical skills** — always include `/understand` and `/contextualize {node}` for each anchored node, plus language-specific skills used
- **Missed skills** — any skill that should have been invoked but was not, and what problems skipping it caused
- **Next skill invocation** — the specific skill the receiving Claude context invokes first, and why
- **Node path** — full path to the resumption node (e.g., `spx/55-example.enabler/21-bar.outcome`)
- **TDD flow position** — which step (1-8) per the `/apply` skill

</perspective_next_context>

<perspective_external_state>
Identify external-infrastructure state the next session cannot re-derive from the spec tree, PLAN.md/ISSUES.md, or git history: live PR, run, image, or job identifiers and their status; in-flight workflows or deployments; inventory or baseline counts. When such state exists and bears on the next session's first action, capture it for the session file's `<state_at_handoff>` section so the next pickup skips the re-discovery, and note what one read-only command re-confirms it. When every fact the next session needs already lives in the repository, this perspective produces nothing and the handoff stays a thin pointer.

Guide the next pickup from the state in prose. Do not pre-compute fixed if-then branches — the next session decides freely from what it observes.

</perspective_external_state>

<perspective_claimed_sessions>
Resolve which sessions are in this conversation's claimed sessions and locate any mid-session handoff artifact to reconcile.

Read `references/claimed-session-resolution.md` and follow every step of the algorithm. After resolving, emit a marker into the conversation so workflow 04 reads the claimed sessions from context rather than re-running the algorithm:

```text
<RESOLVED_CLAIMED_SESSIONS ids="id-1,id-2,..." artifact_id="id-or-none">
claimed_sessions: id-1, id-2, ...
mid_session_artifact: id-or-none
</RESOLVED_CLAIMED_SESSIONS>
```

Use `ids=""` (empty) for a fresh handoff with no prior pickup. Use `artifact_id="none"` when no mid-session artifact exists.

For each claimed session, fold every still-relevant fact into durable targets first (spec tree, skills, CLAUDE.md, memory), then into the canonical continuation's coordination section only when no higher tier fits. Mid-session artifacts are reconciled in workflow 04 by rewrite-in-place or archival.

A handoff replaces incorporated context. The existence of any session is not, by itself, permission to archive a claimed session — permission flows from completing this workflow.

</perspective_claimed_sessions>

<perspective_existing_sessions>
Before proposing or creating any continuation session, inspect the existing session queue:

```bash
spx session list --status todo --json
spx session list --status doing --json
```

Compare every `todo` and `doing` session against this closure's anchored nodes and topic terms:

- Node overlap: any `specs` or `files` path under the same anchored node, or a `goal` / `next_step` naming the same full node path.
- Topic overlap: meaningful terms from the unresolved note, blocker, or external state appear in the existing session's `goal` or `next_step`.
- Ownership: whether the overlapping session is in this conversation's claimed-session set, a mid-session artifact created by this conversation, or another context's session.

Classify overlaps:

- **same-owner-continuation** — this conversation created the TODO artifact or claimed the doing session; workflow 04 may rewrite or archive it according to the claimed-session rules.
- **existing-owner** — another `todo` or `doing` session already owns the continuation; do not create another session. Reconcile any facts into durable artifacts if needed, then leave the existing session untouched and close only if no other blocker remains.
- **unrelated** — no overlapping node and topic.
- **ambiguous** — overlap exists but ownership or topic match is unclear; STOP and ask the operator before any continuation session is proposed.

Emit a marker:

```text
<EXISTING_SESSION_RECONCILIATION status="none|same-owner-continuation|existing-owner|ambiguous">
summary: [what the queue search found]
</EXISTING_SESSION_RECONCILIATION>
```

`status="none"` is the only state that permits a new Path C session, and only when continuation by Claude is impossible now. `status="existing-owner"` blocks Path C because adding a session would duplicate queue state.

</perspective_existing_sessions>

<continuation_signal>
Compute the continuation signal workflow 04 reads to decide whether closure is allowed and whether a session reader is needed — the check that makes `--no-session` answerable to state rather than an unconditional skip.

**The signal ranges over the nodes in scope this session (the anchored nodes from workflow 01), independently of `CLAIMED_SESSIONS`.** The claimed-session set decides only what gets archived; it never decides whether to hand off. An empty claimed-session set (no `/pickup` this conversation) therefore NEVER implies an absent signal.

The signal is `present` when any of these holds for a node anchored this session:

- a node-local `PLAN.md` exists and its item is not already satisfied;
- a node-local `ISSUES.md` carries an unresolved entry;
- an `spx/EXCLUDE` entry names an anchored node (specified but unimplemented);
- a spec assertion touched this session is declared but not yet satisfied (no passing `[test]`/`[eval]`, or an unmet `[audit]`);
- the path-forward perspective named concrete remaining steps.

A `present` signal blocks closure while Claude can still act. It permits a session file only when continuation by Claude is impossible now: the user halted the work, context is exhausted, or an external blocker prevents the next action. There is no "deferred notes but no session" state: if a note carries no future work, it is removed during closure, not kept while the session file is skipped. Small imperfections are fixed in-session, not deferred into a note.

Emit the signal so workflow 04 reads it from context:

```text
<CONTINUATION_SIGNAL state="present|absent">
<one line: the unresolved work, or "no continuation remains">
</CONTINUATION_SIGNAL>
```

`--no-session` asserts either `state="absent"` or `status="existing-owner"` with no local blocker. It never authorizes skipping the session file when the signal is `present` and no existing owner exists. Workflow 04's `<write_canonical_continuation>` Path A acts on this: a `--no-session` invocation that meets a `present` signal without an existing owner surfaces the contradiction rather than silently omitting the session file.

</continuation_signal>

<success_criteria>

- All six perspectives completed internally before proceeding to workflow 03.
- `<RESOLVED_CLAIMED_SESSIONS>` marker emitted into the conversation.
- `<EXISTING_SESSION_RECONCILIATION>` marker emitted into the conversation before any continuation proposal.
- `<CONTINUATION_SIGNAL>` marker emitted into the conversation.
- Stale PLAN.md or ISSUES.md items identified as fix-now work, closure blockers, or operator decisions; no actionable coordination note is converted into a session-only continuation while Claude can still act.

</success_criteria>
