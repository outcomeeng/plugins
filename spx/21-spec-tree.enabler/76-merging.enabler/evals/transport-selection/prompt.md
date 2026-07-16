<!-- Generated from the ordered complete merge producers. -->

Apply the complete merge producers below to the supplied changeset classification and overlay state. Return exactly one JSON object with these mandatory fields:

- `selected_transport`: `GITHUB_PR` or `DIRECT_PUSH`
- `selection_reason`: `overlay-selector`, `coordination-note-only`, or `default`
- `delegation_target`: `manage-github-pr` or `direct-push-lifecycle`
- `pre_mutation_action`: `PRESENT_CONFIRMATION` or `PROCEED_AUTONOMOUSLY`

===== BEGIN PRODUCER: src/plugins/spec-tree/skills/merge/SKILL.md =====
---
name: merge
description: >-
  ALWAYS invoke this skill when the user asks to ship, integrate, or merge a changeset into the default branch on origin, or runs /merge.
  NEVER select a merge transport or drive a changeset to the default branch on origin without this skill.
argument-hint: "[instructions describing the change, or empty to use the current changeset]"
allowed-tools: Skill, Agent, {{! tool('ask_user') !}}, Read, Bash(git branch:*), Bash(git status:*), Bash(git symbolic-ref:*), Bash(git rev-parse:*), Bash(git diff:*), Bash(git push:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/classify_changeset.py":*), Bash(echo:*), Bash(spx diagnose:*), Bash(spx validation markdown:*), Bash(spx spec status:*)
---

<objective>
A changeset reaches the default branch on origin through exactly one merge transport.
</objective>

<context>
Live repository state for transport selection, read at invocation.

**Arguments:** `$ARGUMENTS`

**Current branch:**
!`git branch --show-current || echo '(not a git repo)'`

Working-tree paths and changeset classification are computed in Step 2 by the bounded classification script, not in this block — base-ref and committed branch-scope derivation route through the canonical `scope-changeset` primitives rather than inline git.

</context>

<transport_selection>
Select exactly one transport, in this precedence order:

1. **Overlay-declared transport.** If `spx/local/merging.md` declares an explicit `transport:` selector, honor it (`manage-github-pr` or `direct-push`). The overlay's declaration wins over the changeset heuristic.
2. **Coordination-note-only changeset -> direct-push.** When every changed path (working tree plus commits ahead of base) is a coordination note — a `PLAN.md` or `ISSUES.md` — route to the direct-push transport. Coordination notes carry no product truth, no spec assertion, and no implementation; the repository commits them directly so collaborators see the coordination state immediately.
3. **GitHub-PR transport (default).** Every other changeset — any spec, decision, implementation, test, doc, or mixed change, and any not-yet-materialized instructed change whose final file set is unknown — routes to the GitHub-PR transport.

The classification is produced by the classification script (Step 2), which derives the base ref and committed branch scope through the canonical `changeset_scope` primitives (`detect_base_ref`, `branch_scope`) and adds the uncommitted working-tree paths — never re-implementing base-ref or diff derivation inline, per the `scope-changeset` skill's contract. It emits counts over the full changed-file set: a changeset is coordination-note-only exactly when the total changed-file count is greater than zero and the non-coordination-note count is zero. The file preview the script prints is bounded for orientation only — classify from the counts, never the preview, since the preview may be truncated and a changeset with any non-note file is never coordination-note-only regardless of size. An empty or not-yet-materialized changeset (total zero) is never coordination-note-only — it defaults to GitHub-PR, where `/manage-github-pr` establishes the change.

The transport binds the gate predicates (which verification establishes `VERIFICATION_READINESS`, which review attests `MERGE_READINESS`, which checks are required, and which deploy or release actions exist) without adding, removing, reordering, or renaming a gate or changing the finding-disposition rule, per /merging-standards `<authority_gates>`.
</transport_selection>

<workflow>

**Step 1 — Load foundation and vocabulary.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke `/understand` first. Invoke `/merging-standards` for the shared gate vocabulary, the repo-local overlay topics, and the action tokens. Read `spx/local/merging.md` for the transport selector and per-transport configuration **when that file is present** — it is a conditional read of an optional overlay. Its absence is normal and not a blocker: apply the default lifecycle (default transport precedence, default merge command, autonomous drive). NEVER reconstruct the transport or any merge behavior from incidental repository docs when the overlay is absent, and NEVER edit a generated guide (`{{! file('root_guide') !}}`) to change it — `/merge` and `/merging-standards` govern the lifecycle, and `spx/local/merging.md` is the one place repository-specific merge behavior belongs.

A task the user explicitly limited to local-only work completes at that local boundary and does not dispatch a merge transport. Classify that boundary as `STOP_LOCAL_SCOPE`; it is distinct from `NO_MERGE_NEEDED`, which applies only when no merge work exists. For default-branch-scoped work, a changeset with commits ahead of its resolved base remains unfinished throughout classification and dispatch. An overlay-required pre-mutation confirmation pauses the next mutation and requires operator input, but it never turns local readiness into completion or becomes a lifecycle gate.

**Step 2 — Select the transport.** Compute the changeset classification by running the classification script, which routes base-ref and committed branch-scope derivation through the canonical `changeset_scope` primitives:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/classify_changeset.py"
```

It prints the total and non-coordination-note counts over the full changed-file set (committed branch scope plus working tree) and a bounded file preview. Apply `<transport_selection>` against those counts and the overlay selector read in Step 1. Name the selected transport and the policy reason: overlay selector, coordination-note-only, or default GitHub PR. Do not expose raw file counts unless the count is itself the decision boundary the operator needs to inspect.

**Step 3 — Dispatch.**

- **GitHub-PR transport** -> invoke `/manage-github-pr` with `$ARGUMENTS` verbatim. `/manage-github-pr` owns the GitHub-PR lifecycle end to end: its own mode detection, the pre-mutation-confirmation pass (opt-in, off by default), and the commit -> open -> manage -> close protocols. /merge adds nothing to that flow and never reimplements it. Before delegating, state the selected transport, the policy reason, and that `/manage-github-pr` owns the next mutation and closeout. Any pre-mutation confirmation `/manage-github-pr` presents is the single confirmation for this path.
- **Direct-push transport** -> drive the direct-push lifecycle in `<direct_push_lifecycle>`.

**Step 4 — Continue or close.** Reaching merged state ends the transport, not necessarily the session. When in-scope parts of the user's stated goal remain, the transport continues with them rather than closing; it closes through `/handoff` only when the session is complete — the goal is met with no in-scope work remaining, or continuation by Claude is impossible (per `/understand` `references/imperfection-protocol.md` `<closing_protocol>` and the `/handoff` precondition). Do not emit an independent merge receipt after the transport returns. The final operator-facing closeout comes from `/handoff` or from continuing the remaining governed work.

</workflow>

<direct_push_lifecycle>
The direct-push transport publishes a verified changeset straight to the default branch on origin with no pull request, under the same four gates as every transport, with the review predicate bound to the local review since no CI review exists, per /merging-standards `<authority_gates>`. The project's `spx/local/merging.md` direct-push block binds the push command and any declared deploy or release action.

**Step D1 — State the plan; confirm only if the overlay opts in.** By default — no pre-mutation-confirmation setting in `spx/local/merging.md` — state the plan in prose and proceed autonomously; there is no confirmation pause. The plan names the changeset, the selected direct-push transport, the destination ref on origin, the commit, push, deploy, and release actions, why the overlay allows proceeding without confirmation, and the verification and review gates that must hold before the push. Only when the overlay opts into a pre-mutation confirmation, present that plan through the runtime's structured-question tool (`{{! tool('ask_user', 'claude') !}}` on Claude Code, `{{! tool('ask_user', 'codex') !}}` on Codex) and obtain confirmation before any mutating action — never commit or push before that confirmation.

After the plan or required confirmation, run every overlay-declared preflight check per /merging-standards `<overlay_safety_checks>` immediately before Step D2's commit or branch mutation. A failed check stops before the direct-push lifecycle changes the checkout.

**Step D2 — Commit.** Invoke `/commit-changes`. Branch hygiene from /merging-standards `<branch_hygiene>` does not apply unchanged here — direct-push publishes to the default branch on origin, so the working changeset is committed on the default-branch-tracking checkout or a short-lived branch per the overlay's direct-push configuration.

**Step D3 — Establish `VERIFICATION_READINESS`.** All predicates per /merging-standards `<authority_gates>`:

- *Deterministic verification passes* — run the project's local deterministic verification per /merging-standards `<local_deterministic_scope>` and `spx/local/merging.md`. Fix failures and re-run until green.
- *Evidence-auditor predicates pass* — dispatch `test-evidence-auditor` for changed `[test]` assertions, linked tests, or imported test-infrastructure artifacts, and `eval-evidence-auditor` for changed `[eval]` assertions, eval artifacts, or producer artifacts for eval-backed assertions. Handle rejected, failing, or unknown verdicts per /merging-standards `<auditor_verdicts>`, then re-run deterministic verification and the relevant auditor until the evidence predicate is clean.
- *Local review converged* — after deterministic verification and applicable evidence audits pass, create a checkpoint commit through /commit-changes and confirm the worktree is clean. Run the `changes-reviewer` agent per /merging-standards `<local_review_invocation>` on raw scope `HEAD`, with no interpretive scope, severity pre-filter, or emphasis steering. Act on its findings by validity and explicit resolution evidence per `<review_classification>`; rerun affected gates, checkpoint, and review each new clean committed head to convergence. This local review is the direct-push transport's `MERGE_READINESS` review predicate — it is the only review the transport has.

**Step D4 — Base-sync, then merge (push to the default branch on origin).** Before publishing, base-sync per /merging-standards `<base_sync>`: fetch `origin/<default>` and, if the changeset is behind it, rebase onto it automatically from observable git state — never asking the operator — then re-establish `VERIFICATION_READINESS` on the rebased tree before the push, scoped by the `/sync-base` `preservation` proof per `<base_sync>` so an unrelated base movement does not force a full re-run. A rebase conflict that cannot be resolved autonomously stops with `/sync-base`'s structured `conflict` report and active rebase state; a `dirty_tree` outcome is committed through `/commit-changes` then re-synced, never surfaced as a conflict. With `VERIFICATION_READINESS` held on the tree the push will publish, `MERGE_READINESS` for direct-push holds when the converged local review reports no unresolved valid `BLOCKING` or `DEBT` finding and every required check the overlay defines is terminal-green (a project with no CI on the default branch defines none). Once it holds, run every overlay-declared preflight check per /merging-standards `<overlay_safety_checks>` immediately before publishing to the default branch on origin with the overlay's direct-push command (the explicit destination ref form from /merging-standards `<push_semantics>` is preserved). The transport never opens a pull request and never waits on a CI review.

**Step D5 — Deploy, release, then continue or close.** Evaluate each declared phase's readiness before running its action. An unsatisfied `DEPLOYMENT_READINESS` gate stops at that gate, requires operator input, and runs no deploy, release, or close action. An unsatisfied `RELEASE_READINESS` gate after deploy completion or a deploy no-op stops at that gate, requires operator input, and runs no release or close action. Otherwise run every declared deploy and release action in order. Preserve direct-push merge facts for closeout: default branch, pushed full HEAD SHA, deploy and release results, and release-source worktree state when the declared release or marketplace refresh used one. If in-scope parts of the user's stated goal remain, continue with them — a push to the default branch on origin is not a license to stop. Invoke `/handoff` plain only when the session is complete — the goal is met with no in-scope work remaining, or continuation by Claude is impossible (per `/understand` `references/imperfection-protocol.md` `<closing_protocol>` and the `/handoff` precondition); `/handoff` computes the branch-state closeout record from /merging-standards `<branch_state_closeout>`, runs its safe cleanup policy using its own closeout tool surface, decides session-file creation per continuation state, includes **Remaining Branches**, and never receives `--no-session` on the user's behalf. Do not emit an independent merge receipt, push receipt, or sync receipt in place of that operator-useful closeout.

</direct_push_lifecycle>

<constraints>

- MUST select exactly one transport per `<transport_selection>` and delegate to that transport's skills — never run two transports, never reimplement a transport's internal protocol inline. The GitHub-PR lifecycle is `/manage-github-pr`'s; the direct-push lifecycle invokes `/commit-changes`, `/merging-standards`, and the `changes-reviewer` review.
- MUST keep the four gates and the finding-disposition rule transport-neutral — /merge selects the transport and binds nothing about the gates. A transport binds only the gate predicates, per /merging-standards `<authority_gates>`.
- MUST honor `spx/local/merging.md`: an explicit `transport:` selector wins over the changeset heuristic, and the per-transport configuration (merge command, deployment declarations, and release declarations) is the transport's, not /merge's.
- MUST proceed autonomously from the determined changeset by default; present a pre-mutation confirmation through the runtime's structured-question tool and obtain confirmation before any mutating action only when the merge overlay opts into it — for the direct-push path /merge presents it, for the GitHub-PR path `/manage-github-pr` presents it.
- NEVER merge directly outside a transport's authority — the direct-push push executes only under `MERGE_READINESS`, and the GitHub-PR merge executes only through `/manage-pr`'s gates.
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
- The four gates and the finding-disposition rule stayed transport-neutral; only the predicate bindings differed by transport.
- The changeset reached the default branch on origin through the selected transport's authority, then continued any remaining in-scope work or closed through `/handoff` plain; the flow stopped only at an explicit gate surfaced to the user.

</success_criteria>
===== END PRODUCER: src/plugins/spec-tree/skills/merge/SKILL.md =====

===== BEGIN PRODUCER: src/plugins/spec-tree/skills/merging-standards/SKILL.md =====
---
name: merging-standards
user-invocable: false
description: >-
  Shared vocabulary for the merge lifecycle — pre-flight predicates, branch topology gate, push command, authority gates, review classification, integration review surfaces, action tokens, delivered-value boundary, closeout, and repo-local overlay topics.
  Loaded by /merge, /manage-github-pr, /open-pr, and /manage-pr.
allowed-tools: Read
---

<objective>
The shared merge-lifecycle vocabulary — the concepts, predicates, gates, commands, and tokens that `/merge`, `/manage-github-pr`, `/open-pr`, and `/manage-pr` all read.
</objective>

<repo_local_overlay>
When loaded inside a repository, check for `spx/local/merging.md` at the repository root. Read it after this reference if present and apply it as the repo-local specialization; a local overlay supplements skill behavior and does not declare product truth.

`spx/local/merging.md` is a **conditional read** and an **optional file**: read it only when it exists, and treat its absence as normal — never a missing-state error or a blocker. When it is absent, the defaults in this reference apply and the lifecycle proceeds unchanged. It is the one place repository-specific merge behavior (transport, readiness, confirmation, merge command, preview actions, deployment actions, and release actions) belongs. When the overlay is absent, NEVER reconstruct the transport or any merge behavior from incidental repository docs — invoke `/merge` and let the lifecycle apply the defaults — and NEVER edit a generated guide (`{{! file('root_guide') !}}`) to change merge behavior; the authored skills and this overlay are the only surfaces that govern it.

Topics the overlay MAY refine:

- **Safety checks** — preflight checks that run immediately before a lifecycle entry's first checkout-sensitive mutation, and post-cleanup checks that run immediately after detach-based cleanup. See `<overlay_safety_checks>`.
- The project's local deterministic-verification scope for `VERIFICATION_READINESS`: validation and testing commands for the touched scope by default, plus any documented escalation cases that require a wider local run. Full-repository validation and testing are CI's responsibility unless the overlay explicitly requires a local full-repository predicate for a class of change.
- The terminal full deterministic gate: when the overlay requires a local full-repository bundle, its command runs only after all applicable evidence auditors and agentic reviews have converged on the same clean committed head. The full gate runs once at that terminal point, never before agentic verification, inside an agent, or concurrently with another heavy command. Any later change invalidates it and reopens the affected agentic gates before the full gate runs again.
- Push command overrides — the explicit destination ref form must be preserved.
- **Preview declarations** — pre-merge publication, generated preview, dry-run, or inspection actions and their predicates after `VERIFICATION_READINESS` publication and before `MERGE_READINESS`. Absence means `PREVIEW` is a no-op and never blocks merge, deploy, release, or close.
- **Deployment and release declarations** — environment mutation actions and predicates under `DEPLOYMENT_READINESS`, plus consumer-visible publication or refresh actions and predicates under `RELEASE_READINESS`. Absence means `DEPLOY` and `RELEASE` are no-op phases and never block later phases.
- **Pre-mutation confirmation** — whether Claude pauses for operator confirmation before the first mutating action of the lifecycle (branch, commit, push, PR open, direct-push). A project whose operators want to confirm intent before any mutation opts in here; Claude then presents — through the runtime's structured-question tool — the change to make, the branch, the commit shape, and the end-to-end scope from intent through merge, and waits before mutating. A project that wants none declares no setting, and Claude drives the determined changeset from intent to merge autonomously, stating the plan in prose with no structured-question pause. This is an opt-in touch-point ahead of the lifecycle, never a gate; it leaves `VERIFICATION_READINESS`, `MERGE_READINESS`, `DEPLOYMENT_READINESS`, `RELEASE_READINESS`, and the finding-disposition rule unchanged. Establishing *what* to ship when no changeset is determined (the `/manage-github-pr` Empty-mode interview) is requirements work, not this confirmation.
- **Merge command** — rebase merge followed by a worktree-safe manual branch deletion is the universal default; the merge flow runs it unless the overlay opts in to a different command. The merge runs with explicit `--delete-branch=false` (`gh pr merge <pr-number> --rebase --delete-branch=false`), then this worktree detaches onto the refreshed base tip and the local and remote branches are deleted by separate commands — the sequence and its rationale are in `<merge_cleanup>`. The overlay may opt in to merge commit (`--merge`) or squash (`--squash`); merge commits and squashes are not Claude's choice to make from the gate alone. The overlay should document its rationale for human reviewers of the overlay change itself, but rationale is not a runtime predicate Claude enforces — the overlay's declaration is Claude's signal. The overlay MAY opt into inline `gh pr merge --rebase --delete-branch` for projects that are always single-worktree, where `gh`'s post-merge switch-to-base never collides.
- **Mention-reviewer trigger phrase** — the leading phrase Claude posts as a PR-level comment to fire the mention-triggered reviewer when the auto-review job reports `conclusion: skipped` (see `<authority_gates>` reviewer-skipped-by-design exception). The full comment body is `<trigger-phrase> review`; the `review` suffix is the keyword the mention reviewer matches on. Default: `@spec-tree` (the upstream reviewer action's default `trigger_phrase`). Each consuming project that configures a non-default `trigger_phrase` in its reviewer caller workflow declares the matching phrase here.

If `spx/local/merging.md` is absent or silent on a topic, the defaults in this reference apply. Absent preview, deployment, and release declarations make `PREVIEW`, `DEPLOY`, and `RELEASE` no-op phases; `MERGE_READINESS` still requires current-head CI review with no unresolved valid `BLOCKING` or `DEBT` finding, every other required check terminal-green, branch hygiene, and PR state. **Absence of a pre-mutation-confirmation setting means Claude drives the lifecycle autonomously**, with no up-front confirmation pause before the first mutation.

The overlay cannot override the open-ready mandate — once `VERIFICATION_READINESS` holds the PR is created `ready_for_review`. There is no draft phase and no gated draft-to-ready promotion; a stacked PR is the one exception, held draft per `<branch_topology>` until its base merges.
</repo_local_overlay>

<overlay_safety_checks>
When `spx/local/merging.md` declares preflight checks, run all of them immediately before the first checkout-sensitive mutation owned by each lifecycle entry. `/manage-github-pr` and the direct-push transport run them before branch or commit work, `/open-pr` before push, direct-push runs them again before its default-branch push, `/manage-pr` runs them after its initial read-only inspection and before base sync, finding repair, commit, push, or merge work, and `/handoff` runs them before every detach. `<merge_cleanup>` repeats the checks immediately before the merge command. A failed check stops before mutation with its output preserved.

When the overlay declares post-cleanup checks, run all of them immediately after every detach-based cleanup and before branch deletion, session persistence, deploy, release, or closeout. This applies both to `<merge_cleanup>` and whenever `/handoff` detaches a checkout. A failed post-cleanup check stops the remaining cleanup and preserves the detached checkout for inspection.
</overlay_safety_checks>

<delivered_value_boundary>

For changes destined for a repository's default branch, value is delivered only when the selected merge lifecycle reaches the default branch on origin. A branch with committed changes ahead of its resolved base is unfinished even when the working tree is clean and deterministic verification, tests, local review, or audits have passed. Those signals are progress evidence for `VERIFICATION_READINESS` and later gates, never completion.

When a status assessment finds a determined changeset with commits ahead of its resolved base, Claude reports the evidence it found and continues through the merge lifecycle unless the user explicitly limited the task to proposal, review, analysis, or local-only work, or the lifecycle reaches an explicit action-token or structured base-sync stop with no independent local action remaining. Terse follow-ups such as "so?", "continue", "ship it", "finish", and "go on" mean continue the already-governed lifecycle.

</delivered_value_boundary>

<close_phase>

`CLOSE` is the lifecycle disposition phase after the selected transport reaches the default branch on origin and every declared deploy or release phase has completed, no-oped, or stopped at an explicit readiness gate. Close is not a receipt. Close has two valid outcomes:

- continue remaining in-scope work directly when the user's stated goal still has do-able work; or
- close by invoking `/handoff` plain when the session is complete or continuation by Claude is impossible.

The `/handoff` invocation supplies the operator-useful product summary, verification evidence, delivered state, remaining-work disposition, and session-file decision. Merge transports invoke `/handoff` without receiving `--no-session`; the handoff workflow decides whether a continuation reader is needed from live state. A merge transport MUST NOT replace this phase with a receipt-only response that lists PR state, branch cleanup, commit SHAs, or sync mechanics while leaving the operator to infer what changed or what happens next.

</close_phase>

<branch_state_closeout>

After a default-branch merge, every transport produces branch-state closeout evidence before the final operator closeout. The GitHub-PR transport builds the full branch-state closeout record in `/manage-pr` Step 9 before returning closeout-ready evidence to `/manage-github-pr`. The direct-push transport preserves merge-time facts and delegates full record construction to `/handoff`, which computes the record from this section using its own closeout tool surface. The record removes ambiguity about which refs still exist, which are safe to delete, and which require operator attention.

The closeout record includes:

- PR number and merge commit SHA when the transport used a pull request; direct-push transports record the default-branch HEAD SHA after publication.
- Merged branch name.
- Whether the remote branch still exists.
- Whether the local branch still exists.
- Whether the local branch is fully merged into `origin/<base>`.
- Whether any live worktree checks out the local branch.
- Whether any preservation branch was created.
- For each preservation branch, whether its commits are exact ancestors of `origin/<base>`.
- For each non-ancestor preservation branch, `git cherry -v --abbrev=40 origin/<base> <branch>` output as patch-equivalence evidence.
- Final worktree state: clean or dirty, branch or detached, and current full HEAD SHA.
- Release-source worktree state when a declared release or marketplace refresh used a separate source worktree: path, branch, full HEAD SHA, clean or dirty, and sync status.

Use full branch names and full commit SHAs. Do not abbreviate identity values in the record, in commands, or in the final closeout.

Safe cleanup policy:

- If the remote feature branch exists after merge, delete it through the merge lifecycle's approved deletion command.
- If the local feature branch exists, its remote ref is absent, no live worktree checks it out, and its tip is an ancestor of `origin/<base>`, delete it with `git branch -d <branch>` regardless of upstream configuration.
- If a preservation branch has no remote and all substantive commits are present on `origin/<base>` by ancestry or patch equivalence, report it as safe to delete and delete it unless the branch name or operator instruction marks it as retained evidence.
- Never delete a branch checked out in another live worktree. Report the exact worktree path and branch instead.
- Never delete a branch whose commits are neither ancestors nor patch-equivalent to `origin/<base>`. Report the unmatched full SHAs and keep the branch.

Use git state observations rather than memory for every record field. The patch-equivalence observation is `git cherry -v --abbrev=40 origin/<base> <branch>`.

The final `/handoff` closeout includes a compact **Remaining Branches** section with exactly these groups:

- **Deleted locally**
- **Deleted remotely**
- **Retained, with reason**
- **Needs operator decision, with exact evidence**

</branch_state_closeout>

<local_deterministic_scope>

Local deterministic verification is the author-side validation and testing predicate for the exact changeset about to be published. It is scoped to the touched evidence by default:

- **Validation**: run the narrow validation lane that covers changed specs, skill files, generated plugin output, validation configuration, or implementation files. For Markdown-only skill/spec changes, this usually means the documented skill/doc or markdown validation commands rather than the full repository gate.
- **Testing**: run the node, package, module, or language test commands that exercise the assertions, source contracts, and implementation files the changeset touched.
- **Escalation**: run broader local validation/testing only when the overlay, governing node, or risk evidence requires it — for example a change to validation infrastructure, test runner wiring, generated distribution, package manager config, shared runtime code, or a broad refactor whose touched-scope commands cannot cover the contract.

CI owns full-repository deterministic regression detection. The author still owns all verification types locally: validate, test, review, and audit run before publication, but local validate/test are scoped while review/audit inspect the changeset and the touched node(s).

Run long or verbose deterministic commands with complete stdout/stderr redirected to a temporary log path, then inspect the summary, exit status, and failing sections. Do not stream passing-test logs through the session transcript. Keep the log path only when a failure requires later inspection; a passing run needs the command, exit code, and concise summary.

</local_deterministic_scope>

<assigned_cwd_worktree_discipline>

The changeset's git work — branch, commit, push, base-sync, PR management, merge, and its cleanup — happens in the **assigned worktree**, the repository working directory the session started in. The constraint that decides what is off-limits is **occupancy**, not worktree identity: a worktree is held by a live agent (claimed) or free, and in a bare-repository pool the default branch is unattached and claimable by any worktree.

- NEVER run the changeset's git work in a worktree **a live agent holds** — that collision is what this discipline prevents. NEVER create a worktree to carry the work, and NEVER use `git stash`; a dirty tree is cleared by committing per `<base_sync>`, never by stashing.
- A worktree or branch conflict is never a stopping point — it is branch-here-and-continue. When the assigned worktree is on the default branch, a detached HEAD, a dirty branch, or a branch name another worktree holds, create a fresh task branch in the assigned worktree from the resolved base and continue. When a PR branch is held in another worktree it is unavailable locally: stay in the assigned worktree, create a fresh branch there from the correct base or remote head, and push or open the PR from that branch.

Claude NEVER stops with blocked-by-worktree, cannot-use-other-worktree, or cannot-create-worktree reasoning. Branch in the assigned worktree and continue.

</assigned_cwd_worktree_discipline>

<branch_hygiene>

Conditions that must hold before every push (initial or follow-up). A branch-state failure is resolved in place per `<assigned_cwd_worktree_discipline>` — branch in the assigned worktree and continue, never switch to another worktree and never stash; the remaining conditions stop the calling flow until resolved.

| Condition (must hold)                                        | Failure response                                                                                                                   |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| Current branch is not `main`, `master`, or detached HEAD     | Create a fresh task branch in the assigned worktree from the resolved base and continue, per `<assigned_cwd_worktree_discipline>`. |
| Working tree is clean (no uncommitted changes)               | Commit via /commit-changes before pushing — never stash.                                                                           |
| Branch is at least one commit ahead of the resolved base     | STOP. Confirm the base branch — there is nothing to PR.                                                                            |
| Branch is not behind the resolved base (no upstream commits) | Rebase onto `origin/<base>` per `<base_sync>`, then re-run this gate.                                                              |
| Branch topology is classified as peer or stacked             | STOP. Apply `<branch_topology>` before continuing.                                                                                 |
| Work branch is not tracking the default branch               | STOP. Replace the upstream before pushing.                                                                                         |
| No PR already exists for this branch (initial push only)     | STOP. Surface the existing PR URL via `gh pr view --json url`.                                                                     |
| `gh auth status` reports an authenticated token              | STOP. Resolve auth before continuing.                                                                                              |

Commands:

```bash
gh auth status
git branch --show-current
git status --porcelain
base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git fetch origin "${base}"
git log --oneline "origin/${base}..HEAD"
git diff "origin/${base}...HEAD" --stat
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
if [ "${upstream}" = "origin/${base}" ]; then
  echo "STOP: work branch tracks the default branch" >&2
  exit 1
fi
existing_url=$(gh pr view --json url --jq '.url' 2>/dev/null)
[ -n "$existing_url" ] && echo "PR already exists: $existing_url"
```

The `exit 1` inside the upstream-safety check is a STOP for the calling flow.

</branch_hygiene>

<branch_topology>

Every PR branch is one of two shapes:

| Shape   | Meaning                                                                               | Required handling                                                                                                        |
| ------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Peer    | Targets the repository default branch and contains only its own review payload.       | Create from the current default branch. Refuse stale sibling merge commits.                                              |
| Stacked | Intentionally depends on another unmerged branch and targets that branch as its base. | Name the dependency in the PR body. Keep draft until the base merges, then reconstruct onto default base and open ready. |

**Peer-gate** (all must hold): `origin/${base}` is an ancestor of `HEAD`; the commit list contains only the intended payload; the changed file list matches the PR scope; no merge commits from sibling work.

```bash
base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git fetch origin "${base}"
git merge-base --is-ancestor "origin/${base}" HEAD
git log --merges "origin/${base}..HEAD"
git log --oneline "origin/${base}..HEAD"
git diff --name-only "origin/${base}...HEAD"
```

**Peer-gate failure path.** Pick exactly one repair before pushing:

1. **Repair as peer** — divergence unintentional. Rebase onto `origin/${base}`, drop sibling merge commits, re-run the gate.
2. **Reclassify as stacked** — dependency on an unmerged base is intentional. Identify the actual base branch, update the `<base>` argument used at `gh pr create` time, and run the stacked gate against it.

**Stacked-gate** (all must hold): the PR base is the previous stack branch (named in the PR body's `Stack` or `Merge order` note); the branch remains draft while the base is unmerged; after the base merges, the branch is rebased onto the updated default branch before final merge.

Identify the previous stack branch from context: the PR description's `Stack` / `Merge order` note, the branch-naming convention, or an explicit user instruction. If none of those yields a ref, the consuming workflow asks the operator through its own structured-question tool grant rather than guessing.

```bash
base_branch="<previous-stack-branch>"
git fetch origin "${base_branch}"
git merge-base --is-ancestor "origin/${base_branch}" HEAD
git log --oneline "origin/${base_branch}..HEAD"
git diff --name-only "origin/${base_branch}...HEAD"
```

**Post-merge reconstruction.** Once the stack base merges, re-invoke /open-pr (or rebase manually) to re-target the PR at the default branch, re-classify as peer, and open it ready. GitHub auto-retargets the PR base on the API side, but the local branch must still be rebased onto the updated default and the manifest version re-evaluated against the new base.

</branch_topology>

<push_semantics>

Always push with an explicit destination ref:

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"          # first push
git push    origin HEAD:refs/heads/"${branch}"          # subsequent pushes
git push --force-with-lease origin HEAD:refs/heads/"${branch}"  # after a rebase (see <base_sync>)
```

The bare `git push` and `git push -u origin <branch>` forms are forbidden because `push.default=tracking` would publish feature-branch commits to whatever upstream is configured locally — including `main` when the branch was created from `main` without an upstream reset. The `HEAD:refs/heads/<branch>` form makes the remote branch explicit and removes the dependency on local upstream configuration.

A rebase rewrites branch history, so the post-rebase push cannot fast-forward. `--force-with-lease` performs the non-fast-forward push but refuses if the remote branch advanced since the last fetch, which keeps it safe on a single-author PR branch. Plain `git push --force` stays forbidden — it overwrites the remote unconditionally.

If the product defines a custom branch-push command, follow the product convention from {{! file('root_guide') !}} — the explicit destination ref must remain part of any custom command.

</push_semantics>

<base_sync>

Base drift is checked on the same checkpoint that inspects reviews — every management pass reads review state and the `origin/<base>` position together. When the branch is behind `origin/<base>`, sync immediately through `/sync-base`, independent of whether a review has landed and independent of whether any landed review carries findings.

`/sync-base` owns the mechanism: it fetches the base, rebases the branch onto `origin/<base>`, and never uses `git reset` to integrate base movement. Claude NEVER asks the operator whether to rebase — base-sync is a mechanical consequence of observable git state, not a decision to surface; surfacing "should I rebase?" through a structured question or in prose is a defect. A clean rebase runs to completion with no operator interaction. A conflict `/sync-base` cannot resolve autonomously is reported as `conflict` with a structured `conflict` object; the rebase remains active so the operator can inspect, resolve and continue, or abort. A `dirty_tree` outcome — uncommitted tracked changes blocking the rebase — is not a conflict: commit the working changes through `/commit-changes`, then re-run `/sync-base`. Never stash, and Claude never surfaces a dirty tree as an operator decision.

Rebase on drift, not at merge time. A branch behind base is superseded by a rebase before it can merge, so every check run and every review posted against the un-rebased head is wasted effort. Rebasing the moment drift appears aims CI and reviewers at the head that will actually merge, and surfaces a conflicted ("nasty") rebase early during review/check convergence instead of at merge time, where an unexpected conflict or an integration regression costs a full extra review round on the critical path.

Invoke `/sync-base` with the calling flow's base passed as `--base ${base}` rather than letting it re-derive one — /manage-pr Step 1 captures `${base}` from `gh pr view --json baseRefName` (which returns the PR's actual base for both peer and stacked topologies), and /open-pr's `<branch_hygiene>` sets it from `gh repo view --json defaultBranchRef` before any PR exists. The block runs identically in both contexts.

