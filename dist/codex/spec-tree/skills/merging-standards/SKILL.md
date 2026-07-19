---
name: merging-standards
user-invocable: false
description: >-
  Merge-lifecycle standards for pre-flight predicates, branch topology, push commands, authority gates, review classification, integration review surfaces, action tokens, delivered-value boundaries, closeout, and repo-local overlays.
allowed-tools: Read
---

<objective>
The shared merge-lifecycle vocabulary — transport-neutral concepts, predicates, gates, commands, and tokens for delivery through closeout.
</objective>

<repo_local_overlay>
When loaded inside a repository, check for `spx/local/merging.md` at the repository root. Read it after this reference if present and apply it as the repo-local specialization; a local overlay supplements skill behavior and does not declare product truth. This reference is the sole merge-lifecycle skill that reads or interprets that file. Resolve each configured topic into the named contract that owns it; protocol skills consume those resolved contracts and MUST NOT discover, read, or interpret the overlay themselves.

`spx/local/merging.md` is a **conditional read** and an **optional file**: read it only when it exists, and treat its absence as normal — never a missing-state error or a blocker. When it is absent, the defaults in this reference apply and the lifecycle proceeds unchanged. It is the one place repository-specific merge behavior (transport, readiness, confirmation, merge command, preview actions, deployment actions, and release actions) belongs. When the overlay is absent, NEVER reconstruct transport or merge behavior from incidental repository docs; apply the defaults. NEVER edit a generated guide (`AGENTS.md`) to change merge behavior; authored lifecycle skills and this overlay are the governing surfaces.

Topics the overlay MAY refine:

