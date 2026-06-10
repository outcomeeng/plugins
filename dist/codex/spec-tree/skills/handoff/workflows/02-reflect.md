<objective>
Work through five perspectives internally before presenting anything to the user. Produces the input for workflows 03 and 04. Do not skip perspectives.

Lean on the imperfection ledger defined in `/understanding` (loaded as a foundation before any spec-tree work). Reflection here classifies ledger items by destination and adds spec-tree-specific concerns the ledger does not cover: path forward, next-context notes, external-infrastructure state, session scope.

</objective>

<perspective_imperfections>
Review remaining imperfections from this session — items observed but not yet resolved. These come from the running imperfection ledger maintained per `/understanding`'s `references/imperfection-protocol.md`. If for any reason the ledger has been pruned (e.g., context compaction), reconstruct by scanning recent turns for: user corrections, methodology gaps, broken references, stale PLAN.md or ISSUES.md, untestable assertions, missing test coverage, library or API gotchas.

Classify each imperfection by nature to determine the persistence target. The destination is governed by the imperfection's nature, not its origin:

| Nature                | Signal                                                       | Destination                                                                         |
| --------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| **Library / API**     | API change, library behavior, version gotcha                 | Language plugin `coding-*` skill references (e.g., `coding-typescript/references/`) |
| **Methodology**       | Skill invocation order, audit interpretation, process error  | Spec-tree plugin skill (amend skill instructions)                                   |
| **Product rule**      | Convention specific to this codebase, forbidden pattern      | Product `CLAUDE.md`                                                                 |
| **Interaction style** | Response format, verbosity, tone — NOT coding patterns       | Memory (`feedback` type)                                                            |
| **Domain knowledge**  | Who's doing what, external system locations, product context | Memory (`product`/`reference` type)                                                 |
| **Spec correction**   | Assertion was wrong or incomplete                            | Amend the spec file directly                                                        |
| **Task-specific**     | Only relevant to this session's work                         | Session file only                                                                   |

**Fix-now rule**: if Claude can fix the imperfection right now (broken link, stale path, wrong filename, simple correction), fix it immediately using Edit/Grep — do not propose it in workflow 03. Note what was fixed for the persisted log.

**Defer rule**: a fix too large for this session becomes a Tier 3 coordination note (PLAN.md or ISSUES.md), proposed in workflow 03 and written in workflow 04.

**Spec correction rule**: a wrong or incomplete assertion is fixed directly in the spec file — Tier 2, governed by the audit gate.

Read existing PLAN.md and ISSUES.md for each anchored node. Check every item against the current specs, decisions, tests, implementation, and user intent — items listed as open may now be fixed; new items may not be listed. A stale coordination note is worse than none. If updates or removals are needed, propose them in workflow 03 — do not edit here.

</perspective_imperfections>

<perspective_path_forward>
Identify what is now understood about how the remaining work should proceed:

- Approach decisions and rejected alternatives
- Concrete remaining steps in order
- Dependencies between steps

For each insight, propose the persistence target (workflow 03 confirms; workflow 04 writes):

- Amend a spec (Tier 2, durable) — when the insight changes what the spec says
- Write or update PLAN.md in the node directory (Tier 3 coordination note) — requires `AskUserQuestion` approval
- Remove PLAN.md (a done plan is a stale plan) — also requires approval
- Session file only — coordination context

</perspective_path_forward>

<perspective_next_context>
Identify exactly where the next Claude context picks up:

- **Critical skills** — always include `/understanding` and `/contextualizing {node}` for each anchored node, plus language-specific skills used
- **Missed skills** — any skill that should have been invoked but was not, and what problems skipping it caused
- **Next skill invocation** — the specific skill the receiving Claude context invokes first, and why
- **Node path** — full path to the resumption node (e.g., `spx/55-example.enabler/21-bar.outcome`)
- **TDD flow position** — which step (1-8) per the `/applying` skill

</perspective_next_context>

<perspective_external_state>
Identify external-infrastructure state the next agent cannot re-derive from the spec tree, PLAN.md/ISSUES.md, or git history: live PR, run, image, or job identifiers and their status; in-flight workflows or deployments; inventory or baseline counts. When such state exists and bears on the next agent's first action, capture it for the session file's `<state_at_handoff>` section so the next pickup skips the re-discovery, and note what one read-only command re-confirms it. When every fact the next agent needs already lives in the repository, this perspective produces nothing and the handoff stays a thin pointer.

Guide the next pickup from the state in prose. Do not pre-compute fixed if-then branches — the next agent decides freely from what it observes.

</perspective_external_state>

<perspective_session_scope>
Resolve which sessions are in this conversation's scope and locate any mid-session handoff artifact to reconcile.

Read `references/scope-resolution.md` and follow every step of the algorithm. After resolving, emit a marker into the conversation so workflow 04 reads scope from context rather than re-running the algorithm:

```text
<RESOLVED_SCOPE ids="id-1,id-2,..." artifact_id="id-or-none">
in_scope: id-1, id-2, ...
mid_session_artifact: id-or-none
</RESOLVED_SCOPE>
```

Use `ids=""` (empty) for a fresh handoff with no prior pickup. Use `artifact_id="none"` when no mid-session artifact exists.

For each in-scope session, fold every still-relevant fact into durable targets first (spec tree, skills, CLAUDE.md, memory), then into the canonical continuation's coordination section only when no higher tier fits. Mid-session artifacts are reconciled in workflow 04 by rewrite-in-place or archival.

A handoff replaces incorporated context. The existence of any session is not, by itself, permission to archive an in-scope session — permission flows from completing this workflow.

</perspective_session_scope>

<success_criteria>

- All five perspectives completed internally before proceeding to workflow 03.
- `<RESOLVED_SCOPE>` marker emitted into the conversation.
- Stale PLAN.md or ISSUES.md items identified for proposal in workflow 03 (or fixed inline if safe).

</success_criteria>
