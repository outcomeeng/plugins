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

<reference_note>
This is a reference skill. /merge, /manage-github-pr, /open-pr, and /manage-pr load this vocabulary automatically. Do not invoke directly.
</reference_note>

<repo_local_overlay>
When loaded inside a repository, check for `spx/local/merging.md` at the repository root. Read it after this reference if present and apply it as the repo-local specialization; a local overlay supplements skill behavior and does not declare product truth.

`spx/local/merging.md` is a **conditional read** and an **optional file**: read it only when it exists, and treat its absence as normal — never a missing-state error or a blocker. When it is absent, the defaults in this reference apply and the lifecycle proceeds unchanged. It is the one place repository-specific merge behavior (transport, readiness, confirmation, merge command, preview actions, deployment actions, and release actions) belongs. When the overlay is absent, NEVER reconstruct the transport or any merge behavior from incidental repository docs — invoke `/merge` and let the lifecycle apply the defaults — and NEVER edit a generated guide (`CLAUDE.md`) to change merge behavior; the authored skills and this overlay are the only surfaces that govern it.

Topics the overlay MAY refine:

- Extra pre-flight checks beyond `<branch_hygiene>`.
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
- Whether the local branch tracks a gone upstream.
- Whether any preservation branch was created.
- For each preservation branch, whether its commits are exact ancestors of `origin/<base>`.
- For each non-ancestor preservation branch, `git cherry -v --abbrev=40 origin/<base> <branch>` output as patch-equivalence evidence.
- Final worktree state: clean or dirty, branch or detached, and current full HEAD SHA.
- Release-source worktree state when a declared release or marketplace refresh used a separate source worktree: path, branch, full HEAD SHA, clean or dirty, and sync status.

Use full branch names and full commit SHAs. Do not abbreviate identity values in the record, in commands, or in the final closeout.

Safe cleanup policy:

- If the remote feature branch exists after merge, delete it through the merge lifecycle's approved deletion command.
- If the local feature branch exists, tracks a gone upstream, and is fully merged into `origin/<base>`, delete it locally.
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

If the product defines a custom branch-push command, follow the product convention from CLAUDE.md — the explicit destination ref must remain part of any custom command.

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

The local `changes-reviewer` gate is the author-side, pre-push instance of the same review kind the CI review runs post-push — the two are the same class of gate on opposite sides of each push. Invoke it the way CI invokes its reviewer, passing nothing that narrows it:

- **Let the review resolve its own scope.** `changes-reviewer` self-discovers the worktree it runs in and computes the diff itself. The caller makes the base explicit only when the changeset's base is not `origin/HEAD` (a stacked PR), and passes nothing else — no file list, no changed-area summary, no "the important part is …".
- **Add no interpretive scope.** Do not tell the reviewer which layers, files, or concerns to weight. It reviews the whole diff against the whole taxonomy.
- **Add no severity pre-filter.** Do not ask only for `BLOCKING`, do not suppress `DEBT`. The reviewer emits every finding; handling is by validity and phase per `<review_classification>`, downstream of the review and never inside its invocation.
- **Add no emphasis steering.** Do not tell the reviewer what to conclude or what matters most. It reads the repository's own instructions (CLAUDE.md and the standards skills) and the shared taxonomy itself.

Run it via the `changes-reviewer` agent. The isolated context keeps the verdict from being biased by what the operator's main context has been doing. Iterate to convergence: each round, act on findings by validity and phase per `<review_classification>`, until no valid finding remains unaddressed.

This is the review predicate `VERIFICATION_READINESS` reads, and it runs before every push — the opening push (`/open-pr`) and every follow-up push (`/manage-pr`), against the diff that push would publish. Narrowing the invocation diverges the local gate from the CI reviewer it parallels, so its convergence no longer means what `VERIFICATION_READINESS` claims it means.

</local_review_invocation>

<authority_gates>

The delivery lifecycle runs `VERIFY -> PREVIEW -> MERGE -> DEPLOY -> RELEASE -> CLOSE` with four gates, evaluated in order: `VERIFICATION_READINESS`, `MERGE_READINESS`, `DEPLOYMENT_READINESS`, and `RELEASE_READINESS`. A **gate** is a named authorization over one lifecycle step, decided from defined predicates; a **predicate** is a condition a gate reads — predicates are never themselves gates. `/open-pr` evaluates the GitHub-PR transport's `VERIFICATION_READINESS` predicates before publishing; `/manage-pr` evaluates `MERGE_READINESS` for the current head, then continues through declared `DEPLOYMENT_READINESS` and `RELEASE_READINESS` phases after merge.

