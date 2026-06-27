---
name: merge
description: >-
  ALWAYS invoke this skill when the user asks to ship, integrate, or merge a changeset into the default branch on origin, or runs /merge.
  NEVER select a merge transport or drive a changeset to the default branch on origin without this skill.
argument-hint: "[instructions describing the change, or empty to use the current changeset]"
allowed-tools: Skill, AskUserQuestion, Bash, Read
---

<objective>
A changeset reaches the default branch on origin through exactly one merge transport.
</objective>

<context>
Live repository state for transport selection, read at invocation.

**Arguments:** `$ARGUMENTS`

**Current branch:**
!`git branch --show-current || echo '(not a git repo)'`

**Working tree (empty = clean):**
!`git status --porcelain || echo '(not a git repo)'`

**Transport overlay (selector, if any):**
!`grep -iE '^transport:' spx/local/merging.md 2>/dev/null || echo '(no explicit transport: selector — default applies)'`

The changeset classification is computed in Step 2 by the classification script, not in this block — base-ref and committed branch-scope derivation route through the canonical `scope-changeset` primitives rather than inline git.

</context>

<transport_selection>
Select exactly one transport, in this precedence order:

1. **Overlay-declared transport.** If `spx/local/merging.md` declares an explicit `transport:` selector, honor it (`manage-github-pr` or `direct-push`). The overlay's declaration wins over the changeset heuristic.
2. **Coordination-note-only changeset -> direct-push.** When every changed path (working tree plus commits ahead of base) is a coordination note — a `PLAN.md` or `ISSUES.md` — route to the direct-push transport. Coordination notes carry no product truth, no spec assertion, and no implementation; the repository commits them directly so collaborators see the coordination state immediately.
3. **GitHub-PR transport (default).** Every other changeset — any spec, decision, implementation, test, doc, or mixed change, and any not-yet-materialized instructed change whose final file set is unknown — routes to the GitHub-PR transport.

The classification is produced by the classification script (Step 2), which derives the base ref and committed branch scope through the canonical `changeset_scope` primitives (`detect_base_ref`, `branch_scope`) and adds the uncommitted working-tree paths — never re-implementing base-ref or diff derivation inline, per the `scope-changeset` skill's contract. It emits counts over the full changed-file set: a changeset is coordination-note-only exactly when the total changed-file count is greater than zero and the non-coordination-note count is zero. The file preview the script prints is bounded for orientation only — classify from the counts, never the preview, since the preview may be truncated and a changeset with any non-note file is never coordination-note-only regardless of size. An empty or not-yet-materialized changeset (total zero) is never coordination-note-only — it defaults to GitHub-PR, where `/manage-github-pr` establishes the change.

The transport binds the gate predicates (which review attests `MERGE_READINESS`, which checks are required, how `REVIEW_READINESS` publishes the changeset) without adding, removing, or reordering a gate or changing the finding-disposition rule, per /merging-standards `<authority_gates>`.
</transport_selection>

<workflow>

**Step 1 — Load foundation and vocabulary.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke `/understand` first. Invoke `/merging-standards` for the shared gate vocabulary, the repo-local overlay topics, and the action tokens. Read `spx/local/merging.md` for the transport selector and per-transport configuration **when that file is present** — it is a conditional read of an optional overlay. Its absence is normal and not a blocker: apply the default lifecycle (default transport precedence, default merge command, autonomous drive). NEVER reconstruct the transport or any merge behavior from incidental repository docs when the overlay is absent, and NEVER edit a generated guide (`CLAUDE.md`, `spx/CLAUDE.md`) to change it — `/merge` and `/merging-standards` govern the lifecycle, and `spx/local/merging.md` is the one place repository-specific merge behavior belongs.

