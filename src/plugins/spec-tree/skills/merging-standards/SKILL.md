---
name: merging-standards
user-invocable: false
description: >-
  Shared vocabulary for the merge lifecycle — pre-flight predicates, branch topology gate, push command, the three authority gates (review / merge / production readiness), review classification, integration review surfaces, action tokens, delivered-value boundary, and repo-local overlay topics.
  Loaded by /merge, /manage-github-pr, /open-pr, and /manage-pr.
allowed-tools: Read
---

<objective>
Defines the concepts, predicates, gates, commands, and tokens shared by the merge lifecycle — /merge as dispatcher, /manage-github-pr as router, /open-pr as the one-shot opening protocol, and /manage-pr as the open-PR managing protocol. Carries no flow itself; ships vocabulary only.
</objective>

<reference_note>
This is a reference skill. /merge, /manage-github-pr, /open-pr, and /manage-pr load this vocabulary automatically. Do not invoke directly.
</reference_note>

<repo_local_overlay>
When loaded inside a repository, check for `spx/local/merging.md` at the repository root. Read it after this reference if present and apply it as the repo-local specialization; a local overlay supplements skill behavior and does not declare product truth. Topics the overlay MAY refine:

- Extra pre-flight checks beyond `<branch_hygiene>`.
- The project's full deterministic-verification command (validation and testing) that `REVIEW_READINESS` runs.
- Push command overrides — the explicit destination ref form must be preserved.
- **Production-relevance recognition** — the mechanism by which the project classifies a change as production-relevant (label, branch prefix, file pattern, manifest declaration). A production-relevant change reaches `MERGE_READINESS` autonomously but executes only after explicit operator approval (`PRODUCTION_READINESS`). A project that wants a human in the loop for every merge declares every change production-relevant; a project that wants none declares no mechanism.
- **Pre-mutation confirmation** — whether Claude pauses for operator confirmation before the first mutating action of the lifecycle (branch, commit, push, PR open, direct-push). A project whose operators want to confirm intent before any mutation opts in here; Claude then presents — through the runtime's structured-question tool — the change to make, the branch, the commit shape, and the end-to-end scope from intent through merge, and waits before mutating. A project that wants none declares no setting, and Claude drives the determined changeset from intent to merge autonomously, stating the plan in prose with no structured-question pause. This is an opt-in touch-point ahead of the lifecycle, never a fourth gate; it leaves `REVIEW_READINESS`, `MERGE_READINESS`, `PRODUCTION_READINESS`, and the finding-disposition rule unchanged. Establishing *what* to ship when no changeset is determined (the `/manage-github-pr` Empty-mode interview) is requirements work, not this confirmation.
- **Merge command** — rebase merge followed by a worktree-safe manual branch deletion is the universal default; the merge flow runs it unless the overlay opts in to a different command. The merge runs with explicit `--delete-branch=false` (`gh pr merge <pr-number> --rebase --delete-branch=false`), then this worktree detaches onto the refreshed base tip and the local and remote branches are deleted by separate commands — the sequence and its rationale are in `<merge_cleanup>`. The overlay may opt in to merge commit (`--merge`) or squash (`--squash`); merge commits and squashes are not Claude's choice to make from the gate alone. The overlay should document its rationale for human reviewers of the overlay change itself, but rationale is not a runtime predicate Claude enforces — the overlay's declaration is Claude's signal. The overlay MAY opt into inline `gh pr merge --rebase --delete-branch` for projects that are always single-worktree, where `gh`'s post-merge switch-to-base never collides.
- **Mention-reviewer trigger phrase** — the leading phrase Claude posts as a PR-level comment to fire the mention-triggered reviewer when the auto-review job reports `conclusion: skipped` (see `<authority_gates>` reviewer-skipped-by-design exception). The full comment body is `<trigger-phrase> review`; the `review` suffix is the keyword the mention reviewer matches on. Default: `@spec-tree` (the upstream reviewer action's default `trigger_phrase`). Each consuming project that configures a non-default `trigger_phrase` in its reviewer caller workflow declares the matching phrase here.

If `spx/local/merging.md` is absent or silent on a topic, the defaults in this reference apply. **Absence of a production-relevance recognition mechanism means every change is treated as not production-relevant**, so `PRODUCTION_READINESS` holds and the merge executes on `MERGE_READINESS` alone. The other `MERGE_READINESS` predicates (current-head CI review with no unresolved valid `BLOCKING` or `DEBT` finding, every other required check terminal-green, branch hygiene, PR-state) still apply. **Absence of a pre-mutation-confirmation setting means Claude drives the lifecycle autonomously**, with no up-front confirmation pause before the first mutation.

The overlay cannot override the open-ready mandate — once `REVIEW_READINESS` holds the PR is created `ready_for_review`. There is no draft phase and no gated draft-to-ready promotion; a stacked PR is the one exception, held draft per `<branch_topology>` until its base merges.
</repo_local_overlay>

<delivered_value_boundary>

For changes destined for a repository's default branch, value is delivered only when the selected merge lifecycle reaches the default branch on origin. A branch with committed changes ahead of its resolved base is unfinished even when the working tree is clean and deterministic verification, tests, local review, or audits have passed. Those signals are progress evidence for `REVIEW_READINESS` and later gates, never completion.

When a status assessment finds a determined changeset with commits ahead of its resolved base, Claude reports the evidence it found and continues through the merge lifecycle unless the user explicitly limited the task to proposal, review, analysis, or local-only work, or the lifecycle emits an explicit `<action_tokens>` stop with no independent local action remaining. Terse follow-ups such as "so?", "continue", "ship it", "finish", and "go on" mean continue the already-governed lifecycle.

</delivered_value_boundary>

<branch_hygiene>

Conditions that must hold before every push (initial or follow-up). Failure stops the calling flow.

| Condition (must hold)                                        | Failure response                                                      |
| ------------------------------------------------------------ | --------------------------------------------------------------------- |
| Current branch is not `main`, `master`, or detached HEAD     | STOP. Switch to a feature branch.                                     |
| Working tree is clean (no uncommitted changes)               | STOP. Commit via /commit-changes or stash before pushing.             |
| Branch is at least one commit ahead of the resolved base     | STOP. Confirm the base branch — there is nothing to PR.               |
| Branch is not behind the resolved base (no upstream commits) | Rebase onto `origin/<base>` per `<base_sync>`, then re-run this gate. |
| Branch topology is classified as peer or stacked             | STOP. Apply `<branch_topology>` before continuing.                    |
| Work branch is not tracking the default branch               | STOP. Replace the upstream before pushing.                            |
| No PR already exists for this branch (initial push only)     | STOP. Surface the existing PR URL via `gh pr view --json url`.        |
| `gh auth status` reports an authenticated token              | STOP. Resolve auth before continuing.                                 |

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

Identify the previous stack branch from context: the PR description's `Stack` / `Merge order` note, the branch-naming convention, or an explicit user instruction. If none of those yields a ref, invoke `AskUserQuestion` rather than guess.

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

If the product defines a custom branch-push command, follow the product convention from CLAUDE.md / AGENTS.md — the explicit destination ref must remain part of any custom command.

</push_semantics>

<base_sync>

Base drift is checked on the same checkpoint that inspects reviews — every management pass reads review state and the `origin/<base>` position together. When the branch is behind `origin/<base>`, rebase immediately, independent of whether a review has landed and independent of whether any landed review carries findings.

Claude NEVER asks the operator whether to rebase. A behind-base branch is rebased automatically — base-sync is a mechanical consequence of observable git state, not a decision to surface. The only operator touch-point in base-sync is a conflict Claude cannot resolve autonomously, which emits `SYNC_BASE` per `<action_tokens>`; a rebase that applies cleanly runs to completion with no operator interaction. Surfacing "should I rebase?" through a structured question or in prose is a defect.

Rebase on drift, not at merge time. A branch behind base is superseded by a rebase before it can merge, so every check run and every review posted against the un-rebased head is wasted effort. Rebasing the moment drift appears aims CI and reviewers at the head that will actually merge, and surfaces a conflicted ("nasty") rebase early during review/check convergence instead of at merge time, where an unexpected conflict or an integration regression costs a full extra review round on the critical path.

`<base_sync>` reads `${base}` from the calling flow rather than re-deriving it — /manage-pr Step 1 captures it from `gh pr view --json baseRefName` (which returns the PR's actual base for both peer and stacked topologies), and /open-pr's `<branch_hygiene>` sets it from `gh repo view --json defaultBranchRef` before any PR exists. The block runs identically in both contexts.

```bash
git fetch origin "${base}"
git merge-base --is-ancestor "origin/${base}" HEAD || git rebase "origin/${base}"
```

Resolve textual conflicts by editing the conflict markers out, then `git rebase --continue`. The rebased tree is a fresh integration — this branch replayed on newly merged work — that no prior deterministic-verification run covered: the consuming flow MUST run the project's full deterministic-verification command against the rebased tree, and MUST re-establish the local `review-changes` review per `<local_review_invocation>` on the rebased diff, before the `--force-with-lease` push from `<push_semantics>`, and MUST fix any failure or unaddressed valid finding in the same pass before pushing.

A rebase that cannot be resolved autonomously — semantic conflicts, ambiguous overlapping edits — emits `SYNC_BASE` from `<action_tokens>` and waits for the operator to resolve the conflict before the next management pass.

Integrate base movement only with `git rebase origin/<base>`, which updates the working tree. NEVER `git reset` onto `origin/<base>` — not to integrate, and not to reorganize the branch's own commits during the review-convergence loop. `origin/<base>` advances as concurrent worktree-pool branches merge, so a reset onto it silently re-bases the branch onto whatever it became; with `--soft` the working tree is left on the old basis while HEAD jumps forward, desyncing the tree (files present in HEAD show as deleted, files the new base changed show as modified, none of it the branch's work). To reword or re-split the branch's own commits, reset to a FIXED ancestor on the branch — `git reset --soft HEAD~N` where N is the branch's own commit count, or the fork-point SHA from `git merge-base HEAD origin/<base>` — never onto `origin/<base>`. After any history rewrite, confirm `git diff --stat origin/<base>...HEAD` shows only the intended files and `git status` reports no surprise deletions before the `<push_semantics>` push; surprise files mean the base moved under the rewrite — stop and re-derive, do not push.

</base_sync>

<local_review_invocation>

The local `review-changes` gate is the author-side, pre-push instance of the same reviewing kind the CI review runs post-push — the two are the same class of gate on opposite sides of each push. Invoke it the way CI invokes its reviewer, passing nothing that narrows it:

- **Pass only the repository/worktree and the diff range.** `review-changes` resolves the diff itself (`git diff <base_ref>...<head_ref>` — three-dot merge-base semantics, where `head_ref` defaults to `HEAD`); the caller supplies the repository/worktree and, only when it must be made explicit, the base ref. No file list, no changed-area summary, no "the important part is …".
- **Add no interpretive scope.** Do not tell the reviewer which layers, files, or concerns to weight. It reviews the whole diff against the whole taxonomy.
- **Add no severity pre-filter.** Do not ask only for `BLOCKING`, do not suppress `DEBT`. The reviewer emits every finding; handling is by validity and phase per `<review_classification>`, downstream of the review and never inside its invocation.
- **Add no emphasis steering.** Do not tell the reviewer what to conclude or what matters most. It reads the repository's own instructions (CLAUDE.md / AGENTS.md and the standards skills) and the shared taxonomy itself.

Run it via the `changes-reviewer` agent — isolated context, so the verdict is not biased by what the operator's main context has been doing — or the `/review-changes` command when `changes-reviewer` is not installed; both drive the same `review-changes` skill chain. Iterate to convergence: each round, act on findings by validity and phase per `<review_classification>`, until no valid finding remains unaddressed.

This is the review predicate `REVIEW_READINESS` reads, and it runs before every push — the opening push (`/open-pr`) and every follow-up push (`/manage-pr`), against the diff that push would publish. Narrowing the invocation diverges the local gate from the CI reviewer it parallels, so its convergence no longer means what `REVIEW_READINESS` claims it means.

</local_review_invocation>

<authority_gates>

The PR lifecycle has three gates, evaluated in order. A **gate** is a named authorization over one lifecycle step, decided from defined predicates; a **predicate** is a condition a gate reads — predicates are never themselves gates. `/open-pr` evaluates `REVIEW_READINESS`; `/manage-pr` evaluates `MERGE_READINESS` and `PRODUCTION_READINESS`.

**`REVIEW_READINESS`** authorizes opening the PR. It holds when both predicates hold:

- **deterministic verification passes** — the project's full validation-and-testing command — the command the project documents in its `CLAUDE.md` / `AGENTS.md` (an overlay MAY centralize it in `spx/local/merging.md` so `/open-pr` and `/manage-pr` read one value) — reports success. A failing test in the suite means this predicate does not hold, including a TDD-red opener authored intentionally ahead of an implementation slice. The remedy is either land the implementation in the same PR so the test passes, or add the owning node to the project's spec-tree EXCLUDE mechanism (for example `spx/EXCLUDE`) so the test runner skips the node until implementation arrives. See `references/excluded-nodes.md` in `/understand`. Per-line suppression (`# noqa`, `# type: ignore`, `@pytest.mark.skipif`, `@pytest.mark.xfail`, equivalents in other languages) does not satisfy this predicate because those suppressions are scattered and invisible to the spec-tree status surface; and
- **the local review has converged** — `review-changes` (via the `changes-reviewer` agent or `/review-changes`), invoked at parity per `<local_review_invocation>` and iterated to convergence, leaves no valid finding unaddressed: each is fixed in the diff, or split out of the changeset and captured in the owning node's `ISSUES.md` / `PLAN.md`. An unbacked finding is dropped.

The moment `REVIEW_READINESS` holds, the PR is created `ready_for_review` — never draft (a stacked PR is the one exception, held draft per `<branch_topology>` until its base merges). There is no draft phase and no gated promotion; opening ready fires every CI review at once (reviewers that wait for ready, such as Codex, alongside the CI review).

Both `REVIEW_READINESS` predicates are re-established before every push, not only the opening push. A follow-up push that changes the diff — a fix for a CI finding, or a `<base_sync>` rebase — re-runs deterministic verification and the local review per `<local_review_invocation>` on the new diff before it is pushed. The local review before every push parallels the CI review that fires after every push: same class of gate, opposite sides of the push, so a follow-up diff never reaches CI without an author-side review first.

**`MERGE_READINESS`** authorizes merge. It holds when all predicates hold, every one decidable from observable PR state:

- a clean current-head CI review exists — the reviewing-kind output for the current head, read from the surfaces in `<review_inspection>`, complete and valid, that reports **no unresolved `BLOCKING` or `DEBT` finding** — stated directly per the reviewer's no-`BLOCKING`-or-`DEBT` convention, or with **every** such finding individually assessed and dropped as unbacked; a `DEBT` finding the author tracks out of scope with a recorded reason is not unresolved (validity per `<review_classification>`; a valid in-scope `BLOCKING`/`DEBT` finding is unresolved work Claude fixes before merge). The absence of a current-head review is never clean — it is `WAIT_FOR_REVIEW`;
- every other required check on `statusCheckRollup` is **terminal-green** (defined below);
- `<branch_hygiene>` passes, including the upstream-safety check;
- PR state is `OPEN`, `isDraft` is false, the inspected head SHA matches the branch head fetched from origin, and the branch is rebased onto current `origin/<base>` or is a fast-forward descendant.

`MERGE_READINESS` carries no time-based settle: a clean review arriving two minutes after open makes the gate hold two minutes after open.

**Mutation-point guard.** Immediately before any `gh pr merge` command, /manage-pr re-reads live PR state and recomputes `MERGE_READINESS`; it never relies on earlier inspection, conversation memory, or a prior `gh pr view` result. The guard reads PR state, `statusCheckRollup`, PR-level comments, formal reviews, review-thread comments, the fetched remote branch head, and the fetched base branch. It produces `MERGE_READY:<head-sha>` only when the freshly inspected head SHA, fetched remote branch head, and inspected status-check SHA match and every `MERGE_READINESS` predicate above still holds for that same head.

The guard withholds the merge command and emits the existing action token when any predicate fails:

- `WAIT_FOR_REVIEW` when current-head review output is absent, the reviewing-kind check is missing/non-terminal, or the reviewing-kind check skipped for any cause except the reviewer-skipped-by-design exception.
- `WAIT_FOR_CHECKS` when a non-review required check is queued, in progress, pending, expected, or otherwise non-terminal.
- `MERGE_BLOCKED:<reason>` when a required check is absent or terminal-but-not-success, the head SHA does not match the fetched remote branch head or status-check head, the PR is closed/draft, the branch is not based on current `origin/<base>`, or any other hard PR-state predicate fails.

`mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, and a successful `gh pr merge` response are GitHub transport behavior, not repository policy authority. Claude never runs `gh pr merge` as a probe for mergeability; the command is legal only after the mutation-point guard has produced `MERGE_READY:<head-sha>` and `PRODUCTION_READINESS` also holds.

**`PRODUCTION_READINESS`** permits the merge to execute. It holds when **either** the change is not production-relevant (per the overlay's production-relevance recognition mechanism) **or** the operator has explicitly approved the merge. Claude computes and pursues `MERGE_READINESS` identically for every PR; it executes the merge only when `PRODUCTION_READINESS` also holds. When the overlay declares no recognition mechanism, every change is non-production-relevant and the merge executes on `MERGE_READINESS` alone; a production-relevant change without approval keeps the merge withheld and the flow emits `AWAIT_APPROVAL` from `<action_tokens>`.

Claude NEVER asks the operator to choose between auto-merge, hold-at-green, or pause. `PRODUCTION_READINESS` is the only merge-approval touch-point, and it applies only where the overlay's production-relevance recognition mechanism marks the change production-relevant. With no such mechanism declared, every change is non-production-relevant and the merge fires on `MERGE_READINESS` alone — presenting a merge-gate confirmation through a structured question or in prose is a defect, identical to surfacing "should I rebase?" per `<base_sync>`. The merge is a mechanical consequence of `MERGE_READINESS ∧ PRODUCTION_READINESS`, not a decision to surface; the only operator-facing pauses the lifecycle carries are the explicit `<action_tokens>` an unresolved condition emits.

**terminal-green.** A required check in `statusCheckRollup` is a check run (`status` reaches `COMPLETED`, then a `conclusion`) or a status context (`state`). It is **terminal-green** only when terminal — `status == COMPLETED`, or `state ∈ {SUCCESS, ERROR, FAILURE}` — AND successful — `conclusion == SUCCESS`, or `state == SUCCESS`. A check that is non-terminal (`QUEUED` / `IN_PROGRESS` / `PENDING` / `EXPECTED`), terminal-but-not-success (`FAILURE` / `CANCELLED` / `TIMED_OUT` / `SKIPPED` / `NEUTRAL` / `ACTION_REQUIRED` / `ERROR`), or absent from the rollup is not terminal-green and blocks `MERGE_READINESS`.

**Acting on findings (validity and phase, never severity).** Claude acts on each finding by **validity** — whether it holds against its cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions; read those fresh and drop a finding they do not support — and by **phase**: before open (`REVIEW_READINESS`) apply every valid finding that belongs and split out of the changeset only a fix too large to belong — a genuinely separate, larger concern (its own node or feature), never a bounded fix such as a rename propagation, a cross-reference update, or a mechanical change — the split work leaves the diff and is captured in `ISSUES.md` / `PLAN.md`; on the open PR (`MERGE_READINESS`) fix every valid finding whose fix belongs in the changeset and re-push, with no deferral of in-scope work — a bounded fix is in-scope work the changeset carries, never deferred — while a `DEBT` finding the author judges a genuinely separate, larger concern is recorded in `ISSUES.md` / `PLAN.md` with a reason naming why it is large and tracked, not a merge blocker. Severity is the reviewer's reporting label; validity and scope (never the label) decide whether and how Claude acts on a finding, and the reviewer never decides whether the change merges.

**Reviewer-skipped-by-design (self-modifying-PR exception).** When the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate), no current-head review exists for `MERGE_READINESS`. Post one PR-level comment containing exactly `<trigger-phrase> review` (e.g., `@spec-tree review`) to fire the mention reviewer (which has no identical-content gate), emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, run `<pr_check_wait>`, and on the next management pass treat that reviewer's posted findings as the current-head review. This applies to that skip cause only — not path-filter, branch-filter, or manual skips.

**Follow-up pushes.** The PR is ready from open; a follow-up push — fixing a valid CI finding, or a `<base_sync>` rebase — pushes to the ready PR and re-fires CI. There is no draft toggle and no `gh pr ready` step in the loop.

</authority_gates>

<merge_cleanup>

Once `MERGE_READINESS ∧ PRODUCTION_READINESS` authorize the merge and the mutation-point guard has produced `MERGE_READY:<head-sha>`, Claude merges and then deletes the branch. The universal default — used whenever the overlay declares no merge command — is rebase merge with an explicit **`--delete-branch=false`**, followed by a worktree-safe manual deletion:

```bash
base=$(gh pr view <pr-number> --json baseRefName --jq '.baseRefName')
branch=$(gh pr view <pr-number> --json headRefName --jq '.headRefName')
# explicit --delete-branch=false — never rely on gh's default for the omitted flag (it
# varies by gh version and config, unknowable across consumer environments). =false
# guarantees gh skips its local-branch-delete + switch-to-"${base}" step, which fails
# when "${base}" is checked out in another worktree.
gh pr merge <pr-number> --rebase --delete-branch=false
git fetch origin "${base}"
git switch --detach "origin/${base}"   # step this worktree off the merged branch onto the new base tip
git branch -D "${branch}" 2>/dev/null || true   # delete the now-unoccupied local branch (tolerate "not found")
git ls-remote --exit-code --heads origin "${branch}" >/dev/null 2>&1 && git push origin --delete "${branch}"
git status --porcelain
```

Order matters: merge while the branch is still checked out — `gh pr merge` fails with "could not determine current branch" from a detached HEAD even with an explicit PR number — then detach this worktree, then delete the local branch, then delete the remote branch unless the host already auto-deleted it.

**Why the default passes `--delete-branch=false` explicitly.** `gh pr merge --delete-branch` — or the bare flag where a `gh` version or config defaults it on — run from the worktree on the branch being merged, makes `gh` switch that worktree to the base branch as part of deleting the local branch. In a multi-worktree checkout where the base (for example `main`) is checked out in another worktree, that switch fails with `fatal: '<base>' is already used by worktree at <path>` — the merge completes on the host, but the local branch is left undeleted and the flow ends in an error state. Omitting the flag is not enough: this methodology ships to consumer environments whose `gh` default for the omitted flag is unknowable, so the default states `--delete-branch=false` explicitly, guaranteeing `gh` never attempts that switch regardless of environment. Deliberate deletion stays in the worktree-safe manual sequence above, which behaves identically in single- and multi-worktree checkouts and tolerates a host that already auto-deleted the remote branch. A project that is always single-worktree MAY opt the overlay into inline `gh pr merge --rebase --delete-branch` per `<repo_local_overlay>`.

The merge flag follows the overlay when it declares one (`--merge` or `--squash`); `--rebase` is the universal default flag. The deletion steps after the merge are independent of which merge flag runs.

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
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments \
  --jq '.[] | {author: .user.login, path, line, createdAt: .created_at, excerpt: .body[0:160]}'
```

**NEVER drop `comments` from the `gh pr view --json` argument list.** The `comments` field carries PR-level issue comments — a distinct surface from `reviews` (formal review submissions) and from `gh api repos/<owner>/<repo>/pulls/<n>/comments` (review-thread comments tied to specific lines). Dropping `comments` to "trim the JSON" silently loses that third surface; a valid `BLOCKING` or `DEBT` finding posted there is invisible to the inspection, and `MERGE_READINESS` evaluates against a partial view. Whatever field list a calling flow constructs — it may add `statusCheckRollup`, `headRefOid`, `baseRefName`, `mergeable`, `mergeStateStatus`, or others for the merge-state predicates — `comments` MUST appear in it on every management pass. Construct the field list explicitly per pass; do not omit fields from an abbreviated re-creation between turns.

Compare timestamps against the most recent push. Entries after that push are re-reviews of the latest state — read them in full.

</review_inspection>

<review_classification>

Every review finding — whether produced by a reviewer (outgoing feedback) or triaged by an author (incoming feedback) — carries two dimensions: **severity** (one of two) and **category** (one of six). The taxonomy is shared so output and triage use the same vocabulary; nothing has to be translated between them.

The canonical specification for this taxonomy is `REVIEW.template.md` at the repository root. Consumer repos fork it to `REVIEW.md` to activate repo-local overrides; absent a fork, this skill's defaults apply. The taxonomy below mirrors the template's defaults.

**Severity** (one of two — the reviewer's reporting label for the finding's merge-safety nature):

| Severity   | Use when                                                                                                         |
| ---------- | ---------------------------------------------------------------------------------------------------------------- |
| `BLOCKING` | Merge-safety defect: if deployed, the changeset would create a deterministic issue or pose a risk.               |
| `DEBT`     | Real defect that does not jeopardize merge safety: a genuine problem the change carries, but not merge-blocking. |

Severity is the validity judgment the reviewer makes. **Disposition** — whether each `DEBT` finding is fixed in this PR or tracked out of scope — is the author's call, not the reviewer's; the reviewer carries no scope axis. A fix is **in scope** when it is bounded — a rename propagation, a cross-reference update, a mechanical change, or a fix that merely touches another file — and is fixed in the changeset; a finding is tracked out of scope only when its fix is a genuinely separate, larger concern (its own node or feature), with a recorded reason naming why it is large. Boundedness is never grounds to defer: a rename, a cross-reference, or a mechanical change is never tracked out of scope.

**A defect the changeset's own edits introduced is always in-scope and is never split out.** A claim an edit made stale, dead code a change orphaned, a cross-reference a rename broke, a spec a consolidation falsified — fixing the consequences of this change is part of this change, however many files the fix touches. "A genuinely separate, larger concern" means a node or capability that exists independently of this changeset; it is never a label applied to self-caused bounded work to end a review-convergence loop. If the only thing making a finding feel large is that fixing it would reopen the loop, it is in-scope — converge the loop, do not relabel the work to escape it.

**Handling is by validity and phase, never by severity.** Severity classifies the finding's nature for the reader; it is not a routing key. The consumer of a review validates each finding against its cited rule and the governing decisions, drops any the citation does not support, and acts on the rest by phase per `<authority_gates>`: before open (`REVIEW_READINESS`), apply every valid finding that belongs and split out of the changeset any whose fix is too large to belong; on the open PR (`MERGE_READINESS`), fix every valid in-scope finding the CI review surfaces, with no deferral of in-scope work — a bounded fix (a rename, a cross-reference, a mechanical change, a fix that merely touches another file) is in-scope work the changeset carries, never deferred — while a `DEBT` finding whose fix the author judges a genuinely separate, larger concern is recorded in `ISSUES.md` / `PLAN.md` with a reason naming why it is large and does not block the merge. A `BLOCKING` label does not force an action the citation does not support, and a `DEBT` label does not exempt a finding whose fix actually belongs in the changeset — validity, phase, and scope decide, and the reviewer never decides whether the change merges.

**Category** (one of six), grouped by three axes:

*What the code does vs. what it is supposed to do*

- `consistency` — disagreement across layers (decisions / PDR / ADR ↔ spec ↔ tests ↔ implementation). Surface the disagreement; do not judge which side is right.
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

Local auditor agents — `spec-tree:test-evidence-auditor`, `spec-tree:adr-auditor`, `spec-tree:pdr-auditor`, `spec-tree:auditor`, and the auditor agent that matches each installed language plugin (for example `<language>:<language>-code-auditor`, `<language>:<language>-test-auditor`, `<language>:<language>-architecture-auditor`, plus any language-specific specialized auditor that plugin declares) — emit structured findings for the slice they inspect.

**Verdict handling.** A `REJECTED` overall verdict, an `UNKNOWN` overall verdict, a `FAIL` row, an `UNKNOWN` row, or a `REJECT` finding is in-slice unresolved work, identical in handling to a valid `BLOCKING` or `DEBT` finding in `<review_classification>`: fix the bug or resolve the audit uncertainty, re-run the auditor, repeat until clean. `APPROVED` means the auditor found nothing in scope. "Capture in `ISSUES.md`" is NOT an option for rejected or unknown in-slice audit work on a slice currently under review — `ISSUES.md` is for items genuinely outside the slice (a known gap in an unrelated module, a tracking note for future enablement), never for in-slice bugs or audit uncertainty the auditor surfaced.

**Why auditor verdicts are authoritative.** Auditor agents invoke the same auditing skills the operator would invoke directly; each verdict is the auditing skill's structured output for its specific concern, not a separate discretionary decision. CI green and reviewer-bot approval do not erase an auditor REJECT because auditing and reviewing inspect different concerns: test evidence, PDR quality, architectural fitness, or language-specific code quality.

**Loop semantics.** When an invoked workflow surfaces auditor verdicts while preparing or repairing a PR, handle every `REJECTED` or `UNKNOWN` overall verdict, `FAIL` or `UNKNOWN` row, and `REJECT` finding as in-slice work under `<review_classification>`: fix it or resolve the audit uncertainty, re-run the auditor, and repeat until no rejected or unknown in-slice audit work remains. `APPROVED` means the auditor found nothing in its scope. Auditor findings do not add a fourth PR-lifecycle gate and do not change the `MERGE_READINESS` predicate set in `<authority_gates>`.

</auditor_verdicts>

<action_tokens>

The managing flow emits exactly one of these tokens per management pass when no autonomous action fires. An autonomous fire — the merge under `MERGE_READINESS ∧ PRODUCTION_READINESS` — runs the command directly and does not emit a token. A routine `<base_sync>` rebase likewise runs directly and emits no token of its own; only a rebase conflict that cannot be resolved autonomously emits `SYNC_BASE`.

| Token                                    | Emitted when                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `WAIT_FOR_CHECKS`                        | A required check is non-terminal (running, queued, pending) while a current-head review has landed; not yet terminal-green. Run the exact PR-check wait command from `<pr_check_wait>`, then re-inspect.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `WAIT_FOR_REVIEW`                        | No current-head CI review has landed yet on any inspected surface — review-absence takes precedence over the check-not-terminal-green and branch-hygiene predicates, so this fires even while other required checks remain non-terminal. Run the exact PR-check wait command from `<pr_check_wait>`, then re-inspect.                                                                                                                                                                                                                                                                                                                                                                                                        |
| `FIX_FINDING:<item>`                     | The current-head CI review reports a valid in-scope finding (the author judged it backed by its cited rule and governance, with a fix that belongs in the changeset). Claude fixes it and re-pushes; `<item>` carries the finding for triage, and its severity label is reporting only — validity and scope, not severity, drive the fix. A bounded fix (a rename propagation, a cross-reference, a mechanical change, a fix that touches another file) is in-scope and routed here, never deferred. A `DEBT` finding whose fix the author judges a genuinely separate, larger concern is recorded in `ISSUES.md` / `PLAN.md` with a reason naming why it is large and tracked, never routed here and never a merge blocker. |
| `AWAIT_APPROVAL:<reason>`                | `MERGE_READINESS` holds but the change is production-relevant and the operator has not approved; `PRODUCTION_READINESS` withholds the merge pending explicit approval.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `MENTION_REVIEW_NEEDED:<trigger-phrase>` | The current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate). Post one PR-level comment containing exactly `<trigger-phrase> review` to fire the mention-triggered reviewer (which has no identical-content gate); run the exact PR-check wait command from `<pr_check_wait>` before re-inspecting. The `review` suffix is the keyword the mention reviewer matches on — posting only the trigger phrase without it does not fire the reviewer.                                                                                                                                                                       |
| `MERGE_BLOCKED:<reason>`                 | `MERGE_READINESS` fails for a concrete reason not covered by another token (for example a failed or absent required check, or a PR-state predicate).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `SYNC_BASE`                              | A rebase onto the advanced base per `<base_sync>` hit a conflict that cannot be resolved autonomously; awaiting operator resolution before the next management pass.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `POST_MERGE_VERIFY`                      | PR merged; run post-merge verification per the project's Git workflow.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |

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
- The PR opens `ready_for_review` once `REVIEW_READINESS` holds — deterministic verification passes and the local review has converged — with no draft phase as a gating mechanism (a stacked PR held draft per `<branch_topology>` is the one exception).
- Both `REVIEW_READINESS` predicates — deterministic verification and a converged local review — are re-established on the diff every push publishes: the opening push and every follow-up push, including after a `<base_sync>` rebase.
- The local `review-changes` gate is invoked per `<local_review_invocation>` — only the repository/worktree and diff range are passed, with no interpretive scope, severity pre-filter, or emphasis steering.
- Waiting for CI review or checks uses the exact PR-check wait command from `<pr_check_wait>`.
- All three surfaces in `<review_inspection>` are inspected after every push, with `comments` always present in the `gh pr view --json` field list.
- Every finding is labeled with one of `BLOCKING` / `DEBT` — never `FOLLOW-UP`, never a severity rank, never a legacy class label — and acted on by validity and phase, never by severity.
- Every auditor verdict from a local auditor agent (per `<auditor_verdicts>`) is handled as an in-slice finding; `REJECTED` or `UNKNOWN` overall verdicts, `FAIL` or `UNKNOWN` rows, and `REJECT` findings are fixed or resolved in the slice, not deferred to `ISSUES.md`.
- Merge runs only when `MERGE_READINESS` and `PRODUCTION_READINESS` both hold and the mutation-point guard has just produced `MERGE_READY:<head-sha>`: the current-head CI review has no unresolved valid `BLOCKING` or `DEBT` finding, every other required check is terminal-green, branch hygiene and PR-state hold on the freshly inspected head, and the change is non-production-relevant or operator-approved. `MERGE_READINESS` carries no time-based settle.
- A committed changeset ahead of its resolved base is treated as unfinished until it reaches the default branch on origin through the selected lifecycle, or stops at an explicit `<action_tokens>` emission with no independent local action remaining.
- Local readiness — clean working tree, committed changes, passing deterministic verification, tests, local review, or audits — is reported as evidence and then carried forward; it is never a reason to ask what to do next.
- No structured question or prose confirmation asks the operator to choose between auto-merge, hold-at-green, or pause; the only operator-facing pauses are explicit `<action_tokens>` emissions.
- Merge runs via rebase merge followed by the worktree-safe manual branch deletion in `<merge_cleanup>` (`gh pr merge --rebase --delete-branch=false`, then detach this worktree onto the refreshed base and delete the local and remote branches separately) unless the overlay declares a different command or opts into inline `--delete-branch` — merge commit and squash are overlay opt-ins (overlay rationale documents the choice for human reviewers; Claude does not enforce it), not Claude's choice from the gate alone.
- The lifecycle runs from the determined changeset autonomously when the overlay declares no pre-mutation confirmation; when the overlay opts in, the structured-question plan presentation precedes the first mutating action and Claude waits for confirmation.
- Each pass that does not fire an autonomous action emits exactly one token from `<action_tokens>`.
- No `<self_reference>` violation appears in any artifact.

</success_criteria>