**`VERIFICATION_READINESS`** authorizes publishing the verified changeset to the selected transport. For the GitHub-PR transport, it authorizes opening the PR. It holds when all predicates hold:

- **deterministic verification passes** — the project's local validation and testing commands for the touched scope per `<local_deterministic_scope>` report success. A failing touched-scope test means this predicate does not hold, including a TDD-red opener authored intentionally ahead of an implementation slice. The remedy is either land the implementation in the same PR so the test passes, or add the owning node to the project's spec-tree EXCLUDE mechanism (for example `spx/EXCLUDE`) so the test runner skips the node until implementation arrives. See `references/excluded-nodes.md` in `/understand`. Per-line suppression (`# noqa`, `# type: ignore`, `@pytest.mark.skipif`, `@pytest.mark.xfail`, equivalents in other languages) does not satisfy this predicate because those suppressions are scattered and invisible to the spec-tree status surface; and
- **required evidence audits have passed** — when the diff creates or modifies `[test]` assertions, linked test files, or test-infrastructure artifacts imported by linked tests, dispatch `test-evidence-auditor`; when the diff creates or modifies `[eval]` assertions, eval artifacts (`eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`), or producer artifacts for eval-backed assertions, dispatch `eval-evidence-auditor`. Run the applicable evidence auditors after deterministic verification passes and before `changes-reviewer`. Handle rejected, failing, or unknown evidence-auditor verdicts per `<auditor_verdicts>`; and
- **the local review has converged** — `changes-reviewer`, invoked at parity per `<local_review_invocation>` and iterated to convergence, leaves no valid finding unaddressed: each is fixed in the diff, or split out of the changeset and captured in the owning node's `ISSUES.md` / `PLAN.md`. An unbacked finding is dropped.
- **the terminal full deterministic gate has passed when required** — `just check-full` ran after every applicable evidence audit and agentic review converged, against the current clean committed head, with no subsequent change and no concurrent heavy command.

The moment `VERIFICATION_READINESS` holds, the PR is created `ready_for_review` — never draft (a stacked PR is the one exception, held draft per `<branch_topology>` until its base merges). There is no draft phase and no gated promotion; opening ready fires every CI review at once (reviewers that wait for ready, such as Codex, alongside the CI review). A declared `PREVIEW` action then runs before `MERGE_READINESS`; absent preview declaration means `PREVIEW` is a no-op and never blocks merge.

All `VERIFICATION_READINESS` predicates are re-established before every push, not only the opening push. A follow-up push that changes the branch's own content — a fix for a CI finding — re-runs local deterministic verification per `<local_deterministic_scope>`, re-runs any evidence-auditor predicate whose touched evidence surface changed, and re-runs the local review per `<local_review_invocation>` on the new diff before it is pushed. A follow-up push that **only** rebased onto an advanced base re-establishes the predicates scoped by the `<base_sync>` preservation proof — reusing the local review and evidence-auditor verdicts when the branch diff is unchanged and the base movement does not touch the governed evidence surface, and running a narrower local validation/testing lane when the proof and the project overlay permit — rather than always re-running every predicate in full. Either way, the author-side evidence audits and review precede the push that fires CI, so a follow-up diff never reaches CI without author-side agentic verification first.

**`MERGE_READINESS`** authorizes merge. It holds when all predicates hold, every one decidable from observable PR state:

- a clean current-head CI review exists — the review-kind output for the current head, read from the surfaces in `<review_inspection>`, complete and valid, that reports **no unresolved `BLOCKING` or `DEBT` finding** — stated directly per the reviewer's no-`BLOCKING`-or-`DEBT` convention, or with **every** such finding individually assessed and dropped as unbacked; a `DEBT` finding the author tracks out of scope with a recorded reason is not unresolved (validity per `<review_classification>`; a valid in-scope `BLOCKING`/`DEBT` finding is unresolved work Claude fixes before merge). When multiple reviewers or review surfaces comment on the same head, the review predicate reads the union of current-head findings: a no-findings review from one reviewer never cancels a valid finding from another reviewer, and a required-check success never cancels a valid finding posted as a PR comment or review-thread comment. The absence of a current-head review is never clean — it is `WAIT_FOR_REVIEW`;
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