**Step 2 — Select the transport.** Compute the changeset classification by running the classification script, which routes base-ref and committed branch-scope derivation through the canonical `changeset_scope` primitives:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/classify_changeset.py"
```

It prints the total and non-coordination-note counts over the full changed-file set (committed branch scope plus working tree) and a bounded file preview. Apply `<transport_selection>` against those counts and the overlay selector from `<context>`. Name the selected transport and the reason (overlay selector, coordination-note-only, or default).

**Step 3 — Dispatch.**

- **GitHub-PR transport** -> invoke `/manage-github-pr` with `$ARGUMENTS` verbatim. `/manage-github-pr` owns the GitHub-PR lifecycle end to end: its own mode detection, the pre-mutation-confirmation pass (opt-in, off by default), and the commit -> open -> manage -> close protocols. /merge adds nothing to that flow and never reimplements it. State the transport selection in prose before delegating; any pre-mutation confirmation `/manage-github-pr` presents is the single confirmation for this path.
- **Direct-push transport** -> drive the direct-push lifecycle in `<direct_push_lifecycle>`.

**Step 4 — Continue or close.** Reaching merged state ends the transport, not necessarily the session. When in-scope parts of the user's stated goal remain, the transport continues with them rather than closing; it closes through `/handoff` only when the session is genuinely over — the goal is met with no in-scope work remaining, or continuation by Claude is impossible (per `/understand` `references/imperfection-protocol.md` `<closing_protocol>` and the `/handoff` precondition). /merge adds no closure of its own.

</workflow>

<direct_push_lifecycle>
The direct-push transport publishes a verified changeset straight to the default branch on origin with no pull request, under the same three gates as every transport, with the review predicate bound to the local review since no CI review exists, per /merging-standards `<authority_gates>`. The project's `spx/local/merging.md` direct-push block binds the push command and the post-merge step.

**Step D1 — State the plan; confirm only if the overlay opts in.** By default — no pre-mutation-confirmation setting in `spx/local/merging.md` — state the plan in prose (the changeset, that the transport is direct-push to the default branch on origin with no PR, and that the flow runs through the push and post-merge steps) and proceed autonomously; there is no confirmation pause. Only when the overlay opts into a pre-mutation confirmation, present that plan through the runtime's structured-question tool (`AskUserQuestion` on Claude Code, `request_user_input` on Codex) and obtain confirmation before any mutating action — never commit or push before that confirmation.

**Step D2 — Commit.** Invoke `/commit-changes`. Branch hygiene from /merging-standards `<branch_hygiene>` does not apply unchanged here — direct-push publishes to the default branch on origin, so the working changeset is committed on the default-branch-tracking checkout or a short-lived branch per the overlay's direct-push configuration.

**Step D3 — Establish `REVIEW_READINESS`.** Both predicates per /merging-standards `<authority_gates>`:

- *Deterministic verification passes* — run the project's local deterministic verification per /merging-standards `<local_deterministic_scope>` and `spx/local/merging.md`. Fix failures and re-run until green.
- *Local review converged* — run the `changes-reviewer` agent (or `/review-changes` when `changes-reviewer` is absent) per /merging-standards `<local_review_invocation>`: let it resolve its own scope (the worktree it runs in and the diff), with no interpretive scope, severity pre-filter, or emphasis steering. Act on findings by validity and phase per `<review_classification>`; iterate to convergence. This local review is the direct-push transport's `MERGE_READINESS` review predicate — it is the only review the transport has.

**Step D4 — Base-sync, then merge (push to the default branch on origin).** Before publishing, base-sync per /merging-standards `<base_sync>`: fetch `origin/<default>` and, if the changeset is behind it, rebase onto it automatically from observable git state — never asking the operator — then re-establish `REVIEW_READINESS` on the rebased tree before the push, scoped by the `/sync-base` `preservation` proof per `<base_sync>` so an unrelated base movement does not force a full re-run. A rebase conflict that cannot be resolved autonomously stops with `/sync-base`'s structured `conflict` report and active rebase state; a `dirty_tree` outcome is committed through `/commit-changes` then re-synced, never surfaced as a conflict. With `REVIEW_READINESS` held on the tree the push will publish, `MERGE_READINESS` for direct-push holds when the converged local review reports no unresolved valid `BLOCKING` or `DEBT` finding and every required check the overlay defines is terminal-green (a project with no CI on the default branch defines none). `PRODUCTION_READINESS` holds when the change is not production-relevant per the overlay's recognition mechanism, or the operator has approved. Once both hold, publish to the default branch on origin with the overlay's direct-push command (the explicit destination ref form from /merging-standards `<push_semantics>` is preserved). The transport never opens a pull request and never waits on a CI review.

**Step D5 — Post-merge, then continue or close.** Run the overlay's post-merge step (for example a marketplace sync). If in-scope parts of the user's stated goal remain, continue with them — a push to the default branch on origin is not a license to stop. Invoke `/handoff` only when the session is genuinely over — the goal is met with no in-scope work remaining, or continuation by Claude is impossible (per `/understand` `references/imperfection-protocol.md` `<closing_protocol>` and the `/handoff` precondition); the skill then decides session-file creation per continuation state and never receives `--no-session` on the user's behalf.

</direct_push_lifecycle>

<constraints>

- MUST select exactly one transport per `<transport_selection>` and delegate to that transport's skills — never run two transports, never reimplement a transport's internal protocol inline. The GitHub-PR lifecycle is `/manage-github-pr`'s; the direct-push lifecycle invokes `/commit-changes`, `/merging-standards`, and the `changes-reviewer` review.
- MUST keep the three gates and the finding-disposition rule transport-neutral — /merge selects the transport and binds nothing about the gates. A transport binds only the gate predicates, per /merging-standards `<authority_gates>`.
- MUST honor `spx/local/merging.md`: an explicit `transport:` selector wins over the changeset heuristic, and the per-transport configuration (merge command, production-relevance recognition, post-merge step) is the transport's, not /merge's.
- MUST proceed autonomously from the determined changeset by default; present a pre-mutation confirmation through the runtime's structured-question tool and obtain confirmation before any mutating action only when the merge overlay opts into it — for the direct-push path /merge presents it, for the GitHub-PR path `/manage-github-pr` presents it.
- NEVER merge directly outside a transport's authority — the direct-push push executes only under `MERGE_READINESS` ∧ `PRODUCTION_READINESS`, and the GitHub-PR merge executes only through `/manage-pr`'s gates.
- NEVER surface a `dirty_tree` base-sync outcome as a rebase conflict — commit the working changes through `/commit-changes`, then re-run `/sync-base`; never stash.
- MUST drive every transport in the assigned worktree per /merging-standards `<assigned_cwd_worktree_discipline>` — never cross into a sibling worktree, never create a worktree, never stash; a branch-state conflict is resolved by branching in the assigned worktree and continuing.

</constraints>

<failure_modes>

**Mis-selected the transport from a mixed changeset.** Claude read a changeset that touched a `PLAN.md` plus a spec or implementation file as coordination-note-only and routed it to direct-push, bypassing the PR review. Coordination-note-only holds only when *every* changed path is a `PLAN.md` / `ISSUES.md`; one non-note file makes the whole changeset GitHub-PR. Re-read the full changed-file set before classifying — never sample.

**Routed a not-yet-materialized instructed change to direct-push.** Claude classified an instructed change whose files do not exist yet — an empty or unknown changeset — as coordination-note-only, which is wrong. An empty or not-yet-materialized changeset defaults to GitHub-PR, where `/manage-github-pr` establishes the change and re-evaluation happens against the real diff.

**Double confirmation.** Claude presented /merge's own pre-mutation confirmation and then `/manage-github-pr` presented another. For the GitHub-PR path, `/manage-github-pr` owns the single pre-mutation confirmation when the overlay opts into one — /merge states the transport selection in prose and delegates without a structured question. /merge presents a structured confirmation only on the direct-push path it executes itself, and only when the overlay opts in.

</failure_modes>

<success_criteria>

- Exactly one transport was selected per `<transport_selection>`, with the reason named (overlay selector, coordination-note-only, or default).
- A coordination-note-only changeset routed to direct-push; every other changeset routed to GitHub-PR unless the overlay declared a transport.
- The GitHub-PR path delegated to `/manage-github-pr` without reimplementing its lifecycle; the direct-push path drove `<direct_push_lifecycle>` invoking the governing skills.
- By default the flow proceeded autonomously from the determined changeset; where the merge overlay opted into a pre-mutation confirmation, a proposal was presented through the runtime's structured-question tool and confirmed before the first mutation.
- The three gates and the finding-disposition rule stayed transport-neutral; only the predicate bindings differed by transport.
- The changeset reached the default branch on origin through the selected transport's authority, and the session closed through that transport's closure, or the flow stopped at an explicit gate surfaced to the user.

</success_criteria>