- **Safety checks** — preflight checks that run immediately before a lifecycle entry's first checkout-sensitive mutation, and post-cleanup checks that run immediately after detach-based cleanup. See `<overlay_safety_checks>`.
- The project's local deterministic-verification scope for `VERIFICATION_READINESS`: validation and testing commands for the touched scope by default, plus any documented escalation cases that require a wider local run. Full-repository validation and testing are CI's responsibility unless the overlay explicitly requires a local full-repository predicate for a class of change.
- The terminal full deterministic gate: when the overlay requires a local full-repository bundle, its command runs only after all applicable evidence auditors and agentic reviews have converged on the same clean committed head. The full gate runs once at that terminal point, never before agentic verification, inside an agent, or concurrently with another heavy command. Any later change invalidates it and reopens the affected agentic gates before the full gate runs again.
- Push command overrides — the explicit destination ref form must be preserved.
- **Preview declarations** — pre-merge publication, generated preview, dry-run, or inspection actions and their predicates after `VERIFICATION_READINESS` publication and before `MERGE_READINESS`. Absence means `PREVIEW` is a no-op and never blocks merge, deploy, release, or close.
- **Deployment and release declarations** — environment mutation actions and predicates under `DEPLOYMENT_READINESS`, plus consumer-visible publication or refresh actions and predicates under `RELEASE_READINESS`. Absence means `DEPLOY` and `RELEASE` are no-op phases and never block later phases.
- **Pre-mutation confirmation** — whether Claude pauses for operator confirmation before the first mutating action of the lifecycle (branch, commit, push, PR open, direct-push). A project whose operators want to confirm intent before any mutation opts in here; Claude then presents — through the runtime's structured-question tool — the change to make, the branch, the commit shape, and the end-to-end scope from intent through merge, and waits before mutating. A project that wants none declares no setting, and Claude drives the determined changeset from intent to merge autonomously, stating the plan in prose with no structured-question pause. This is an opt-in touch-point ahead of the lifecycle, never a gate; it leaves `VERIFICATION_READINESS`, `MERGE_READINESS`, `DEPLOYMENT_READINESS`, `RELEASE_READINESS`, and the finding-disposition rule unchanged. Establishing *what* to ship when no changeset is determined is requirements work, not this confirmation.
- **Merge command** — rebase merge followed by a worktree-safe manual branch deletion is the universal default; the merge flow runs it unless the overlay opts in to a different command. The merge runs with explicit `--delete-branch=false` (`gh pr merge <pr-number> --rebase --delete-branch=false`), then this worktree detaches onto the refreshed base tip and the local and remote branches are deleted by separate commands — the sequence and its rationale are in `<merge_cleanup>`. The overlay may opt in to merge commit (`--merge`) or squash (`--squash`); merge commits and squashes are not Claude's choice to make from the gate alone. The overlay should document its rationale for human reviewers of the overlay change itself, but rationale is not a runtime predicate Claude enforces — the overlay's declaration is Claude's signal. The overlay MAY opt into inline `gh pr merge --rebase --delete-branch` for projects that are always single-worktree, where `gh`'s post-merge switch-to-base never collides.
- **Mention-reviewer trigger phrase** — the leading phrase Claude posts as a PR-level comment to fire the mention-triggered reviewer when the auto-review job reports `conclusion: skipped` (see `<authority_gates>` reviewer-skipped-by-design exception). The full comment body is `<trigger-phrase> review`; the `review` suffix is the keyword the mention reviewer matches on. Default: `@spec-tree` (the upstream reviewer action's default `trigger_phrase`). A project that configures a non-default `trigger_phrase` in its review workflow declares the matching phrase here.
- **PR-opening specialization** — additional preflights and PR-body sections resolved into `<pr_opening_specialization>`. Absence yields empty lists and leaves the portable opening protocol unchanged.

If `spx/local/merging.md` is absent or silent on a topic, the defaults in this reference apply. Absent preview, deployment, and release declarations make `PREVIEW`, `DEPLOY`, and `RELEASE` no-op phases; `MERGE_READINESS` still requires current-head CI review with no unresolved valid `BLOCKING` or `DEBT` finding, every other required check terminal-green, branch hygiene, and PR state. **Absence of a pre-mutation-confirmation setting means Claude drives the lifecycle autonomously**, with no up-front confirmation pause before the first mutation.

The overlay cannot override the topology state. Once `VERIFICATION_READINESS` holds, a peer PR is created `ready_for_review`; a stacked PR is created draft and stays draft per `<branch_topology>` until its base merges. No other draft phase or gated draft-to-ready promotion exists.
</repo_local_overlay>

<pr_opening_specialization>
Resolve the optional overlay's PR-opening configuration into one contract before `/open-pr` starts publication:

- `additional_preflights` — an ordered list of repository commands or observable predicates, each with its applicability rule and failure handling. Default: empty.
- `required_body_sections` — an ordered list of complete Markdown sections, each with its heading, body template, and applicability rule. Default: empty.

The resolved values are data supplied to `/open-pr`, never instructions for that protocol to read the overlay. Run every applicable `additional_preflights` entry in declared order during the publication preflight, after `VERIFICATION_READINESS` converges and before the push. A failure stops publication with the complete diagnostic preserved.

Compose every applicable `required_body_sections` entry exactly once, in declared order, after the portable `## Changes` section and before the topology-specific `## Stack` section or the portable `## Test plan` / `## Refs` tail. Omit an inapplicable section completely. After creation, verify the observed PR body contains each applicable section exactly once in that order and contains no inapplicable configured section.

The contract MUST NOT weaken any portable readiness predicate, topology rule, upstream-safety check, or required body section. An absent overlay or an overlay silent on PR opening resolves to empty lists and needs no special handling in `/open-pr`.
</pr_opening_specialization>

<overlay_safety_checks>
When `spx/local/merging.md` declares preflight checks, run all of them immediately before the first checkout-sensitive mutation owned by each lifecycle entry: orchestration before branch or commit work, publication before push, direct-push again before default-branch publication, open-PR management after initial read-only inspection and before base sync, finding repair, commit, push, or merge work, and handoff before every detach. `<merge_cleanup>` repeats the checks immediately before the merge command. A failed check stops before mutation with its output preserved.

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
Read \`${SKILL_DIR}/references/branch-and-push.md\` before applying branch-state closeout. Apply its \`<branch_state_closeout>\` contract.
</branch_state_closeout>

<local_deterministic_scope>
Read \`${SKILL_DIR}/references/branch-and-push.md\` before selecting local deterministic scope. Apply its \`<local_deterministic_scope>\` contract.
</local_deterministic_scope>

<assigned_cwd_worktree_discipline>
Read \`${SKILL_DIR}/references/branch-and-push.md\` before checkout-sensitive lifecycle work. Apply its \`<assigned_cwd_worktree_discipline>\` contract.
</assigned_cwd_worktree_discipline>

<branch_hygiene>
Read \`${SKILL_DIR}/references/branch-and-push.md\` before every push. Set its required \`active_base\` and \`publication_phase\` inputs, then apply the \`<branch_hygiene>\` contract. Opening uses \`publication_phase=initial\`; management follow-ups use \`publication_phase=follow-up\`.
</branch_hygiene>

<branch_topology>
Read \`${SKILL_DIR}/references/branch-and-push.md\` before classifying or transitioning PR topology. Apply its \`<branch_topology>\` contract.
</branch_topology>

<push_semantics>
Read \`${SKILL_DIR}/references/branch-and-push.md\` before every push. Apply its \`<push_semantics>\` contract.
</push_semantics>

<base_sync>
Read \`${SKILL_DIR}/references/branch-and-push.md\` before synchronizing a lifecycle base. Apply its \`<base_sync>\` contract.
</base_sync>

<local_review_invocation>
Read \`${SKILL_DIR}/references/branch-and-push.md\` before dispatching the local changeset review. Apply its \`<local_review_invocation>\` contract.
</local_review_invocation>

<authority_gates>
Read \`${SKILL_DIR}/references/readiness-and-review.md\` before evaluating or applying any lifecycle gate. Apply its \`<authority_gates>\` contract.
</authority_gates>

<merge_cleanup>
Read `${SKILL_DIR}/references/merge-cleanup.md` immediately before the merge mutation. It defines the merge command, overlay checks, worktree transition, and remote and local branch cleanup sequence.

</merge_cleanup>

<pr_check_wait>
Read \`${SKILL_DIR}/references/readiness-and-review.md\` before waiting for PR checks. Apply its \`<pr_check_wait>\` contract.
</pr_check_wait>

<review_inspection>
Read \`${SKILL_DIR}/references/readiness-and-review.md\` before inspecting PR review state. Apply its \`<review_inspection>\` contract.
</review_inspection>

<review_classification>
Read \`${SKILL_DIR}/references/readiness-and-review.md\` before classifying or disposing of findings. Apply its \`<review_classification>\` contract.
</review_classification>

<auditor_verdicts>
Read \`${SKILL_DIR}/references/readiness-and-review.md\` before handling an auditor verdict. Apply its \`<auditor_verdicts>\` contract.
</auditor_verdicts>

<action_tokens>
Read `${SKILL_DIR}/references/action-tokens.md` before emitting a merge lifecycle action token. The reference defines `WAIT_FOR_CHECKS`, `WAIT_FOR_REVIEW`, `FIX_FINDING:<item>`, `MENTION_REVIEW_NEEDED:<trigger-phrase>`, `MERGE_BLOCKED:<reason>`, `AWAIT_DEPLOYMENT_AUTHORIZATION`, and `AWAIT_RELEASE_AUTHORIZATION`, including the exact trigger condition and required follow-up for each token.
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
How to avoid: Follow `${SKILL_DIR}/references/merge-cleanup.md`: remove the remote ref first, prove the local tip is an ancestor, and use `git branch -d`.

**Failure 3: Claude let `gh pr merge` clean up the branch.**
What happened: Claude delegated local cleanup to the host CLI.
Why it failed: Host or CLI behavior can switch onto a base held by another worktree and fail after merging.
How to avoid: Pass `--delete-branch=false`, then run the explicit cleanup sequence.

</failure_modes>

<success_criteria>
The flows that consume this vocabulary satisfy their contracts when, at minimum:

- `<branch_hygiene>` predicates hold before every push with the correct `publication_phase`; only the duplicate-open-PR predicate is initial-publication-specific.
- `<branch_topology>` is classified before every push, with the matching gate passing.
- Every push uses the explicit destination ref form from `<push_semantics>`.
- A managing-flow pass that finds the branch behind `origin/<base>` rebases it per `<base_sync>` before driving the work queue.
- The PR opens `ready_for_review` once `VERIFICATION_READINESS` holds — local deterministic verification per `<local_deterministic_scope>` passes, every required evidence-auditor predicate has passed, the local review has converged, and the terminal full deterministic gate has passed on that clean committed head when required — with no draft phase as a gating mechanism (a stacked PR held draft per `<branch_topology>` is the one exception).
- All `VERIFICATION_READINESS` predicates — local deterministic verification per `<local_deterministic_scope>`, required evidence-auditor predicates, a converged local review, and the terminal full deterministic gate when required — are re-established on the diff every push publishes: the opening push and every content-changing follow-up push; a push that only rebased onto an advanced base re-establishes the reusable predicates scoped by the `<base_sync>` preservation proof, then runs the terminal full deterministic gate on the resulting clean committed head when required.
- The local `changes-reviewer` gate is invoked per `<local_review_invocation>` — the review resolves its own scope, with no interpretive scope, severity pre-filter, or emphasis steering added.
- Waiting for CI review or checks uses the exact PR-check wait command from `<pr_check_wait>`.
- All three surfaces in `<review_inspection>` are inspected after every push, with `comments` always present in the `gh pr view --json` field list.
- Every finding is labeled with one of `BLOCKING` / `DEBT` — never `FOLLOW-UP`, never a severity rank, never a legacy class label — and acted on by validity and phase, never by severity.
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