**Acting on findings (validity and phase, never severity).** Claude acts on each finding by **validity** — whether it holds against its cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions; read those fresh and drop a finding they do not support — and by **phase**: before open (`VERIFICATION_READINESS`) apply every valid finding that belongs and split out of the changeset only a fix too large to belong — a separate, larger concern (its own node or feature), never a bounded fix such as a rename propagation, a cross-reference update, or a mechanical change — the split work leaves the diff and is captured in `ISSUES.md` / `PLAN.md`; on the open PR (`MERGE_READINESS`) fix every valid finding whose fix belongs in the changeset and re-push, with no deferral of in-scope work — a bounded fix is in-scope work the changeset carries, never deferred — while a `DEBT` finding the author judges a separate, larger concern is recorded in `ISSUES.md` / `PLAN.md` with a reason naming why it is large and tracked, not a merge blocker. Severity is the reviewer's reporting label; validity and scope (never the label) decide whether and how Claude acts on a finding, and the reviewer never decides whether the change merges.

**Same-class sweep.** A valid review or audit finding is evidence of a defect class, not only the cited line. Before the next push, inspect the touched node(s) — the files they govern — for parallel instances of the same defect: same rule, same source contract, same evidence pattern, same lifecycle step, or same generated-source relationship. Fix every in-scope parallel instance in the same bounded changeset. If the sweep proves the cited instance isolated, record that conclusion in the review/audit handling summary. A one-line patch that only satisfies the cited example is incomplete until this sweep is done.

**Reviewer disagreement and repeated rounds.** A clean review, passing required check, approved audit, or "no findings" comment is evidence about that reviewer or verifier's scope only; it does not invalidate a separate current-head finding that is backed by its cited rule and governance. Repeated valid findings in the same lifecycle area — each exposing a deeper variant of the same source contract, state transition, crash path, idempotency boundary, artifact lifecycle, or other defect class — mean the defect class is still open. Widen the same-class sweep, repair the underlying contract, and re-run the author-side review before the next push. Never convert that pattern into a "stuck gate" stop, operator call, or merge allowance. A path being foundational, not yet consumed by production code, behind a deferred downstream slice, or covered by other clean gates does not change finding disposition: if the changed diff carries the failure mode and the finding is valid in scope, fix it in the changeset or remove/split the capability so the diff no longer carries it.

**Reviewer-skipped-by-design (self-modifying-PR exception).** When the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate), no current-head review exists for `MERGE_READINESS`. Post one PR-level comment containing exactly `<trigger-phrase> review` (e.g., `@spec-tree review`) to fire the mention reviewer (which has no identical-content gate), emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run `<pr_check_wait>`, and on the next management pass treat that reviewer's posted findings as the current-head review. This applies to that skip cause only — not path-filter, branch-filter, or manual skips.

**Follow-up pushes.** The PR is ready from open; a follow-up push — fixing a valid CI finding, or a `<base_sync>` rebase — pushes to the ready PR and re-fires CI. There is no draft toggle and no `gh pr ready` step in the loop.

</authority_gates>

<merge_cleanup>

Once `MERGE_READINESS` authorizes the merge and the mutation-point guard has produced `MERGE_READY:<head-sha>`, Claude merges and then deletes the branch. Cleanup of the changeset's branch is scoped to the assigned worktree per `<assigned_cwd_worktree_discipline>` — Claude NEVER detaches, cleans, or deletes a branch in a worktree a live agent holds; if the merged branch is checked out in such a worktree, it is left untouched. The universal default — used whenever the overlay declares no merge command — is rebase merge with an explicit **`--delete-branch=false`**, followed by a worktree-safe manual deletion:

