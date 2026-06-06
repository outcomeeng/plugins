---
name: standardizing-merging
user-invocable: false
description: >-
  Shared vocabulary for the PR flow — pre-flight predicates, branch topology gate, push command, the three PR-authority gates (review / merge / production readiness), review classification, three review surfaces, action tokens, and repo-local overlay topics.
  Loaded by /opening-pr and /managing-pr.
allowed-tools: Read
---

<objective>
Defines the concepts, predicates, gates, commands, and tokens shared between the two PR flows — /opening-pr (the one-shot opening flow) and /managing-pr (the per-heartbeat managing loop). Carries no flow itself; ships vocabulary only.
</objective>

<reference_note>
This is a reference skill. /opening-pr and /managing-pr load this vocabulary automatically. Do not invoke directly.
</reference_note>

<repo_local_overlay>
When loaded inside a repository, check for `spx/local/merging.md` at the repository root. Read it after this reference if present and apply it as the repo-local specialization. Topics the overlay MAY refine:

- Extra pre-flight checks beyond `<branch_hygiene>`.
- The project's full deterministic-verification command (validation and testing) that `REVIEW_READINESS` runs.
- Push command overrides — the explicit destination ref form must be preserved.
- **Production-relevance recognition** — the mechanism by which the project classifies a change as production-relevant (label, branch prefix, file pattern, manifest declaration). A production-relevant change reaches `MERGE_READINESS` autonomously but executes only after explicit operator approval (`PRODUCTION_READINESS`). A project that wants a human in the loop for every merge declares every change production-relevant; a project that wants none declares no mechanism.
- **Merge command** — rebase merge followed by a worktree-safe manual branch deletion is the universal default; the merge flow runs it unless the overlay opts in to a different command. The merge runs without `--delete-branch` (`gh pr merge <pr-number> --rebase`), then this worktree detaches onto the refreshed base tip and the local and remote branches are deleted by separate commands — the sequence and its rationale are in `<merge_cleanup>`. The overlay may opt in to merge commit (`--merge`) or squash (`--squash`); merge commits and squashes are not the agent's choice to make from the gate alone. The overlay should document its rationale for human reviewers of the overlay change itself, but rationale is not a runtime predicate the agent enforces — the overlay's declaration is the agent's signal. The overlay MAY opt into inline `gh pr merge --rebase --delete-branch` for projects that are always single-worktree, where `gh`'s post-merge switch-to-base never collides.
- **Mention-reviewer trigger phrase** — the leading phrase the agent posts as a PR-level comment to fire the mention-triggered reviewer when the auto-review job reports `conclusion: skipped` (see `<authority_gates>` reviewer-skipped-by-design exception). The full comment body is `<trigger-phrase> review`; the `review` suffix is the keyword the mention reviewer matches on. Default: `@spec-tree` (the upstream reviewer action's default `trigger_phrase`). Each consuming project that configures a non-default `trigger_phrase` in its reviewer caller workflow declares the matching phrase here.

If `spx/local/merging.md` is absent or silent on a topic, the defaults in this reference apply. **Absence of a production-relevance recognition mechanism means every change is treated as not production-relevant**, so `PRODUCTION_READINESS` holds and the merge executes on `MERGE_READINESS` alone. The other `MERGE_READINESS` predicates (current-head CI review with no unresolved valid `BLOCKING` or `DEBT` finding, every other required check terminal-green, branch hygiene, PR-state) still apply.

The overlay cannot override the open-ready mandate — once `REVIEW_READINESS` holds the PR is created `ready_for_review`. There is no draft phase and no gated draft-to-ready promotion; a stacked PR is the one exception, held draft per `<branch_topology>` until its base merges.
</repo_local_overlay>

<branch_hygiene>

Conditions that must hold before every push (initial or follow-up). Failure stops the calling flow.

| Condition (must hold)                                        | Failure response                                                      |
| ------------------------------------------------------------ | --------------------------------------------------------------------- |
| Current branch is not `main`, `master`, or detached HEAD     | STOP. Switch to a feature branch.                                     |
| Working tree is clean (no uncommitted changes)               | STOP. Commit via /committing-changes or stash before pushing.         |
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

**Post-merge reconstruction.** Once the stack base merges, re-invoke /opening-pr (or rebase manually) to re-target the PR at the default branch, re-classify as peer, and open it ready. GitHub auto-retargets the PR base on the API side, but the local branch must still be rebased onto the updated default and the manifest version re-evaluated against the new base.

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

Base drift is checked on the same checkpoint that inspects reviews — every heartbeat reads review state and the `origin/<base>` position together. When the branch is behind `origin/<base>`, rebase immediately, independent of whether a review has landed and independent of whether any landed review carries findings.

Rebase on drift, not at merge time. A branch behind base is superseded by a rebase before it can merge, so every check run and every review posted against the un-rebased head is wasted effort. Rebasing the moment drift appears aims CI and reviewers at the head that will actually merge, and surfaces a conflicted ("nasty") rebase early — while the heartbeat is already waiting on reviews — instead of at merge time, where an unexpected conflict or an integration regression costs a full extra review round on the critical path.

`<base_sync>` reads `${base}` from the calling flow rather than re-deriving it — /managing-pr Step 1 captures it from `gh pr view --json baseRefName` (which returns the PR's actual base for both peer and stacked topologies), and /opening-pr's `<branch_hygiene>` sets it from `gh repo view --json defaultBranchRef` before any PR exists. The block runs identically in both contexts.

```bash
git fetch origin "${base}"
git merge-base --is-ancestor "origin/${base}" HEAD || git rebase "origin/${base}"
```

Resolve textual conflicts by editing the conflict markers out, then `git rebase --continue`. The rebased tree is a fresh integration — this branch replayed on newly merged work — that no prior deterministic-verification run covered: the consuming flow MUST run the project's full deterministic-verification command against the rebased tree, and MUST re-establish the local `reviewing-changes` review per `<local_review_invocation>` on the rebased diff, before the `--force-with-lease` push from `<push_semantics>`, and MUST fix any failure or unaddressed valid finding in the same pass before pushing.

A rebase that cannot be resolved autonomously — semantic conflicts, ambiguous overlapping edits — emits `SYNC_BASE` from `<action_tokens>` and waits for the operator; the heartbeat re-fires.

</base_sync>

<local_review_invocation>

The local `reviewing-changes` gate is the author-side, pre-push instance of the same reviewing kind the CI review runs post-push — the two are the same class of gate on opposite sides of each push. Invoke it the way CI invokes its reviewer, passing nothing that narrows it:

- **Pass only the repository/worktree and the diff range.** `reviewing-changes` resolves the diff itself (`git diff <base_ref>...<head_ref>` — three-dot merge-base semantics, where `head_ref` defaults to `HEAD`); the caller supplies the repository/worktree and, only when it must be made explicit, the base ref. No file list, no changed-area summary, no "the important part is …".
- **Add no interpretive scope.** Do not tell the reviewer which layers, files, or concerns to weight. It reviews the whole diff against the whole taxonomy.
- **Add no severity pre-filter.** Do not ask only for `BLOCKING`, do not suppress `FOLLOW-UP`. The reviewer emits every finding; handling is by validity and phase per `<review_classification>`, downstream of the review and never inside its invocation.
- **Add no emphasis steering.** Do not tell the reviewer what to conclude or what matters most. It reads the repository's own instructions (CLAUDE.md / AGENTS.md and the `standardizing-*` skills) and the shared taxonomy itself.

Run it via the `changes-reviewer` agent — isolated context, so the verdict is not biased by what the operator's main agent has been doing — or the `/review-changes` command when the agent is not installed; both drive the same `reviewing-changes` skill chain. Iterate to convergence: each round, act on findings by validity and phase per `<review_classification>`, until no valid finding remains unaddressed.

This is the review predicate `REVIEW_READINESS` reads, and it runs before every push — the opening push (`/opening-pr`) and every follow-up push (`/managing-pr`), against the diff that push would publish. Narrowing the invocation diverges the local gate from the CI reviewer it parallels, so its convergence no longer means what `REVIEW_READINESS` claims it means.

</local_review_invocation>

<authority_gates>

The PR lifecycle has three gates, evaluated in order. A **gate** is a named authorization over one lifecycle step, decided from defined predicates; a **predicate** is a condition a gate reads — predicates are never themselves gates. `/opening-pr` evaluates `REVIEW_READINESS`; `/managing-pr` evaluates `MERGE_READINESS` and `PRODUCTION_READINESS`.

**`REVIEW_READINESS`** authorizes opening the PR. It holds when both predicates hold:

- **deterministic verification passes** — the project's full validation-and-testing command — the command the project documents in its `CLAUDE.md` / `AGENTS.md` (an overlay MAY centralize it in `spx/local/merging.md` so `/opening-pr` and `/managing-pr` read one value) — reports success. A failing test in the suite means this predicate does not hold, including a TDD-red opener authored intentionally ahead of an implementation slice. The remedy is either land the implementation in the same PR so the test passes, or add the owning node to the project's spec-tree EXCLUDE mechanism (for example `spx/EXCLUDE`) so the test runner skips the node until implementation arrives. See `references/excluded-nodes.md` in `/understanding`. Per-line suppression (`# noqa`, `# type: ignore`, `@pytest.mark.skipif`, `@pytest.mark.xfail`, equivalents in other languages) does not satisfy this predicate because those suppressions are scattered and invisible to the spec-tree status surface; and
- **the local review has converged** — `reviewing-changes` (via the `changes-reviewer` agent or `/review-changes`), invoked at parity per `<local_review_invocation>` and iterated to convergence, leaves no valid finding unaddressed: each is fixed in the diff, or split out of the changeset and captured in the owning node's `ISSUES.md` / `PLAN.md`. An unbacked finding is dropped.

The moment `REVIEW_READINESS` holds, the PR is created `ready_for_review` — never draft (a stacked PR is the one exception, held draft per `<branch_topology>` until its base merges). There is no draft phase and no gated promotion; opening ready fires every CI review at once (reviewers that wait for ready, such as Codex, alongside the CI review).

Both `REVIEW_READINESS` predicates are re-established before every push, not only the opening push. A follow-up push that changes the diff — a fix for a CI finding, or a `<base_sync>` rebase — re-runs deterministic verification and the local review per `<local_review_invocation>` on the new diff before it is pushed. The local review before every push parallels the CI review that fires after every push: same class of gate, opposite sides of the push, so a follow-up diff never reaches CI without an author-side review first.

**`MERGE_READINESS`** authorizes merge. It holds when all predicates hold, every one decidable from observable PR state:

- a clean current-head CI review exists — the reviewing-kind output for the current head, read from the surfaces in `<review_inspection>`, complete and valid, that reports **no unresolved `BLOCKING` or `DEBT` finding** — stated directly per the reviewer's no-`BLOCKING`-or-`DEBT` convention, or with **every** such finding individually assessed and dropped as unbacked; `FOLLOW-UP` findings are tracked, never blocking (validity per `<review_classification>`; a valid `BLOCKING`/`DEBT` finding is unresolved work the agent fixes before merge). The absence of a current-head review is never clean — it is `WAIT_FOR_REVIEW`;
- every other required check on `statusCheckRollup` is **terminal-green** (defined below);
- `<branch_hygiene>` passes, including the upstream-safety check;
- PR state is `OPEN`, `isDraft` is false, the inspected head SHA matches the branch head fetched from origin, and the branch is rebased onto current `origin/<base>` or is a fast-forward descendant.

`MERGE_READINESS` carries no time-based settle: a clean review arriving two minutes after open makes the gate hold two minutes after open.

**`PRODUCTION_READINESS`** permits the merge to execute. It holds when **either** the change is not production-relevant (per the overlay's production-relevance recognition mechanism) **or** the operator has explicitly approved the merge. The agent computes and pursues `MERGE_READINESS` identically for every PR; it executes the merge only when `PRODUCTION_READINESS` also holds. When the overlay declares no recognition mechanism, every change is non-production-relevant and the merge executes on `MERGE_READINESS` alone; a production-relevant change without approval keeps the merge withheld and the flow emits `AWAIT_APPROVAL` from `<action_tokens>`.

**terminal-green.** A required check in `statusCheckRollup` is a check run (`status` reaches `COMPLETED`, then a `conclusion`) or a status context (`state`). It is **terminal-green** only when terminal — `status == COMPLETED`, or `state ∈ {SUCCESS, ERROR, FAILURE}` — AND successful — `conclusion == SUCCESS`, or `state == SUCCESS`. A check that is non-terminal (`QUEUED` / `IN_PROGRESS` / `PENDING` / `EXPECTED`), terminal-but-not-success (`FAILURE` / `CANCELLED` / `TIMED_OUT` / `SKIPPED` / `NEUTRAL` / `ACTION_REQUIRED` / `ERROR`), or absent from the rollup is not terminal-green and blocks `MERGE_READINESS`.

**Acting on findings (validity and phase, never severity).** The agent acts on each finding by **validity** — whether it holds against its cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions; read those fresh and drop a finding they do not support — and by **phase**: before open (`REVIEW_READINESS`) apply every valid finding that belongs and split out of the changeset any whose fix is too large to belong — the split work leaves the diff and is captured in `ISSUES.md` / `PLAN.md`; on the open PR (`MERGE_READINESS`) fix every valid finding whose fix belongs in the changeset and re-push, with no deferral of in-scope work — while a genuinely out-of-scope `FOLLOW-UP` is recorded in `ISSUES.md` / `PLAN.md` and tracked, not a merge blocker. Severity is the reviewer's reporting label; validity and scope (never the label) decide whether and how the agent acts on a finding, and the reviewer never decides whether the change merges.

**Reviewer-skipped-by-design (self-modifying-PR exception).** When the current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate), no current-head review exists for `MERGE_READINESS`. Post one PR-level comment containing exactly `<trigger-phrase> review` (e.g., `@spec-tree review`) to fire the mention reviewer (which has no identical-content gate), emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, and on the next heartbeat treat that reviewer's posted findings as the current-head review. This applies to that skip cause only — not path-filter, branch-filter, or manual skips.

**Follow-up pushes.** The PR is ready from open; a follow-up push — fixing a valid CI finding, or a `<base_sync>` rebase — pushes to the ready PR and re-fires CI. There is no draft toggle and no `gh pr ready` step in the loop.

</authority_gates>

<merge_cleanup>

Once `MERGE_READINESS ∧ PRODUCTION_READINESS` authorize the merge, the agent merges and then deletes the branch. The universal default — used whenever the overlay declares no merge command — is rebase merge **without** `--delete-branch`, followed by a worktree-safe manual deletion:

```bash
base=$(gh pr view <pr-number> --json baseRefName --jq '.baseRefName')
branch=$(gh pr view <pr-number> --json headRefName --jq '.headRefName')
# merge only — no --delete-branch (gh would switch THIS worktree to "${base}" as its
# local-cleanup phase, which fails when "${base}" is checked out in another worktree)
gh pr merge <pr-number> --rebase
git fetch origin "${base}"
git switch --detach "origin/${base}"   # step this worktree off the merged branch onto the new base tip
git branch -D "${branch}" 2>/dev/null || true   # delete the now-unoccupied local branch (tolerate "not found")
git ls-remote --exit-code --heads origin "${branch}" >/dev/null 2>&1 && git push origin --delete "${branch}"
git status --porcelain
```

Order matters: merge while the branch is still checked out — `gh pr merge` fails with "could not determine current branch" from a detached HEAD even with an explicit PR number — then detach this worktree, then delete the local branch, then delete the remote branch unless the host already auto-deleted it.

**Why the default avoids inline `--delete-branch`.** `gh pr merge --delete-branch`, run from the worktree that is on the branch being merged, makes `gh` switch that worktree to the base branch as part of deleting the local branch. In a multi-worktree checkout where the base (for example `main`) is checked out in another worktree, that switch fails with `fatal: '<base>' is already used by worktree at <path>` — the merge completes on the host, but the local branch is left undeleted and the flow ends in an error state. The manual sequence above is worktree-safe and behaves identically in single- and multi-worktree checkouts. A project that is always single-worktree MAY opt the overlay into inline `gh pr merge --rebase --delete-branch` per `<repo_local_overlay>`.

The merge flag follows the overlay when it declares one (`--merge` or `--squash`); `--rebase` is the universal default flag. The deletion steps after the merge are independent of which merge flag runs.

</merge_cleanup>

<heartbeat>

Waiting for CI runs, reviews, or check completion happens through the runtime timer, never in-shell. The consuming flow loads `/tracking-tasks` before creating, refreshing, or deleting runtime tracking after opening a PR and after every follow-up push.

`/tracking-tasks` owns runtime-specific payload shape, stale-context limits, lifecycle rules, failed-check handling, approval-boundary deletion, and timer-tool selection. This section owns only the PR-flow fact that PR waits use runtime tracking and re-enter /managing-pr.

The re-entry prompt follows `/tracking-tasks` `<heartbeat_payload>`: it names the skill to reload and the pointer that skill handles — the PR number — as `/managing-pr <pr-number>`. From that pointer the managing flow resolves the branch, base, review state, and checks via `gh pr view`, and reconstructs the directive and finding classifications by re-reading the PR body, the commits, and the node's `PLAN.md` / `ISSUES.md`. The prompt never carries the directive, the finding classifications, or the merge-gate reasoning — those are reconstructed on wake-up, and anything a later fire must know is written to `PLAN.md` / `ISSUES.md`, never assumed to survive in conversation memory.

**One heartbeat per PR.** Whichever flow first needs a heartbeat creates it; the other refreshes the same heartbeat rather than creating a second one.

Forbidden in-shell waits: shell `sleep`, `gh pr checks --watch`, `gh run watch`, `until`/`while` polling. The Bash tool does not reliably reap subprocess trees across turns; fork-bomb-class accumulation results when these patterns are repeated.

</heartbeat>

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

**NEVER drop `comments` from the `gh pr view --json` argument list.** The `comments` field carries PR-level issue comments — a distinct surface from `reviews` (formal review submissions) and from `gh api repos/<owner>/<repo>/pulls/<n>/comments` (review-thread comments tied to specific lines). Dropping `comments` to "trim the JSON" silently loses that third surface; a valid `BLOCKING` or `DEBT` finding posted there is invisible to the inspection, and `MERGE_READINESS` evaluates against a partial view. Whatever field list a calling flow constructs — it may add `statusCheckRollup`, `headRefOid`, `baseRefName`, `mergeable`, `mergeStateStatus`, or others for the merge-state predicates — `comments` MUST appear in it on every heartbeat. Construct the field list explicitly per heartbeat; do not omit fields from an abbreviated re-creation between turns.

Compare timestamps against the most recent push. Entries after that push are re-reviews of the latest state — read them in full.

</review_inspection>

<review_classification>

Every review finding — whether produced by a reviewer (outgoing feedback) or triaged by an author (incoming feedback) — carries two dimensions: **severity** (one of three) and **category** (one of six). The taxonomy is shared so output and triage use the same vocabulary; nothing has to be translated between them.

The canonical specification for this taxonomy is `REVIEW.template.md` at the repository root. Consumer repos fork it to `REVIEW.md` to activate repo-local overrides; absent a fork, this skill's defaults apply. The taxonomy below mirrors the template's defaults.

**Severity** (one of three — the reviewer's reporting label for the finding's merge-safety nature):

| Severity    | Use when                                                                                                                                                    |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BLOCKING`  | Merge-safety defect: if deployed, the changeset would create a deterministic issue or pose a risk.                                                          |
| `DEBT`      | Must-fix-eventually defect: does not jeopardize the product if shipped but accumulates technical debt.                                                      |
| `FOLLOW-UP` | Out-of-scope finding: does not jeopardize the product if shipped and fixing it would require wider refactoring or scope that extends the PR's blast-radius. |

**Handling is by validity and phase, never by severity.** Severity classifies the finding's nature for the reader; it is not a routing key. The consumer of a review validates each finding against its cited rule and the governing decisions, drops any the citation does not support, and acts on the rest by phase per `<authority_gates>`: before open (`REVIEW_READINESS`), apply every valid finding that belongs and split out of the changeset any whose fix is too large to belong; on the open PR (`MERGE_READINESS`), fix every valid in-scope finding the CI review surfaces, with no deferral of in-scope work, while a genuinely out-of-scope `FOLLOW-UP` is recorded in `ISSUES.md` / `PLAN.md` and does not block the merge. A `BLOCKING` label does not force an action the citation does not support, and a `FOLLOW-UP` label does not exempt a finding whose fix actually belongs in the changeset — validity, phase, and scope decide, and the reviewer never decides whether the change merges.

**Category** (one of six), grouped by three axes:

*What the code does vs. what it is supposed to do*

- `consistency` — disagreement across layers (decisions / PDR / ADR ↔ spec ↔ tests ↔ implementation). Surface the disagreement; do not judge which side is right.
- `security` — confidentiality, integrity, availability.
- `performance` — unbounded loops, hot-path allocations, O(n²) traversals where O(n) suffices, synchronous I/O on async paths, and similar pessimisations that change the changeset's runtime characteristics under realistic load.

*How we know it does what it is supposed to do*

- `evidence` — inadequate coverage of declared assertions by tests or evals; unmaintainable tests (literals, magic numbers, test-owned constants, duplication); evals that no longer exercise the assertions they claim to.

*How it does what it is supposed to do*

- `standards` — adherence to CLAUDE.md and the rules declared in `standardizing-*` skills (naming conventions, command tokens, file structure, language idioms).
- `architecture` — violation of structural principles declared by ADRs or PDRs (layer boundaries, separation of concerns, dependency directions, module-shape rules). A finding is an architecture one when the structure itself is at odds with a governance principle, even if every layer is internally consistent.

**Label asymmetry by severity.** `BLOCKING` and `DEBT` both require an action in this PR and use `Reference:` + `Evidence:` + `Required:`. `FOLLOW-UP` requires only a tracking commitment elsewhere and uses `Reference:` + `Issue:` + `Track under:`.

**No findings: say so directly.** When the changeset has no `BLOCKING` or `DEBT` findings, post a one-line comment saying so. NEVER invent lower-priority findings to prove the review happened.

**Findings only — never open questions, never commentary.** A reviewer with a question frames it as a finding (e.g., "Evidence: cannot verify X from the changeset; if assumption Y holds, this breaks Z because …") rather than asking a question that waits for an answer. Questions add CI roundtrips a single-pass review cannot recover from. Praise, observations, and commentary that do not constitute findings are noise — omit them.

**Forbidden taxonomies.** Severity-rank labels MUST NOT replace the three severities — no `P0` / `P1` / `P2` / `P3`, no `critical` / `high` / `medium` / `low`, no `minor` / `nit` headings. Risk words may appear inside rationale only when they add concrete evidence, never as a finding's primary label. Legacy class labels `NEEDS-ANSWER` and `NOTE` are forbidden — open questions are reframed as findings; commentary is omitted.

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

```text
### FOLLOW-UP [architecture]: path/to/file
Reference: <quote the standard from CLAUDE.md, skills, governance from decisions (PDR/ADR), or assertion from specs>
Issue: <what is missing or worthy of improvement>
Track under: <ISSUES.md file or product-specific issue tracker>
```

</review_classification>

<auditor_verdicts>

Local auditor agents — `spec-tree:test-evidence-auditor`, `spec-tree:audit-adr`, `spec-tree:audit-pdr`, `spec-tree:auditor`, and the auditor agent that matches each installed language plugin (for example `<language>:<language>-code-auditor`, `<language>:<language>-test-auditor`, `<language>:<language>-architecture-auditor`, plus any language-specific specialized auditor that plugin declares) — emit structured findings for the slice they inspect.

**Verdict handling.** A `REJECTED` overall verdict, an `UNKNOWN` overall verdict, a `FAIL` row, an `UNKNOWN` row, or a `REJECT` finding is in-slice unresolved work, identical in handling to a valid `BLOCKING` or `DEBT` finding in `<review_classification>`: fix the bug or resolve the audit uncertainty, re-run the auditor, repeat until clean. `APPROVED` means the auditor found nothing in scope. "Capture in `ISSUES.md`" is NOT an option for rejected or unknown in-slice audit work on a slice currently under review — `ISSUES.md` is for items genuinely outside the slice (a known gap in an unrelated module, a tracking note for future enablement), never for in-slice bugs or audit uncertainty the auditor surfaced.

**Why auditor verdicts are authoritative.** Auditor agents invoke the same auditing skills the operator would invoke directly; each verdict is the auditing skill's structured output for its specific concern, not a separate discretionary decision. CI green and reviewer-bot approval do not erase an auditor REJECT because auditing and reviewing inspect different concerns: test evidence, PDR quality, architectural fitness, or language-specific code quality.

**Loop semantics.** When an invoked workflow surfaces auditor verdicts while preparing or repairing a PR, handle every `REJECTED` or `UNKNOWN` overall verdict, `FAIL` or `UNKNOWN` row, and `REJECT` finding as in-slice work under `<review_classification>`: fix it or resolve the audit uncertainty, re-run the auditor, and repeat until no rejected or unknown in-slice audit work remains. `APPROVED` means the auditor found nothing in its scope. Auditor findings do not add a fourth PR-lifecycle gate and do not change the `MERGE_READINESS` predicate set in `<authority_gates>`.

</auditor_verdicts>

<action_tokens>

The managing flow emits exactly one of these tokens per heartbeat pass when no autonomous action fires. An autonomous fire — the merge under `MERGE_READINESS ∧ PRODUCTION_READINESS` — runs the command directly and does not emit a token. A routine `<base_sync>` rebase likewise runs directly and emits no token of its own; only a rebase conflict that cannot be resolved autonomously emits `SYNC_BASE`.

| Token                                    | Emitted when                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `WAIT_FOR_CHECKS`                        | A required check is non-terminal (running, queued, pending) while a current-head review has landed; not yet terminal-green. The heartbeat re-fires.                                                                                                                                                                                                                                                                                                                                                                   |
| `WAIT_FOR_REVIEW`                        | No current-head CI review has landed yet on any inspected surface — review-absence takes precedence over the check-not-terminal-green and branch-hygiene predicates, so this fires even while other required checks remain non-terminal.                                                                                                                                                                                                                                                                              |
| `FIX_FINDING:<item>`                     | The current-head CI review reports a valid in-scope finding (the agent judged it backed by its cited rule and governance, with a fix that belongs in the changeset). The agent fixes it and re-pushes; `<item>` carries the finding for triage, and its severity label is reporting only — validity and scope, not severity, drive the fix. A genuinely out-of-scope `FOLLOW-UP` is recorded in `ISSUES.md` / `PLAN.md` and tracked, never routed here and never a merge blocker.                                     |
| `AWAIT_APPROVAL:<reason>`                | `MERGE_READINESS` holds but the change is production-relevant and the operator has not approved; `PRODUCTION_READINESS` withholds the merge pending explicit approval.                                                                                                                                                                                                                                                                                                                                                |
| `MENTION_REVIEW_NEEDED:<trigger-phrase>` | The current-head CI review reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate). Post one PR-level comment containing exactly `<trigger-phrase> review` to fire the mention-triggered reviewer (which has no identical-content gate); reschedule the heartbeat to await its findings. The `review` suffix is the keyword the mention reviewer matches on — posting only the trigger phrase without it does not fire the reviewer. |
| `MERGE_BLOCKED:<reason>`                 | `MERGE_READINESS` fails for a concrete reason not covered by another token (for example a failed or absent required check, or a PR-state predicate).                                                                                                                                                                                                                                                                                                                                                                  |
| `SYNC_BASE`                              | A rebase onto the advanced base per `<base_sync>` hit a conflict that cannot be resolved autonomously; awaiting operator resolution. The heartbeat re-fires.                                                                                                                                                                                                                                                                                                                                                          |
| `POST_MERGE_VERIFY`                      | PR merged; run post-merge verification per the project's Git workflow.                                                                                                                                                                                                                                                                                                                                                                                                                                                |

</action_tokens>

<self_reference>

No "Claude", "AI", "agent", "Co-Authored-By: Claude", or similar identity strings in any merge-flow artifact: branch names, commit messages, PR titles, PR bodies, review comments.

</self_reference>

<success_criteria>

The two flows that consume this vocabulary satisfy their contracts when, at minimum:

- `<branch_hygiene>` predicates hold before every push (initial and every follow-up).
- `<branch_topology>` is classified before every push, with the matching gate passing.
- Every push uses the explicit destination ref form from `<push_semantics>`.
- A managing-flow pass that finds the branch behind `origin/<base>` rebases it per `<base_sync>` before driving the work queue.
- The PR opens `ready_for_review` once `REVIEW_READINESS` holds — deterministic verification passes and the local review has converged — with no draft phase as a gating mechanism (a stacked PR held draft per `<branch_topology>` is the one exception).
- Both `REVIEW_READINESS` predicates — deterministic verification and a converged local review — are re-established on the diff every push publishes: the opening push and every follow-up push, including after a `<base_sync>` rebase.
- The local `reviewing-changes` gate is invoked per `<local_review_invocation>` — only the repository/worktree and diff range are passed, with no interpretive scope, severity pre-filter, or emphasis steering.
- Waiting for CI, review, or checks is delegated to runtime tracking per `<heartbeat>` and using the skill `/tracking-tasks`.
- All three surfaces in `<review_inspection>` are inspected after every push, with `comments` always present in the `gh pr view --json` field list.
- Every finding is labeled with one of `BLOCKING` / `DEBT` / `FOLLOW-UP` — never a severity rank, never a legacy four-class label — and acted on by validity and phase, never by severity.
- Every auditor verdict from a local auditor agent (per `<auditor_verdicts>`) is handled as an in-slice finding; `REJECTED` or `UNKNOWN` overall verdicts, `FAIL` or `UNKNOWN` rows, and `REJECT` findings are fixed or resolved in the slice, not deferred to `ISSUES.md`.
- Merge runs only when `MERGE_READINESS` and `PRODUCTION_READINESS` both hold: the current-head CI review has no unresolved valid `BLOCKING` or `DEBT` finding, every other required check is terminal-green, branch hygiene and PR-state hold, and the change is non-production-relevant or operator-approved. `MERGE_READINESS` carries no time-based settle.
- Merge runs via rebase merge followed by the worktree-safe manual branch deletion in `<merge_cleanup>` (`gh pr merge --rebase` without `--delete-branch`, then detach this worktree onto the refreshed base and delete the local and remote branches separately) unless the overlay declares a different command or opts into inline `--delete-branch` — merge commit and squash are overlay opt-ins (overlay rationale documents the choice for human reviewers; the agent does not enforce it), not the agent's choice from the gate alone.
- Each pass that does not fire an autonomous action emits exactly one token from `<action_tokens>`.
- No `<self_reference>` violation appears in any artifact.

</success_criteria>