When `/sync-base` reports `rebased`, the rebased tree is a fresh integration — this branch replayed on newly merged work — and the consuming flow re-establishes all `VERIFICATION_READINESS` predicates on it before the `--force-with-lease` push from `<push_semantics>`, fixing any failure or unaddressed valid finding in the same pass. The `preservation` proof in the `/sync-base` result scopes how much of that work the base movement actually invalidated, so a rebase that moved an unrelated part of the tree does not force a full re-run:

- **Local review.** Reuse the converged `changes-reviewer` verdict when `preservation.branch_diff_unchanged` is true **and** no `preservation.base_delta_paths` entry is a governance surface the reviewer judges against (named in the project's merge overlay). Otherwise re-establish the review per `<local_review_invocation>` on the rebased diff.
- **Evidence-auditor predicates.** Reuse a prior evidence-auditor verdict only when `preservation.branch_diff_unchanged` is true and no `preservation.base_delta_paths` entry touches a governed evidence surface. Otherwise re-dispatch the applicable evidence auditors before local review.
- **Deterministic verification.** Run the narrowest local validation/testing lane the project's merge overlay maps `preservation.base_delta_paths` to per `<local_deterministic_scope>`; widen only when an entry is unclassified, `preservation.path_overlap` is non-empty, `preservation.branch_patch_changed` is true, or the overlay/risk evidence requires it.

The proof scopes pre-push local work only. After the push, `MERGE_READINESS` still requires every current-head required check terminal-green and a clean current-head CI review — a preservation proof never substitutes for either. When the project declares no overlay lane mapping, run the full deterministic-verification command and re-establish the review on every rebase.

Integrate base movement only by rebase through `/sync-base`. The same prohibition binds the review-convergence loop, where Claude reorganizes the branch's own commits: NEVER `git reset` onto `origin/<base>` — not to integrate base movement, and not to reword or re-split the branch's own commits. `origin/<base>` advances as concurrent worktree-pool branches merge, so a reset onto it silently re-bases the branch onto whatever it became; with `--soft` the working tree is left on the old basis while HEAD jumps forward, desyncing the tree (files present in HEAD show as deleted, files the new base changed show as modified, none of it the branch's work). To reword or re-split the branch's own commits, reset to a FIXED ancestor on the branch — `git reset --soft HEAD~N` where N is the branch's own commit count, or the fork-point SHA from `git merge-base HEAD origin/<base>` — never onto `origin/<base>`. After any history rewrite, confirm `git diff --stat origin/<base>...HEAD` shows only the intended files and `git status` reports no surprise deletions before the `<push_semantics>` push; surprise files mean the base moved under the rewrite — stop and re-derive, do not push.

</base_sync>

<local_review_invocation>

The local `changes-reviewer` gate is the author-side, pre-push instance of the same review kind the CI review runs post-push — the two are the same class of gate on opposite sides of each push. Before invoking it for a gate, pass deterministic verification, create a checkpoint commit through /commit-changes, and confirm the worktree has no staged, unstaged, or untracked changes. A dirty-worktree review is advisory and never satisfies `VERIFICATION_READINESS`. Invoke the gating review the way CI invokes its reviewer, passing nothing that narrows it:

- **Use a raw committed scope.** Pass `HEAD` for the clean current-head subject. When the changeset's base is not `origin/HEAD`, pass `origin/<base>...HEAD`. Pass nothing else — no file list, no changed-area summary, no "the important part is …". The reviewer self-discovers the worktree and computes the committed diff.
- **Add no interpretive scope.** Do not tell the reviewer which layers, files, or concerns to weight. It reviews the whole diff against the whole taxonomy.
- **Add no severity pre-filter.** Do not ask only for `BLOCKING`, do not suppress `DEBT`. The reviewer emits every finding; handling is by validity and explicit resolution evidence per `<review_classification>`, downstream of the review and never inside its invocation.
- **Add no emphasis steering.** Do not tell the reviewer what to conclude or what matters most. It reads the repository's own instructions ({{! file('root_guide') !}} and the standards skills) and the shared taxonomy itself.

Run it via the `changes-reviewer` agent. The isolated context keeps the verdict from being biased by what the operator's main context has been doing. Iterate to convergence: each round, act on findings by validity and explicit resolution evidence per `<review_classification>`, rerun affected deterministic and evidence gates, create a new checkpoint commit, confirm the worktree is clean, and review the new committed head until no valid finding remains unresolved.

This is the review predicate `VERIFICATION_READINESS` reads, and it runs before every push — the opening push (`/open-pr`) and every follow-up push (`/manage-pr`) — against the clean committed head that push would publish. Narrowing the invocation or reviewing a dirty worktree diverges the local gate from the CI reviewer it parallels, so its convergence no longer means what `VERIFICATION_READINESS` claims it means.

</local_review_invocation>

<authority_gates>

The delivery lifecycle runs `VERIFY -> PREVIEW -> MERGE -> DEPLOY -> RELEASE -> CLOSE` with four gates, evaluated in order: `VERIFICATION_READINESS`, `MERGE_READINESS`, `DEPLOYMENT_READINESS`, and `RELEASE_READINESS`. A **gate** is a named authorization over one lifecycle step, decided from defined predicates; a **predicate** is a condition a gate reads — predicates are never themselves gates. `/open-pr` evaluates the GitHub-PR transport's `VERIFICATION_READINESS` predicates before publishing; `/manage-pr` evaluates `MERGE_READINESS` for the current head, then continues through declared `DEPLOYMENT_READINESS` and `RELEASE_READINESS` phases after merge.

**`VERIFICATION_READINESS`** authorizes publishing the verified changeset to the selected transport. For the GitHub-PR transport, it authorizes opening the PR. It holds when all predicates hold:

- **deterministic verification passes** — the project's local validation and testing commands for the touched scope per `<local_deterministic_scope>` report success. A failing touched-scope test means this predicate does not hold, including a TDD-red opener authored intentionally ahead of an implementation slice. The remedy is either land the implementation in the same PR so the test passes, or add the owning node to the project's spec-tree EXCLUDE mechanism (for example `spx/EXCLUDE`) so the test runner skips the node until implementation arrives. See `references/excluded-nodes.md` in `/understand`. Per-line suppression (`# noqa`, `# type: ignore`, `@pytest.mark.skipif`, `@pytest.mark.xfail`, equivalents in other languages) does not satisfy this predicate because those suppressions are scattered and invisible to the spec-tree status surface; and
- **required evidence audits have passed** — when the diff creates or modifies `[test]` assertions, linked test files, or test-infrastructure artifacts imported by linked tests, dispatch `test-evidence-auditor`; when the diff creates or modifies `[eval]` assertions, eval artifacts (`eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`), or producer artifacts for eval-backed assertions, dispatch `eval-evidence-auditor`. Run the applicable evidence auditors after deterministic verification passes and before `changes-reviewer`. Handle rejected, failing, or unknown evidence-auditor verdicts per `<auditor_verdicts>`; and
- **the local review has converged** — `changes-reviewer`, invoked at parity per `<local_review_invocation>` and iterated to convergence, leaves no valid finding unresolved: the defect class is repaired and the current head is re-reviewed, the finding is individually dropped as unbacked, the affected capability leaves the changeset and the current head is re-reviewed without the finding, or an operator waiver identifies that exact finding and explicitly accepts its stated consequence. A tracking record, general merge authorization, or severity-only authorization resolves nothing.
- **the terminal full deterministic gate has passed when required** — `just check-full` ran after every applicable evidence audit and agentic review converged, against the current clean committed head, with no subsequent change and no concurrent heavy command.

The moment `VERIFICATION_READINESS` holds, the PR is created `ready_for_review` — never draft (a stacked PR is the one exception, held draft per `<branch_topology>` until its base merges). There is no draft phase and no gated promotion; opening ready fires every CI review at once (reviewers that wait for ready, such as Codex, alongside the CI review). A declared `PREVIEW` action then runs before `MERGE_READINESS`; absent preview declaration means `PREVIEW` is a no-op and never blocks merge.

All `VERIFICATION_READINESS` predicates are re-established before every push, not only the opening push. A follow-up push that changes the branch's own content — a fix for a CI finding — re-runs local deterministic verification per `<local_deterministic_scope>`, re-runs any evidence-auditor predicate whose touched evidence surface changed, and re-runs the local review per `<local_review_invocation>` on the new diff before it is pushed. A follow-up push that **only** rebased onto an advanced base re-establishes the predicates scoped by the `<base_sync>` preservation proof — reusing the local review and evidence-auditor verdicts when the branch diff is unchanged and the base movement does not touch the governed evidence surface, and running a narrower local validation/testing lane when the proof and the project overlay permit — rather than always re-running every predicate in full. Either way, the author-side evidence audits and review precede the push that fires CI, so a follow-up diff never reaches CI without author-side agentic verification first.

**`MERGE_READINESS`** authorizes merge. It holds when all predicates hold, every one decidable from observable PR state:

- a clean current-head CI review exists — the review-kind output for the current head, read from the surfaces in `<review_inspection>`, complete and valid, that reports **no unresolved valid `BLOCKING` or `DEBT` finding**. Each reported finding is resolved only by repair and current-head re-review, individual refutation as unbacked, removal of the affected capability followed by current-head re-review, or an exact operator waiver that explicitly accepts the finding's stated consequence. A tracking record, general merge authorization, or severity-only authorization leaves the finding unresolved. When multiple reviewers or review surfaces comment on the same head, the review predicate reads the union of current-head findings: a no-findings review from one reviewer never cancels a valid finding from another reviewer, and a required-check success never cancels a valid finding posted as a PR comment or review-thread comment. The absence of a current-head review is never clean — it is `WAIT_FOR_REVIEW`;
- every other required check on `statusCheckRollup` is **terminal-green** (defined below);
- `<branch_hygiene>` passes, including the upstream-safety check;
- PR state is `OPEN`, `isDraft` is false, the inspected head SHA matches the branch head fetched from origin, and the branch is rebased onto current `origin/<base>` or is a fast-forward descendant.

`MERGE_READINESS` carries no time-based settle: a clean review arriving two minutes after open makes the gate hold two minutes after open.

**Mutation-point guard.** Immediately before any `gh pr merge` command, /manage-pr re-reads live PR state and recomputes `MERGE_READINESS`; it never relies on earlier inspection, conversation memory, or a prior `gh pr view` result. The guard reads PR state, `statusCheckRollup`, PR-level comments, formal reviews, review-thread comments, the fetched remote branch head, and the fetched base branch. It produces `MERGE_READY:<head-sha>` only when the freshly inspected head SHA, fetched remote branch head, and inspected status-check SHA match and every `MERGE_READINESS` predicate above still holds for that same head.

The guard withholds the merge command and emits the existing action token when any predicate fails:

- `WAIT_FOR_REVIEW` when current-head review output is absent, or the review-kind check is missing or non-terminal.
- `WAIT_FOR_CHECKS` when a non-review required check is queued, in progress, pending, expected, or otherwise non-terminal.
- `MENTION_REVIEW_NEEDED:<trigger-phrase>` when the review-kind check is skipped because the PR modifies the reviewer's own workflow file.
- `MERGE_BLOCKED:review-check-skipped` when the review-kind check is skipped for any other cause.
- `MERGE_BLOCKED:review-check-failed` when the review-kind check is terminal but failed, cancelled, timed out, action-required, or neutral.
- `MERGE_BLOCKED:<reason>` when a non-review required check is absent or terminal-but-not-success, the head SHA does not match the fetched remote branch head or status-check head, the PR is closed/draft, the branch is not based on current `origin/<base>`, or any other hard PR-state predicate fails.

Review-kind check outcomes map before non-review required-check outcomes. Missing or non-terminal emits `WAIT_FOR_REVIEW`; success permits inspection of the review surfaces but does not satisfy the review predicate alone; a self-modifying workflow skip emits `MENTION_REVIEW_NEEDED:<trigger-phrase>`; any other skip emits `MERGE_BLOCKED:review-check-skipped`; failed, cancelled, timed-out, action-required, or neutral emits `MERGE_BLOCKED:review-check-failed`.

`mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, and a successful `gh pr merge` response are GitHub transport behavior, not repository policy authority. Claude never runs `gh pr merge` as a probe for mergeability; the command is legal only after the mutation-point guard has produced `MERGE_READY:<head-sha>`.

**`DEPLOYMENT_READINESS`** authorizes declared environment mutation after merge. It holds when every project- or transport-declared deployment predicate authorizes the mutation. When no deploy action is declared, `DEPLOY` is a no-op phase and never blocks later phases.

**`RELEASE_READINESS`** authorizes declared consumer-visible publication or refresh after deployment. It holds when every project- or transport-declared release predicate authorizes the publication or refresh. When no release action is declared, `RELEASE` is a no-op phase and never blocks close.

When a declared deploy action exists but its authorization predicate is unsatisfied, the delivery decision is `DEPLOYMENT_READINESS = WITHHOLD` with action token `AWAIT_DEPLOYMENT_AUTHORIZATION`; when a declared release action exists but its authorization predicate is unsatisfied, the delivery decision is `RELEASE_READINESS = WITHHOLD` with action token `AWAIT_RELEASE_AUTHORIZATION`. The transport preserves the branch-state closeout record, stops before the unauthorized action, and does not continue until the operator supplies the project-declared authorization and the managing flow re-inspects state.
Claude NEVER asks the operator to choose between auto-merge, hold-at-green, or pause. The merge is a mechanical consequence of `MERGE_READINESS` plus the mutation-point guard returning `MERGE_READY:<head-sha>`, not a decision to surface; the only operator-facing pauses the lifecycle carries are the explicit `<action_tokens>` an unresolved condition emits.

**terminal-green.** A required check in `statusCheckRollup` is a check run (`status` reaches `COMPLETED`, then a `conclusion`) or a status context (`state`). It is **terminal-green** only when terminal — `status == COMPLETED`, or `state ∈ {SUCCESS, ERROR, FAILURE}` — AND successful — `conclusion == SUCCESS`, or `state == SUCCESS`. A check that is non-terminal (`QUEUED` / `IN_PROGRESS` / `PENDING` / `EXPECTED`), terminal-but-not-success (`FAILURE` / `CANCELLED` / `TIMED_OUT` / `SKIPPED` / `NEUTRAL` / `ACTION_REQUIRED` / `ERROR`), or absent from the rollup is not terminal-green and blocks `MERGE_READINESS`.

**Acting on findings (validity and explicit resolution evidence, never severity).** Validate each finding against its cited rule, product-local or language governance, and the governing PDR/ADR decisions. Drop an unsupported finding individually as unbacked. For every valid finding, repair the defect class and re-review the current head. When the required repair belongs to a capability too large for the changeset, remove that capability and its finding from the changeset together, then re-review the current head; a coordination note may preserve the removed work but contributes nothing to readiness. The remaining resolution is an operator waiver that identifies the exact finding and explicitly accepts its stated consequence. A general instruction to merge, permission conditioned only on severity, permission to proceed when no finding is considered "truly blocking", or a tracking record waives nothing. Severity is the reviewer's reporting label; validity and explicit resolution evidence decide whether the finding remains unresolved, and the reviewer never decides whether the change merges.

**Same-class sweep.** A valid review or audit finding is evidence of a defect class, not only the cited line. Before the next push, inspect the touched node(s) — the files they govern — for parallel instances of the same defect: same rule, same source contract, same evidence pattern, same lifecycle step, or same generated-source relationship. Fix every in-scope parallel instance in the same bounded changeset. If the sweep proves the cited instance isolated, record that conclusion in the review/audit handling summary. A one-line patch that only satisfies the cited example is incomplete until this sweep is done.

**Reviewer disagreement and repeated rounds.** A clean review, passing required check, approved audit, or "no findings" comment is evidence about that reviewer or verifier's scope only; it does not invalidate a separate current-head finding that is backed by its cited rule and governance. Repeated valid findings in the same lifecycle area — each exposing a deeper variant of the same source contract, state transition, crash path, idempotency boundary, artifact lifecycle, or other defect class — mean the defect class is still open. Widen the same-class sweep, repair the underlying contract, and re-run the author-side review before the next push. Never convert that pattern into a "stuck gate" stop, operator call, or merge allowance. A path being foundational, not yet consumed by production code, behind a deferred downstream slice, or covered by other clean gates does not change finding disposition: if the changed diff carries the failure mode and the finding is valid, fix it in the changeset, remove the affected capability before re-review, or obtain an exact operator waiver accepting the stated consequence.

**Reviewer-skipped-by-design (self-modifying-PR exception).** When the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate), no current-head review exists for `MERGE_READINESS`. Post one PR-level comment containing exactly `<trigger-phrase> review` (e.g., `@spec-tree review`) to fire the mention reviewer (which has no identical-content gate), emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run `<pr_check_wait>`, and on the next management pass treat that reviewer's posted findings as the current-head review. This applies to that skip cause only — not path-filter, branch-filter, or manual skips.

**Follow-up pushes.** The PR is ready from open; a follow-up push — fixing a valid CI finding, or a `<base_sync>` rebase — pushes to the ready PR and re-fires CI. There is no draft toggle and no `gh pr ready` step in the loop.

</authority_gates>

<merge_cleanup>
Read `${CLAUDE_SKILL_DIR}/references/merge-cleanup.md` immediately before the merge mutation. It defines the merge command, overlay checks, worktree transition, and remote and local branch cleanup sequence.

</merge_cleanup>

<pr_check_wait>

Waiting for PR checks or the current-head CI review uses exactly one foreground command:

```bash
gh pr checks <pr-number> --watch --fail-fast --interval 30
```

After that command exits, immediately run the full managing inspection again before acting: PR state, check rollup, PR-level comments, formal reviews, and review-thread comments. This is the only PR-check wait path in the GitHub-PR lifecycle, applies to both Claude Code and Codex, and never runs in the background.

Forbidden waits: shell `sleep`, `gh run watch`, background keep-alives, and `until`/`while` polling. Never wrap `gh pr checks --watch` in a loop or background it. The Bash tool does not reliably reap detached subprocess trees across turns; fork-bomb-class accumulation results when those patterns are repeated.

</pr_check_wait>
<review_inspection>

Inspect all three review surfaces. Automated reviewers (and humans) may post as **formal reviews** OR as **PR-level issue comments** OR as **review-thread comments on specific lines** — checking only one or two surfaces misses feedback.

```bash
# Formal reviews + PR-level issue comments
gh pr view <pr-number> --json reviews,comments \
  --jq '{reviews: [.reviews[] | {author: .author.login, state, submittedAt}],
         comments: [.comments[] | {author: .author.login, createdAt, excerpt: .body[0:160]}]}'

# Review-thread comments tied to specific lines
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments --paginate \
  --jq '.[] | {id, node_id, author: .user.login, path, line, createdAt: .created_at, excerpt: .body[0:160]}'
```

**NEVER drop `comments` from the `gh pr view --json` argument list.** The `comments` field carries PR-level issue comments — a distinct surface from `reviews` (formal review submissions) and from `gh api repos/<owner>/<repo>/pulls/<n>/comments` (review-thread comments tied to specific lines). Dropping `comments` to "trim the JSON" silently loses that third surface; a valid `BLOCKING` or `DEBT` finding posted there is invisible to the inspection, and `MERGE_READINESS` evaluates against a partial view.

Completeness is checked per invocation. Every `gh pr view --json` invocation that participates in a management pass or re-inspection MUST include both `reviews` and `comments` in its field list, even when the same pass also runs another broader `gh pr view` command. Classify a pass by scanning each field list independently: if any participating field list omits `comments`, the PR-level issue-comment surface is missing for that pass and the inspection is incomplete; if any participating field list omits `reviews`, the formal-review surface is missing for that pass and the inspection is incomplete. A pass with one complete `reviews,comments,...` list followed by a later `reviews,...` list missing `comments` is incomplete with missing surface `comments-field`; the earlier complete call never repairs the later narrower call. Whatever field list a calling flow constructs — it may add `statusCheckRollup`, `headRefOid`, `baseRefName`, `mergeable`, `mergeStateStatus`, or others for the merge-state predicates — `reviews` and `comments` remain mandatory. Construct the field list explicitly per pass; do not omit fields from an abbreviated re-creation between turns.

Compare timestamps against the most recent push. Entries after that push are re-reviews of the latest state — read them in full.

</review_inspection>
<review_classification>

Every review finding — whether produced by a reviewer (outgoing feedback) or triaged by an author (incoming feedback) — carries two dimensions: **severity** (one of two) and **concern** (one of five). The taxonomy is shared so output and triage use the same vocabulary; nothing has to be translated between them.

This skill is the canonical consumer-facing taxonomy. Repositories may add local review instructions, but the default severity and concern vocabulary below is complete here.

**Severity** (one of two — the reviewer's reporting label for the finding's merge-safety nature):

| Severity   | Use when                                                                                |
| ---------- | --------------------------------------------------------------------------------------- |
| `BLOCKING` | Defect with evidence of a deterministic merge-safety consequence.                       |
| `DEBT`     | Real defect whose evidence does not establish a deterministic merge-safety consequence. |

Severity is the reviewer's classification of a valid finding's evidenced consequence. It never supplies disposition. **Disposition** belongs to the review consumer and uses the same resolution set for `BLOCKING` and `DEBT`: repair and current-head re-review, individual refutation as unbacked, removal of the affected capability followed by current-head re-review, or an exact operator waiver accepting the finding's stated consequence. Tracking preserves information only; it never resolves a finding and never contributes to readiness.

**A defect the changeset carries remains part of the changeset's resolution burden.** A stale claim, orphaned code, broken cross-reference, falsified spec, inadequate evidence, or any other valid defect remains unresolved regardless of how many files its repair touches. When the repair belongs to a capability too large for the changeset, remove the capability itself before re-review. Never retain the affected capability while moving only its finding into a coordination note.

**Handling is by validity and explicit resolution evidence, never by severity.** Severity classifies the finding's evidenced consequence for the reader; it is not a routing key. Validate each finding against its cited rule and governing decisions, drop unsupported findings individually, and apply one of the valid resolutions above to every supported finding. A `BLOCKING` label does not rescue an unsupported citation, and a `DEBT` label does not exempt a real defect.

**Same-class sweep before disposition.** Treat a valid review or audit finding as evidence of a defect class. Before fixing only the cited site, inspect the touched node(s) for parallel instances with the same rule, source contract, evidence pattern, lifecycle step, or generated-source relationship. Fix all in-scope parallel instances in the same changeset, or record in the handling summary that the sweep found the cited instance isolated. Do not run another external review round after a micro-edit that only addresses one example while the defect class remains unswept.

**Cross-reviewer union and convergence.** Build one finding ledger from all current-head review surfaces and reviewers, then classify each item once. A no-findings review from the designated CI reviewer, a clean local review, a passing deterministic check, or an approved audit never cancels a valid finding from another reviewer. Multiple review rounds that keep surfacing valid variants in the same area are not reviewer noise and not an operator decision point; they prove the prior fix or sweep was too narrow. Treat the next valid variant as the same defect class until the underlying lifecycle contract is repaired and a new review round finds no valid variant. "Not wired into production yet" and "deferred next slice" are not dispositions for code in the diff; apply the exact resolution set to every valid finding.

**Concern** (one of five), grouped by three axes:

*What the code does vs. what it is supposed to do*

- `consistency` — disagreement across layers (decisions / PDR / ADR <-> spec <-> tests <-> implementation). Surface the disagreement; do not judge which side is right.
- `security` — confidentiality, integrity, availability.
- `performance` — unbounded loops, hot-path allocations, O(n²) traversals where O(n) suffices, synchronous I/O on async paths, and similar pessimisations that change the changeset's runtime characteristics under realistic load.

*How we know it does what it is supposed to do*

- `evidence` — inadequate coverage of declared assertions by tests or evals; unmaintainable tests (literals, magic numbers, test-owned constants, duplication); evals that no longer exercise the assertions they claim to.

*How it does what it is supposed to do*

- `architecture` — violation of structural principles declared by ADRs, PDRs, root instructions, or standards skills (layer boundaries, separation of concerns, dependency directions, module-shape rules, naming, command tokens, file structure, or language idioms). A finding is an architecture one when the structure itself is at odds with a governance principle, even if every layer is internally consistent.

**Finding shape.** Both `BLOCKING` and `DEBT` findings carry `id`, `concern`, `severity`, `file`, `line`, `rule`, `message`, and `action`. Reviewers stream one JSON finding object at a time through `append-finding`; consumers may normalize incoming human comments into the same fields before classification.

**No findings: emit no finding objects.** When the changeset has no `BLOCKING` or `DEBT` findings, the review stream is empty and the run records completion separately. NEVER invent lower-priority findings to prove the review happened.

**Findings only — never open questions, never commentary.** A reviewer with a question frames it as a finding (e.g., "Evidence: cannot verify X from the changeset; if assumption Y holds, this breaks Z because …") rather than asking a question that waits for an answer. Questions add CI roundtrips a single-pass review cannot recover from. Praise, observations, and commentary that do not constitute findings are noise — omit them.

**Forbidden taxonomies.** Severity-rank labels MUST NOT replace the two severities — no `P0` / `P1` / `P2` / `P3`, no `critical` / `high` / `medium` / `low`, no `minor` / `nit` headings. A third scope-shaped severity (`FOLLOW-UP`) MUST NOT reappear — finding resolution belongs to the review consumer and is never a reviewer severity. Risk words may appear inside rationale only when they add concrete evidence, never as a finding's primary label. Legacy class labels `NEEDS-ANSWER` and `NOTE` are forbidden — open questions are reframed as findings; commentary is omitted.

Finding object example:

```json
{
  "id": "F-001",
  "concern": "consistency",
  "severity": "blocking",
  "file": "path/to/file",
  "line": 42,
  "rule": "spx/path/to/node.md:ALWAYS:1",
  "message": "The changed lower layer contradicts the cited assertion.",
  "action": "Align the lower layer with the cited assertion."
}
```

</review_classification>

<auditor_verdicts>

Local auditor agents — `test-evidence-auditor`, `eval-evidence-auditor`, `adr-auditor`, `pdr-auditor`, `spec-auditor`, and `implementation-auditor` — emit structured findings for the slice they inspect. Language-specific audit concerns are composed through the installed `audit-{lang}-{code|tests|architecture}` skills, not through language-specific auditor agents.

**Verdict handling.** A `REJECTED` overall verdict, an `UNKNOWN` overall verdict, a `FAIL` row, an `UNKNOWN` row, or a `REJECT` finding is in-slice unresolved work, identical in handling to a valid `BLOCKING` or `DEBT` finding in `<review_classification>`: fix the bug or resolve the audit uncertainty, re-run the auditor, repeat until clean. `APPROVED` means the auditor found nothing in scope. "Capture in `ISSUES.md`" is NOT an option for rejected or unknown in-slice audit work on a slice currently under review — `ISSUES.md` is for items outside the slice (a known gap in an unrelated module, a tracking note for future enablement), never for in-slice bugs or audit uncertainty the auditor surfaced.

**Why auditor verdicts are authoritative.** Auditor agents invoke the same audit skills the operator would invoke directly; each verdict is the audit skill's structured output for its specific concern, not a separate discretionary decision. CI green and reviewer-bot approval do not erase an auditor REJECT because audit and review inspect different concerns: test evidence, PDR quality, architectural fitness, or language-specific code quality.

**Loop semantics.** When an invoked workflow surfaces auditor verdicts while preparing or repairing a PR, handle every `REJECTED` or `UNKNOWN` overall verdict, `FAIL` or `UNKNOWN` row, and `REJECT` finding as in-slice work under `<review_classification>`: fix it or resolve the audit uncertainty, re-run the auditor, and repeat until no rejected or unknown in-slice audit work remains. `APPROVED` means the auditor found nothing in its scope. Auditor findings do not add a fourth PR-lifecycle gate and do not change the `MERGE_READINESS` predicate set in `<authority_gates>`.

</auditor_verdicts>

<action_tokens>
Read `${CLAUDE_SKILL_DIR}/references/action-tokens.md` before emitting a merge lifecycle action token. The reference defines `WAIT_FOR_CHECKS`, `WAIT_FOR_REVIEW`, `FIX_FINDING:<item>`, `MENTION_REVIEW_NEEDED:<trigger-phrase>`, `MERGE_BLOCKED:<reason>`, `AWAIT_DEPLOYMENT_AUTHORIZATION`, and `AWAIT_RELEASE_AUTHORIZATION`, including the exact trigger condition and required follow-up for each token.
</action_tokens>
<self_reference>No "Claude", "AI", "agent", "Co-Authored-By: Claude", or similar identity strings in any merge-flow artifact: branch names, commit messages, PR titles, PR bodies, review comments.</self_reference>

<failure_modes>

**Failure 1: Claude required gone-upstream tracking for local cleanup.**
What happened: Claude retained a safely merged local branch because it had no upstream configuration.
Why it failed: Upstream configuration is optional metadata and does not establish branch safety.
How to avoid: Apply `<branch_state_closeout>` using remote-ref absence, worktree occupancy, and ancestry.

**Failure 2: Claude force-deleted the local branch before proving safety.**
What happened: Claude deleted the branch without proving its commits were present on the base.
Why it failed: The branch could contain commits absent from the base.
How to avoid: Follow `${CLAUDE_SKILL_DIR}/references/merge-cleanup.md`: remove the remote ref first, prove the local tip is an ancestor, and use `git branch -d`.

**Failure 3: Claude let `gh pr merge` clean up the branch.**
What happened: Claude delegated local cleanup to the host CLI.
Why it failed: Host or CLI behavior can switch onto a base held by another worktree and fail after merging.
How to avoid: Pass `--delete-branch=false`, then run the explicit cleanup sequence.

</failure_modes>

<success_criteria>
The flows that consume this vocabulary satisfy their contracts when, at minimum:

- `<branch_hygiene>` predicates hold before every push (initial and every follow-up).
- `<branch_topology>` is classified before every push, with the matching gate passing.
- Every push uses the explicit destination ref form from `<push_semantics>`.
- A managing-flow pass that finds the branch behind `origin/<base>` rebases it per `<base_sync>` before driving the work queue.
- The PR opens `ready_for_review` once `VERIFICATION_READINESS` holds — local deterministic verification per `<local_deterministic_scope>` passes, every required evidence-auditor predicate has passed, and the local review has converged — with no draft phase as a gating mechanism (a stacked PR held draft per `<branch_topology>` is the one exception).
- All `VERIFICATION_READINESS` predicates — local deterministic verification per `<local_deterministic_scope>`, required evidence-auditor predicates, and a converged local review — are re-established on the diff every push publishes: the opening push and every content-changing follow-up push; a push that only rebased onto an advanced base re-establishes them scoped by the `<base_sync>` preservation proof.
- The local `changes-reviewer` gate is invoked per `<local_review_invocation>` — the review resolves its own scope, with no interpretive scope, severity pre-filter, or emphasis steering added.
- Waiting for CI review or checks uses the exact PR-check wait command from `<pr_check_wait>`.
- All three surfaces in `<review_inspection>` are inspected after every push, with `comments` always present in the `gh pr view --json` field list.
- Every finding is labeled with one of `BLOCKING` / `DEBT` — never `FOLLOW-UP`, never a severity rank, never a legacy class label — and acted on by validity and explicit resolution evidence, never by severity.
- Every auditor verdict from a local auditor agent (per `<auditor_verdicts>`) is handled as an in-slice finding; `REJECTED` or `UNKNOWN` overall verdicts, `FAIL` or `UNKNOWN` rows, and `REJECT` findings are fixed or resolved in the slice, not deferred to `ISSUES.md`.
- Merge runs only when `MERGE_READINESS` holds and the mutation-point guard has just produced `MERGE_READY:<head-sha>`: the current-head CI review has no unresolved valid `BLOCKING` or `DEBT` finding, every other required check is terminal-green, branch hygiene and PR-state hold on the freshly inspected head, and the inspected head SHA matches the fetched remote branch head and status-check head. `MERGE_READINESS` carries no time-based settle.
- A committed changeset ahead of its resolved base is treated as unfinished until it reaches the default branch on origin through the selected lifecycle, or stops at an explicit action-token emission or structured base-sync conflict report with no independent local action remaining.
- Local readiness — clean working tree, committed changes, passing deterministic verification, tests, local review, or audits — is reported as evidence and then carried forward; it is never a reason to ask what to do next.
- `CLOSE` continues in-scope work directly or invokes `/handoff` plain for operator-useful closeout and continuation disposition; a receipt-only response never satisfies the lifecycle.
- No structured question or prose confirmation asks the operator to choose between auto-merge, hold-at-green, or pause; the only operator-facing pauses are explicit `<action_tokens>` emissions and structured base-sync conflict reports.
- The changeset's git work runs in the assigned worktree per `<assigned_cwd_worktree_discipline>` — never in a worktree a live agent holds, no created worktree, no `git stash`; a branch conflict is resolved by branching in the assigned worktree and continuing.
- `spx/local/merging.md` is read only when present, its absence applies the defaults with no blocker, and merge behavior is never reconstructed from incidental docs or changed by editing a generated guide.
- Every overlay-declared preflight runs before the lifecycle entry's first checkout-sensitive mutation, direct-push repeats it before default-branch publication, and a failed check preserves its output and stops mutation.
- Every detach-based cleanup runs overlay-declared post-cleanup checks before branch deletion, session persistence, deploy, release, or closeout; failure preserves the detached checkout and stops remaining mutation.
- Merge runs via rebase merge followed by the worktree-safe manual branch deletion in `<merge_cleanup>` (`gh pr merge --rebase --delete-branch=false`, then detach this worktree onto the refreshed base and delete the local and remote branches separately) unless the overlay declares a different command or opts into inline `--delete-branch` — merge commit and squash are overlay opt-ins (overlay rationale documents the choice for human reviewers; Claude does not enforce it), not Claude's choice from the gate alone.
- The lifecycle runs from the determined changeset autonomously when the overlay declares no pre-mutation confirmation; when the overlay opts in, the structured-question plan presentation precedes the first mutating action and Claude waits for confirmation.
- Each pass that does not fire an autonomous action emits exactly one token from `<action_tokens>`, except a base-sync conflict, which stops with `/sync-base`'s structured conflict report and active rebase state.
- No `<self_reference>` violation appears in any artifact.

</success_criteria>
===== END PRODUCER: src/plugins/spec-tree/skills/merging-standards/SKILL.md =====

===== BEGIN PRODUCER: spx/local/merging.md =====
# Marketplace Merge Rules

Loaded by `/merging-standards` `<repo_local_overlay>` and `/merge`. The product-specific values the merge skills read; the gates, transport selection, and protocols are injected by those skills.

## Deployment and release recognition

No deployment action is declared. Every change proceeds without deployment authorization. Release is declared as the marketplace-source refresh in the release marketplace sync section, governed by `RELEASE_READINESS`; the command owns distribution-change detection. Never ask the operator whether to merge.

## Canonical checkout safety

Run the released default diagnosis before the first merge mutation, without a manifest. `@outcomeeng/spx` 0.6.15 and newer select every registered diagnostic provider when neither a manifest nor a configured check set is supplied, so the default machine report includes `worktree-pool`; the plugin-shipped manifest remains the fully instrumented contract for the user-invoked `/diagnose` skill:

```bash
git rev-parse --show-toplevel
just marketplace-source-root outcomeeng
spx diagnose --format json
```

Inspect the JSON record whose `name` is `worktree-pool`; do not gate on the aggregate exit code or `overall`, because an independent check may degrade the aggregate. The preflight holds only when all of these predicates are true:

- the report is valid JSON and contains exactly one `worktree-pool` record;
- that record's `verdict` is `compliant`;
- `readings.mainCheckoutPath` is a non-empty absolute path;
- the absolute marketplace-source path from `just marketplace-source-root outcomeeng` equals `readings.mainCheckoutPath`;
- `readings.mainCheckoutBranchRead` is `true`;
- `readings.mainCheckoutBranch` equals `readings.defaultBranch`;
- the assigned worktree root from `git rev-parse --show-toplevel` differs from `readings.mainCheckoutPath`.

Stop before mutation and report the record verbatim when any predicate fails. A missing, detached, wrong-branch, unreadable, or marketplace-source-mismatched designated main checkout therefore blocks the lifecycle, as does an assigned worktree that is itself the designated main checkout. The merge lifecycle never switches, detaches, or performs feature-branch cleanup in the designated main checkout. The release phase may access that checkout only through the explicit `git -C "$src"` fast-forward commands below after the preflight has established its identity and branch standing.

After detach-based feature-worktree cleanup, run `spx diagnose --format json` again and require the same `worktree-pool` health predicates. At that point the assigned feature worktree may be detached, while the designated main checkout must remain readable and attached to the resolved default branch.

## Merge command

Use a merge commit (the product's `main` history style), not the default rebase:

```bash
gh pr merge <pr-number> --merge --delete-branch=false
```

`--delete-branch=false` is explicit because `gh`'s default for the omitted flag is unknowable across environments and its local-cleanup step fails in this multi-worktree checkout. Remote branch deletion remains a separate cleanup action after the post-cleanup diagnosis below passes.

## Post-merge feature-worktree cleanup

After the canonical-checkout preflight proves that the assigned worktree is a distinct feature worktree, detach that feature worktree onto the merged commit, repeat the complete diagnostic predicate set, and only then delete the remote feature branch:

```bash
git fetch origin main
git switch --detach origin/main
git rev-parse --show-toplevel
just marketplace-source-root outcomeeng
spx diagnose --format json
```

Stop and inspect the post-cleanup `worktree-pool` record and both path command outputs under the canonical checkout safety predicates. A failed check leaves the feature worktree detached and the remote branch intact for inspection. Only after every predicate passes, run:

```bash
git push origin --delete <branch>
```

## Deterministic verification commands

The touched-scope principle is `/merging-standards` `<local_deterministic_scope>`; these are this repository's commands per scope:

- Spec-only (specs, decisions, coordination notes, Markdown): `spx validation markdown` and `spx spec status --format json`.
- Skill/doc Markdown under `src/plugins/` or `dist/`: `just check-skills` and `just docs-check`.
- Implementation, test, validation-config, or broad changes: the focused node/package/module tests plus the narrow validation lane that covers the changed files, widening to full `just check-full` for shared validation/test infrastructure, package-manager files, generated catalog output, or distribution build machinery.

When the full `just check-full` bundle is required, it is the terminal local deterministic gate. Run the focused lane first, then all applicable evidence auditors and agentic reviews to convergence, then run `just check-full` once against the clean committed head. Never run `just check-full` before those agentic checks, inside an agent, or concurrently with another heavy command. Any change after it invalidates the result and reopens the affected agentic gates before the next full-gate run.

## Pull request opening

Before opening a pull request, verify these marketplace predicates in addition to the shared branch-hygiene and readiness gates:

| Check                                                                                             | If failing                                                           |
| ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| The touched-scope deterministic verification selected by this overlay and root `AGENTS.md` passes | STOP. Fix the failing touched-scope lane first.                      |
| Plugin manifest version bumped when the change warrants it                                        | STOP. Bump per `spx/local/commit-changes.md`.                        |
| Both marketplace catalogs updated when adding or removing a plugin                                | STOP. Run the catalog or manifest command named by root `AGENTS.md`. |
| `README.md` skill and thin-agent catalog updated to match the change                              | STOP. New or removed artifacts must appear in the catalog.           |
| `update-instruction-block/templates/instruction-block.md` updated when skill structure changes    | STOP. New projects inherit this template.                            |

Append these sections to `/open-pr`'s default body template:

```text
## Versioning

- <plugin>: <old> → <new> (<MAJOR | MINOR | PATCH>)

## Validation

- [ ] Touched-scope deterministic verification passes
- [ ] `/reload-plugins` confirms the change loads in a running session
```

Drop the **Versioning** section only when no `plugin.json` files changed.

## Governance surfaces (base-sync review reuse)

A prior local review is reusable across a clean rebase only when the branch patch is unchanged **and** no base-delta path is a governance surface: `AGENTS.md`, `CLAUDE.md`, any `spx/local/*.md`, the bundled review prompt at `src/plugins/spec-tree/skills/review-changes/references/review-prompt.md`, or any standards reference under `src/plugins/*/skills/*-standards/` or `src/plugins/*/skills/**/SKILL.md`.

## Mention-reviewer trigger phrase

`@spec-tree` (configured in `.github/workflows/spec-tree-review.yml` `trigger_phrase`; repository-variable override `SPEC_TREE_REVIEW_TRIGGER_PHRASE`).

## Release marketplace sync

The Claude marketplace is registered as a **Directory source** at the authoritative default-branch worktree — the checkout named like the remote (for example `~/Code/outcomeeng/plugins/plugins`), which stays on branch `main`. That worktree's `dist/` is what every Claude session and `claude plugin marketplace update` reads, so the marketplace serves current content only when **that worktree's `main` is current**.

After a merge lands on `origin/main`, fast-forward the **marketplace-source worktree's** `main`, then refresh installs:

```bash
src=$(just marketplace-source-root outcomeeng)
git -C "$src" fetch origin main
git -C "$src" merge --ff-only origin/main   # the source worktree is on main; fast-forward it to the merged tip
(cd "$src" && just sync-marketplace <previous-main-ref>)   # run FROM the source worktree
```

`just sync-marketplace` must run from the source worktree: its `validate_install` reads `current_versions` from its own working directory, so a feature worktree behind `origin/main` false-fails against stale versions. A PR that changes no plugin-distribution files leaves `dist/` unchanged, so the refresh is skipped, but the source `main` is still fast-forwarded so it never drifts. If `merge --ff-only` fails, the source worktree carries unexpected local commits — move them onto a feature branch (never `reset --hard`), then re-run.
===== END PRODUCER: spx/local/merging.md =====
The changeset and overlay state (JSON-encoded):

```json
{input_json}
```