```bash
base_from_pr=$(gh pr view <pr-number> --json baseRefName --jq '.baseRefName')
branch_from_pr=$(gh pr view <pr-number> --json headRefName --jq '.headRefName')
gh pr merge <pr-number> --rebase --delete-branch=false
git fetch origin "$base_from_pr"
git switch --detach "origin/$base_from_pr"   # step this worktree off the merged branch onto the new base tip
held_worktree=$(git worktree list --porcelain | awk -v branch="refs/heads/$branch_from_pr" '/^worktree /{path=substr($0,10)} $0=="branch " branch{print path; exit}')
if [ -n "$held_worktree" ]; then echo "Local branch kept: path=$held_worktree branch=$branch_from_pr"
elif [ -n "$(git branch --list "$branch_from_pr")" ]; then git branch -D "$branch_from_pr"; fi
remote_branch_status=0
git ls-remote --exit-code --heads origin "$branch_from_pr" >/dev/null || remote_branch_status=$?
case "$remote_branch_status" in
  0) git push origin --delete "$branch_from_pr" ;;
  2) ;;
  *) exit "$remote_branch_status" ;;
esac
git status --porcelain
```

Order matters: merge while the branch is still checked out — `gh pr merge` fails with "could not determine current branch" from a detached HEAD even with an explicit PR number — then detach this worktree, then delete the local branch, then delete the remote branch unless the host already auto-deleted it.

**Why the default passes `--delete-branch=false` explicitly.** `gh pr merge --delete-branch` — or the bare flag where a `gh` version or config defaults it on — run from the worktree on the branch being merged, makes `gh` switch that worktree to the base branch as part of deleting the local branch. In a multi-worktree checkout where the base (for example `main`) is checked out in another worktree, that switch fails with `fatal: '<base>' is already used by worktree at <path>` — the merge completes on the host, but the local branch is left undeleted and the flow ends in an error state. Omitting the flag is not enough: this methodology ships to consumer environments whose `gh` default for the omitted flag is unknowable, so the default states `--delete-branch=false` explicitly, guaranteeing `gh` never attempts that switch regardless of environment. Deliberate deletion stays in the worktree-safe manual sequence above, which behaves identically in single- and multi-worktree checkouts and tolerates a host that already auto-deleted the remote branch. A project that is always single-worktree MAY opt the overlay into inline `gh pr merge --rebase --delete-branch` per `<repo_local_overlay>`.

The merge flag follows the overlay when it declares one (`--merge` or `--squash`); `--rebase` is the universal default flag. The deletion steps after the merge are independent of which merge flag runs.

</merge_cleanup>

<step name="pr_check_wait">
<pr_check_wait>

Waiting for PR checks or the current-head CI review uses exactly one foreground command:

```bash
gh pr checks <pr-number> --watch --fail-fast --interval 30
```

After that command exits, immediately run the full managing inspection again before acting: PR state, check rollup, PR-level comments, formal reviews, and review-thread comments. This is the only PR-check wait path in the GitHub-PR lifecycle, applies to both Claude Code and Codex, and never runs in the background.

Forbidden waits: shell `sleep`, `gh run watch`, background keep-alives, and `until`/`while` polling. Never wrap `gh pr checks --watch` in a loop or background it. The Bash tool does not reliably reap detached subprocess trees across turns; fork-bomb-class accumulation results when those patterns are repeated.

</pr_check_wait>
</step>
<step name="review_inspection">
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
</step>
<review_classification>

Every review finding — whether produced by a reviewer (outgoing feedback) or triaged by an author (incoming feedback) — carries two dimensions: **severity** (one of two) and **category** (one of six). The taxonomy is shared so output and triage use the same vocabulary; nothing has to be translated between them.

This skill is the canonical consumer-facing taxonomy. Repositories may add local review instructions, but the default severity and category vocabulary below is complete here.

**Severity** (one of two — the reviewer's reporting label for the finding's merge-safety nature):

| Severity   | Use when                                                                                                 |
| ---------- | -------------------------------------------------------------------------------------------------------- |
| `BLOCKING` | Merge-safety defect: if deployed, the changeset would create a deterministic issue or pose a risk.       |
| `DEBT`     | Real defect that does not jeopardize merge safety: a problem the change carries, but not merge-blocking. |

Severity is the validity judgment the reviewer makes. **Disposition** — whether each `DEBT` finding is fixed in this PR or tracked out of scope — is the author's call, not the reviewer's; the reviewer carries no scope axis. A fix is **in scope** when it is bounded — a rename propagation, a cross-reference update, a mechanical change, or a fix that merely touches another file — and is fixed in the changeset; a finding is tracked out of scope only when its fix is a separate, larger concern (its own node or feature), with a recorded reason naming why it is large. Boundedness is never grounds to defer: a rename, a cross-reference, or a mechanical change is never tracked out of scope.

