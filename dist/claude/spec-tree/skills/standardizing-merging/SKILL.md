---
name: standardizing-merging
user-invocable: false
description: >-
  Shared vocabulary for the PR flow — pre-flight predicates, branch topology gate, push command, the three PR-authority gates (review / merge / production readiness), review classification, three review surfaces, action tokens, and repo-local overlay topics.
  Loaded by /opening-pr and /managing-pr.
allowed-tools: Read
---

<objective>
The shared vocabulary the two PR flows consume. /opening-pr walks the opening flow (one-shot, linear, terminates at exit). /managing-pr walks the managing flow (loop body, re-enters per heartbeat fire). This skill defines the concepts, gates, commands, and tokens the two flows invoke; it carries no flow itself.
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
- **Merge command** — rebase merge with inline branch deletion (`gh pr merge <pr-number> --rebase --delete-branch`) is the universal default; the merge flow runs it unless the overlay opts in to a different command. The overlay may opt in to merge commit (`--merge`) or squash (`--squash`); merge commits and squashes are not the agent's choice to make from the gate alone. The overlay should document its rationale for human reviewers of the overlay change itself, but rationale is not a runtime predicate the agent enforces — the overlay's declaration is the agent's signal. The overlay may also opt out of inline branch deletion and into a separate `git push origin --delete <branch>` after `gh pr merge` to avoid multi-worktree cleanup failures.
- **Mention-reviewer trigger phrase** — the leading phrase the agent posts as a PR-level comment to fire the mention-triggered reviewer when the auto-review job reports `conclusion: skipped` (see `<authority_gates>` reviewer-skipped-by-design exception). The full comment body is `<trigger-phrase> review`; the `review` suffix is the keyword the mention reviewer matches on. Default: `@spec-tree` (the upstream reviewer action's default `trigger_phrase`). Each consuming project that configures a non-default `trigger_phrase` in its reviewer caller workflow declares the matching phrase here.

If `spx/local/merging.md` is absent or silent on a topic, the defaults in this reference apply. **Absence of a production-relevance recognition mechanism means every change is treated as not production-relevant**, so `PRODUCTION_READINESS` holds and the merge executes on `MERGE_READINESS` alone. The other `MERGE_READINESS` predicates (current-head CI review with no valid finding, every other required check terminal-green, branch hygiene, PR-state) still apply.

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

Resolve textual conflicts by editing the conflict markers out, then `git rebase --continue`. The rebased tree is a fresh integration — this branch replayed on newly merged work — that no prior deterministic-verification run covered: the consuming flow MUST run the project's full deterministic-verification command against the rebased tree before the `--force-with-lease` push from `<push_semantics>`, and MUST fix any failure in the same pass before pushing.

A rebase that cannot be resolved autonomously — semantic conflicts, ambiguous overlapping edits — emits `SYNC_BASE` from `<action_tokens>` and waits for the operator; the heartbeat re-fires.

</base_sync>

<authority_gates>

The PR lifecycle has three gates, evaluated in order, from `spx/15-agent-pr-authority.pdr.md`. A **gate** is a named authorization over one lifecycle step, decided from defined predicates; a **predicate** is a condition a gate reads — predicates are never themselves gates. `/opening-pr` evaluates `REVIEW_READINESS`; `/managing-pr` evaluates `MERGE_READINESS` and `PRODUCTION_READINESS`.

**`REVIEW_READINESS`** authorizes opening the PR. It holds when both predicates hold:

- **deterministic verification passes** — the project's full validation-and-testing command (named in `spx/local/merging.md`) reports success; and
- **the local review has converged** — `reviewing-changes` (via the `changes-reviewer` agent or `/review-changes`), iterated to convergence, leaves no valid finding unaddressed: each is fixed in the diff, or split out of the changeset and captured in the owning node's `ISSUES.md` / `PLAN.md`. An unbacked finding is dropped.

The moment `REVIEW_READINESS` holds, the PR is created `ready_for_review` — never draft (a stacked PR is the one exception, held draft per `<branch_topology>` until its base merges). There is no draft phase and no gated promotion; opening ready fires every CI review at once (reviewers that wait for ready, such as Codex, alongside the CI `spec-tree-review`).

**`MERGE_READINESS`** authorizes merge. It holds when all predicates hold, every one decidable from observable PR state:

- the current-head CI `spec-tree-review` reports **no valid finding** (validity per `<review_classification>`; an unbacked finding is dropped, a valid finding is unresolved work the agent fixes before merge);
- every other required check on `statusCheckRollup` is **terminal-green** (defined below);
- `<branch_hygiene>` passes, including the upstream-safety check;
- PR state is `OPEN`, `isDraft` is false, the inspected head SHA matches the branch head fetched from origin, and the branch is rebased onto current `origin/<base>` or is a fast-forward descendant.

`MERGE_READINESS` carries no time-based settle: a clean review arriving two minutes after open makes the gate hold two minutes after open.

**`PRODUCTION_READINESS`** permits the merge to execute. It holds when **either** the change is not production-relevant (per the overlay's production-relevance recognition mechanism) **or** the operator has explicitly approved the merge. The agent computes and pursues `MERGE_READINESS` identically for every PR; it executes the merge only when `PRODUCTION_READINESS` also holds. When the overlay declares no recognition mechanism, every change is non-production-relevant and the merge executes on `MERGE_READINESS` alone; a production-relevant change without approval keeps the merge withheld and the flow emits `AWAIT_APPROVAL` from `<action_tokens>`.

**terminal-green.** A required check in `statusCheckRollup` is a check run (`status` reaches `COMPLETED`, then a `conclusion`) or a status context (`state`). It is **terminal-green** only when terminal — `status == COMPLETED`, or `state ∈ {SUCCESS, ERROR, FAILURE}` — AND successful — `conclusion == SUCCESS`, or `state == SUCCESS`. A check that is non-terminal (`QUEUED` / `IN_PROGRESS` / `PENDING` / `EXPECTED`), terminal-but-not-success (`FAILURE` / `CANCELLED` / `TIMED_OUT` / `SKIPPED` / `NEUTRAL` / `ACTION_REQUIRED` / `ERROR`), or absent from the rollup is not terminal-green and blocks `MERGE_READINESS`.

**Acting on findings (validity and phase, never severity).** The agent acts on each finding by **validity** — whether it holds against its cited rule, product-local / language / spec-tree governance, and the PDR/ADR decisions; read those fresh and drop a finding they do not support — and by **phase**: before open (`REVIEW_READINESS`) apply every valid finding that belongs and split out of the changeset any whose fix is too large to belong — the split work leaves the diff and is captured in `ISSUES.md` / `PLAN.md`; on the open PR (`MERGE_READINESS`) fix every valid finding the CI review surfaces and re-push, with no deferral. Severity is the reviewer's reporting label; it never decides whether the agent acts on a finding, and the reviewer never decides whether the change merges.

**Reviewer-skipped-by-design (self-modifying-PR exception).** When `spec-tree-review / spec-tree-review` reports `conclusion: skipped` with cause "PR head differs from main" (GitHub Actions' identical-workflow-content gate), no current-head review exists for `MERGE_READINESS`. Post one PR-level comment containing exactly `<trigger-phrase> review` (e.g., `@spec-tree review`) to fire the mention reviewer (which has no identical-content gate), emit `MENTION_REVIEW_NEEDED:<trigger-phrase>`, and on the next heartbeat treat that workflow's posted findings as the current-head review. This applies to that skip cause only — not path-filter, branch-filter, or manual skips.

**Follow-up pushes.** The PR is ready from open; a follow-up push — fixing a valid CI finding, or a `<base_sync>` rebase — pushes to the ready PR and re-fires CI. There is no draft toggle and no `gh pr ready` step in the loop.

</authority_gates>

<heartbeat>

Waiting for CI runs, reviews, or check completion happens through the runtime timer, never in-shell. The consuming flow schedules the next inspection through the timer after opening a PR and after every follow-up push.

- **Claude Code:** `ScheduleWakeup` for a single delayed re-check or `/loop` for recurring re-inspection. Pass a continuation prompt that re-enters /managing-pr.
- **Codex:** thread automation. The runtime may start a new thread, so the prompt names the repository, PR number, branch, and the next repository-governed action. Cadence is minute-based (typically every 3 minutes). The prompt instructs Codex to inspect checks and all three review surfaces on each wake, report only material changes, and stop the heartbeat when the PR is merged, closed, or has no remaining repository-governed action.

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

**Handling is by validity and phase, never by severity.** Severity classifies the finding's nature for the reader; it is not a routing key. The consumer of a review validates each finding against its cited rule and the governing decisions, drops any the citation does not support, and acts on the rest by phase per `<authority_gates>`: before open (`REVIEW_READINESS`), apply every valid finding that belongs and split out of the changeset any whose fix is too large to belong; on the open PR (`MERGE_READINESS`), fix every valid finding the CI review surfaces, with no deferral. A `BLOCKING` label does not force an action the citation does not support, and a `FOLLOW-UP` label does not exempt a valid in-scope finding — validity and phase decide, and the reviewer never decides whether the change merges.

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
### BLOCKING [consistency]: path/to/file.py:42
Reference: <quote the standard from CLAUDE.md, skills, governance from decisions (PDR/ADR), or assertion from specs>
Evidence: <quote the diff or behavior and explain the disagreement between layers>
Required: <concrete change>
```

```text
### DEBT [standards]: path/to/file.py:97
Reference: <quote the standard from CLAUDE.md, skills, governance from decisions (PDR/ADR), or assertion from specs>
Evidence: <quote the diff or behavior and explain how it violates the standard>
Required: <concrete change>
```

```text
### FOLLOW-UP [architecture]: path/to/foo.compliance.test.ts
Reference: <quote the standard from CLAUDE.md, skills, governance from decisions (PDR/ADR), or assertion from specs>
Issue: <what is missing or worthy of improvement>
Track under: <ISSUES.md file or product-specific issue tracker>
```

</review_classification>

<action_tokens>

The managing flow emits exactly one of these tokens per heartbeat pass when no autonomous action fires. An autonomous fire — the merge under `MERGE_READINESS ∧ PRODUCTION_READINESS` — runs the command directly and does not emit a token. A routine `<base_sync>` rebase likewise runs directly and emits no token of its own; only a rebase conflict that cannot be resolved autonomously emits `SYNC_BASE`.

| Token                                    | Emitted when                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `WAIT_FOR_CHECKS`                        | A required check is non-terminal (running, queued, pending); not yet terminal-green. The heartbeat re-fires.                                                                                                                                                                                                                                                                                                                                                                                        |
| `WAIT_FOR_REVIEW`                        | Every other required check is terminal-green, but no current-head CI `spec-tree-review` has landed yet on any inspected surface.                                                                                                                                                                                                                                                                                                                                                                    |
| `FIX_FINDING:<item>`                     | The current-head CI review reports a valid finding (the agent judged it backed by its cited rule and governance). The agent fixes it and re-pushes; `<item>` carries the finding for triage, and its severity label is reporting only — validity and phase, not severity, drive the fix.                                                                                                                                                                                                            |
| `AWAIT_APPROVAL:<reason>`                | `MERGE_READINESS` holds but the change is production-relevant and the operator has not approved; `PRODUCTION_READINESS` withholds the merge pending explicit approval.                                                                                                                                                                                                                                                                                                                              |
| `MENTION_REVIEW_NEEDED:<trigger-phrase>` | The CI `spec-tree-review` reports `conclusion: skipped` with cause "PR head differs from main" (the PR modifies the reviewer's own workflow file). Post one PR-level comment containing exactly `<trigger-phrase> review` to fire the mention-triggered reviewer (which has no identical-content gate); reschedule the heartbeat to await its findings. The `review` suffix is the keyword the mention reviewer matches on — posting only the trigger phrase without it does not fire the reviewer. |
| `MERGE_BLOCKED:<reason>`                 | `MERGE_READINESS` fails for a concrete reason not covered by another token (for example a failed or absent required check, or a PR-state predicate).                                                                                                                                                                                                                                                                                                                                                |
| `SYNC_BASE`                              | A rebase onto the advanced base per `<base_sync>` hit a conflict that cannot be resolved autonomously; awaiting operator resolution. The heartbeat re-fires.                                                                                                                                                                                                                                                                                                                                        |
| `POST_MERGE_VERIFY`                      | PR merged; run post-merge verification per the project's Git workflow.                                                                                                                                                                                                                                                                                                                                                                                                                              |

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
- Waiting for CI, review, or checks is delegated to the runtime timer per `<heartbeat>`.
- All three surfaces in `<review_inspection>` are inspected after every push.
- Every finding is labeled with one of `BLOCKING` / `DEBT` / `FOLLOW-UP` — never a severity rank, never a legacy four-class label — and acted on by validity and phase, never by severity.
- Merge runs only when `MERGE_READINESS` and `PRODUCTION_READINESS` both hold: the current-head CI review has no valid finding, every other required check is terminal-green, branch hygiene and PR-state hold, and the change is non-production-relevant or operator-approved. `MERGE_READINESS` carries no time-based settle.
- Merge runs via rebase merge with inline branch deletion (`gh pr merge --rebase --delete-branch`) unless the overlay declares a different command — merge commit and squash are overlay opt-ins (overlay rationale documents the choice for human reviewers; the agent does not enforce it), not the agent's choice from the gate alone.
- Each pass that does not fire an autonomous action emits exactly one token from `<action_tokens>`.
- No `<self_reference>` violation appears in any artifact.

</success_criteria>