**A defect the changeset's own edits introduced is always in-scope and is never split out.** A claim an edit made stale, dead code a change orphaned, a cross-reference a rename broke, a spec a consolidation falsified — fixing the consequences of this change is part of this change, however many files the fix touches. "A separate, larger concern" means a node or capability that exists independently of this changeset; it is never a label applied to self-caused bounded work to end a review-convergence loop. If the only thing making a finding feel large is that fixing it would reopen the loop, it is in-scope — converge the loop, do not relabel the work to escape it.

**Handling is by validity and phase, never by severity.** Severity classifies the finding's nature for the reader; it is not a routing key. The consumer of a review validates each finding against its cited rule and the governing decisions, drops any the citation does not support, and acts on the rest by phase per `<authority_gates>`: before open (`VERIFICATION_READINESS`), apply every valid finding that belongs and split out of the changeset any whose fix is too large to belong; on the open PR (`MERGE_READINESS`), fix every valid in-scope finding the CI review surfaces, with no deferral of in-scope work — a bounded fix (a rename, a cross-reference, a mechanical change, a fix that merely touches another file) is in-scope work the changeset carries, never deferred — while a `DEBT` finding whose fix the author judges a separate, larger concern is recorded in `ISSUES.md` / `PLAN.md` with a reason naming why it is large and does not block the merge. A `BLOCKING` label does not force an action the citation does not support, and a `DEBT` label does not exempt a finding whose fix actually belongs in the changeset — validity, phase, and scope decide, and the reviewer never decides whether the change merges.

**Same-class sweep before disposition.** Treat a valid review or audit finding as evidence of a defect class. Before fixing only the cited site, inspect the touched node(s) for parallel instances with the same rule, source contract, evidence pattern, lifecycle step, or generated-source relationship. Fix all in-scope parallel instances in the same changeset, or record in the handling summary that the sweep found the cited instance isolated. Do not run another external review round after a micro-edit that only addresses one example while the defect class remains unswept.

**Cross-reviewer union and convergence.** Build one finding ledger from all current-head review surfaces and reviewers, then classify each item once. A no-findings review from the designated CI reviewer, a clean local review, a passing deterministic check, or an approved audit never cancels a valid finding from another reviewer. Multiple review rounds that keep surfacing valid variants in the same area are not reviewer noise and not an operator decision point; they prove the prior fix or sweep was too narrow. Treat the next valid variant as the same defect class until the underlying lifecycle contract is repaired and a new review round finds no valid in-scope variant. "Not wired into production yet" and "deferred next slice" are not dispositions for code in the diff — if the changed diff carries the defect and the finding is valid in scope, fix it in the changeset before merge.

**Category** (one of six), grouped by three axes:

*What the code does vs. what it is supposed to do*

- `consistency` — disagreement across layers (decisions / PDR / ADR <-> spec <-> tests <-> implementation). Surface the disagreement; do not judge which side is right.
- `security` — confidentiality, integrity, availability.
- `performance` — unbounded loops, hot-path allocations, O(n²) traversals where O(n) suffices, synchronous I/O on async paths, and similar pessimisations that change the changeset's runtime characteristics under realistic load.

*How we know it does what it is supposed to do*

- `evidence` — inadequate coverage of declared assertions by tests or evals; unmaintainable tests (literals, magic numbers, test-owned constants, duplication); evals that no longer exercise the assertions they claim to.

*How it does what it is supposed to do*

- `standards` — adherence to CLAUDE.md and the rules declared in standards skills (naming conventions, command tokens, file structure, language idioms).
- `architecture` — violation of structural principles declared by ADRs or PDRs (layer boundaries, separation of concerns, dependency directions, module-shape rules). A finding is an architecture one when the structure itself is at odds with a governance principle, even if every layer is internally consistent.

**Finding labels.** Both `BLOCKING` and `DEBT` require an action in this PR and use `Reference:` + `Evidence:` + `Required:`.

**No findings: say so directly.** When the changeset has no `BLOCKING` or `DEBT` findings, post a one-line comment saying so. NEVER invent lower-priority findings to prove the review happened.

**Findings only — never open questions, never commentary.** A reviewer with a question frames it as a finding (e.g., "Evidence: cannot verify X from the changeset; if assumption Y holds, this breaks Z because …") rather than asking a question that waits for an answer. Questions add CI roundtrips a single-pass review cannot recover from. Praise, observations, and commentary that do not constitute findings are noise — omit them.

**Forbidden taxonomies.** Severity-rank labels MUST NOT replace the two severities — no `P0` / `P1` / `P2` / `P3`, no `critical` / `high` / `medium` / `low`, no `minor` / `nit` headings. A third scope-shaped severity (`FOLLOW-UP`) MUST NOT reappear — scope is the author's disposition, not a reviewer severity. Risk words may appear inside rationale only when they add concrete evidence, never as a finding's primary label. Legacy class labels `NEEDS-ANSWER` and `NOTE` are forbidden — open questions are reframed as findings; commentary is omitted.

Comment format examples:

```text
### BLOCKING [consistency]: path/to/file:42
Reference: <quote the standard from CLAUDE.md, skills, governance from decisions (PDR/ADR), or assertion from specs>
Evidence: <quote the diff or behavior and explain the disagreement between layers>
Required: <concrete change>
```

```text
### DEBT [standards]: path/to/file:97
Reference: <quote the standard from CLAUDE.md, skills, governance from decisions (PDR/ADR), or assertion from specs>
Evidence: <quote the diff or behavior and explain how it violates the standard>
Required: <concrete change>
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

<self_reference>
No "Claude", "AI", "agent", "Co-Authored-By: Claude", or similar identity strings in any merge-flow artifact: branch names, commit messages, PR titles, PR bodies, review comments.

</self_reference>

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
- Every finding is labeled with one of `BLOCKING` / `DEBT` — never `FOLLOW-UP`, never a severity rank, never a legacy class label — and acted on by validity and phase, never by severity.
- Every auditor verdict from a local auditor agent (per `<auditor_verdicts>`) is handled as an in-slice finding; `REJECTED` or `UNKNOWN` overall verdicts, `FAIL` or `UNKNOWN` rows, and `REJECT` findings are fixed or resolved in the slice, not deferred to `ISSUES.md`.
- Merge runs only when `MERGE_READINESS` holds and the mutation-point guard has just produced `MERGE_READY:<head-sha>`: the current-head CI review has no unresolved valid `BLOCKING` or `DEBT` finding, every other required check is terminal-green, branch hygiene and PR-state hold on the freshly inspected head, and the inspected head SHA matches the fetched remote branch head and status-check head. `MERGE_READINESS` carries no time-based settle.
- A committed changeset ahead of its resolved base is treated as unfinished until it reaches the default branch on origin through the selected lifecycle, or stops at an explicit action-token emission or structured base-sync conflict report with no independent local action remaining.
- Local readiness — clean working tree, committed changes, passing deterministic verification, tests, local review, or audits — is reported as evidence and then carried forward; it is never a reason to ask what to do next.
- `CLOSE` continues in-scope work directly or invokes `/handoff` plain for operator-useful closeout and continuation disposition; a receipt-only response never satisfies the lifecycle.
- No structured question or prose confirmation asks the operator to choose between auto-merge, hold-at-green, or pause; the only operator-facing pauses are explicit `<action_tokens>` emissions and structured base-sync conflict reports.
- The changeset's git work runs in the assigned worktree per `<assigned_cwd_worktree_discipline>` — never in a worktree a live agent holds, no created worktree, no `git stash`; a branch conflict is resolved by branching in the assigned worktree and continuing.
- `spx/local/merging.md` is read only when present, its absence applies the defaults with no blocker, and merge behavior is never reconstructed from incidental docs or changed by editing a generated guide.
- Merge runs via rebase merge followed by the worktree-safe manual branch deletion in `<merge_cleanup>` (`gh pr merge --rebase --delete-branch=false`, then detach this worktree onto the refreshed base and delete the local and remote branches separately) unless the overlay declares a different command or opts into inline `--delete-branch` — merge commit and squash are overlay opt-ins (overlay rationale documents the choice for human reviewers; Claude does not enforce it), not Claude's choice from the gate alone.
- The lifecycle runs from the determined changeset autonomously when the overlay declares no pre-mutation confirmation; when the overlay opts in, the structured-question plan presentation precedes the first mutating action and Claude waits for confirmation.
- Each pass that does not fire an autonomous action emits exactly one token from `<action_tokens>`, except a base-sync conflict, which stops with `/sync-base`'s structured conflict report and active rebase state.
- No `<self_reference>` violation appears in any artifact.

</success_criteria>
