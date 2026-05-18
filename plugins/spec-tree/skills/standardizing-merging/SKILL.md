---
name: standardizing-merging
user-invocable: false
description: >-
  Shared vocabulary for the PR flow — pre-flight predicates, branch topology gate, push command, PR authority gate, four-class review classification, three review surfaces, action tokens, and repo-local overlay topics.
  Loaded by /opening-pr and /managing-pr.
allowed-tools: Read
---

<objective>
The shared vocabulary the two PR flows consume. /opening-pr walks the opening flow (one-shot, linear, terminates at exit). /managing-pr walks the managing flow (loop body, re-enters per heartbeat fire). This skill is referenced, not flow-shaped — it defines the concepts, gates, commands, and tokens the two flows invoke. There is no flow here.
</objective>

<repo_local_overlay>
When loaded inside a repository, check for `spx/local/merging.md` at the repository root. Read it after this reference if present and apply it as the repo-local specialization. Topics the overlay MAY refine:

- Extra pre-flight checks beyond `<branch_hygiene>`.
- The project-specific closure gate command.
- Push command overrides — the explicit destination ref form must be preserved.
- **Draft-promotion authority** — whether `gh pr ready` runs autonomously when the PR authority gate is green (the gate-green-autonomous default in `<pr_authority_gate>`) or requires explicit human instruction.
- **Merge authority** — whether `gh pr merge` runs autonomously when the PR authority gate is green (the gate-green-autonomous default in `<pr_authority_gate>`) or requires explicit human instruction.
- **Production-class recognition** — the mechanism by which the project classifies a PR as production-class (label, branch prefix, file pattern, manifest declaration). Production-class PRs bypass gate-green-autonomous authority for both actions.
- Keep-ready signal forms — project-specific rules for keeping a PR ready across follow-up pushes when the closure gate has just re-passed.
- **Merge command** — which `gh pr merge` flags the project uses (rebase merge, merge commit, squash; whether `--delete-branch` runs inline or as a separate `git push origin --delete <branch>` to avoid multi-worktree cleanup failures).

If `spx/local/merging.md` is absent or silent on a topic, the defaults in this reference apply. When the overlay declares no production-class recognition mechanism and a PR cannot otherwise be classified, the gate withholds autonomous authority rather than guess.

The overlay cannot override the always-draft mandate — `gh pr create --draft` is mandatory on every PR open. Promotion to ready remains a separate `gh pr ready` command; the overlay's draft-promotion-authority topic governs who authorizes the promotion (gate evaluation versus explicit human instruction), not whether the promotion command runs separately.
</repo_local_overlay>

<branch_hygiene>

Conditions that must hold before every push (initial or follow-up). Failure stops the calling flow.

| Condition (must hold)                                        | Failure response                                                                           |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| Current branch is not `main`, `master`, or detached HEAD     | STOP. PRs are opened from feature branches.                                                |
| Working tree is clean (no uncommitted changes)               | STOP. Direct the user to /committing-changes or to stash.                                  |
| Branch is at least one commit ahead of the resolved base     | STOP. Nothing to PR — verify the base branch.                                              |
| Branch is not behind the resolved base (no upstream commits) | Warn. Offer to rebase; proceed only if the user confirms.                                  |
| Branch topology is classified as peer or stacked             | STOP. See `<branch_topology>`.                                                             |
| Work branch is not tracking the default branch               | STOP. Replace the upstream before pushing.                                                 |
| No PR already exists for this branch (initial push only)     | STOP. Surface the existing PR URL via `gh pr view --json url`.                             |
| `gh auth status` reports an authenticated token              | STOP. Resolve auth before continuing — non-interactive `gh` calls fail opaquely otherwise. |

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

| Shape   | Meaning                                                                               | Required handling                                                                                         |
| ------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Peer    | Targets the repository default branch and contains only its own review payload.       | Create from the current default branch. Refuse stale sibling merge commits.                               |
| Stacked | Intentionally depends on another unmerged branch and targets that branch as its base. | Name the dependency in the PR body. Keep draft until the base merges, then reconstruct onto default base. |

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

**Post-merge reconstruction.** Once the stack base merges, re-invoke /opening-pr (or rebase manually) to re-target the PR at the default branch and re-classify as peer. GitHub auto-retargets the PR base on the API side, but the local branch must still be rebased onto the updated default and the manifest version re-evaluated against the new base.

</branch_topology>

<push_semantics>

Always push with an explicit destination ref:

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"          # first push
git push    origin HEAD:refs/heads/"${branch}"          # subsequent pushes
```

The bare `git push` and `git push -u origin <branch>` forms are forbidden because `push.default=tracking` would publish feature-branch commits to whatever upstream is configured locally — including `main` when the branch was created from `main` without an upstream reset. The `HEAD:refs/heads/<branch>` form makes the remote branch explicit and removes the dependency on local upstream configuration.

If the product defines a custom branch-push command, follow the product convention from CLAUDE.md / AGENTS.md — the explicit destination ref must remain part of any custom command.

</push_semantics>

<pr_authority_gate>

A pull request's draft/ready state is a cost signal to CI and a readiness signal to reviewers. CI typically gates expensive verification behind `ready_for_review` while bot reviewers and lightweight checks run on every push regardless. Two transitions matter:

- **Promotion** (draft → ready): fires expensive CI.
- **Merge**: publishes the change to the base branch.

Both transitions are gated by the **PR authority gate**, evaluated at the moment each action becomes applicable. Promotion-time evaluation reads draft-phase predicates; merge-time evaluation reads ready-phase predicates after CI converges.

**Predicates** (all must hold for the applicable action):

- The project's local closure gate has been run against the latest pushed commit and passed. The local closure gate is the author's responsibility, not CI's — CI is the validation; the closure gate is the assertion that validation is worth spending budget on.
- All required checks on the PR's `statusCheckRollup` are terminal-green for the current head. Any queued, in-progress, pending, failing, cancelled, timed-out, missing, or ambiguous required check blocks authority.
- At least one current-head four-class review on an inspected surface (see `<review_inspection>`) has no unresolved `BLOCKING` or `NEEDS-ANSWER`.
- The latest pushed commit is at least five minutes old at evaluation time, so review automation has time to respond without shell polling.
- `<branch_hygiene>` passes, including the upstream-safety check.
- **For merge only:** PR state is `OPEN`, `isDraft` is false, the inspected head SHA matches the branch head fetched from origin, and the PR branch is rebased onto current `origin/<base>` or is a fast-forward descendant.
- The PR carries no project-declared production-class markers (per the overlay's production-class recognition mechanism).

**Per-action authority model** (set independently per action in `spx/local/merging.md`):

- **Gate-green-autonomous (default).** Gate-green is sufficient authority — the consuming flow runs the action's command (`gh pr ready` for promotion, the project's merge command for merge) without a separate explicit human instruction.
- **Overlay-requires-human.** Gate-green is necessary but not sufficient. The consuming flow emits the corresponding action token from `<action_tokens>` and waits for the operator's explicit instruction.

**Post-ready follow-up rule.** GitHub does not auto-revert state on push. Default: `gh pr ready --undo <pr-number>` before any follow-up push; iterate while draft; the gate re-evaluates after the next push under the same authority model. The overlay's keep-ready signal forms may permit keeping the PR ready when the closure gate has just re-passed immediately before the follow-up push — in that case the follow-up push re-fires expensive CI exactly once with a fresh gate-passed signal.

</pr_authority_gate>

<heartbeat>

Waiting for CI runs, reviews, or check completion happens through the runtime timer, never in-shell. The consuming flow schedules the next inspection through the timer after opening a PR and after every follow-up push.

- **Claude Code:** `ScheduleWakeup` for a single delayed re-check or `/loop` for recurring re-inspection. Pass a continuation prompt that re-enters /managing-pr.
- **Codex:** thread automation. The runtime may start a new thread, so the prompt names the repository, PR number, branch, and the next repository-governed action. Cadence is minute-based (typically every five minutes). The prompt instructs Codex to inspect checks and all three review surfaces on each wake, report only material changes, and stop the heartbeat when the PR is merged, closed, or has no remaining repository-governed action.

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

Every review finding — whether produced by a reviewer (outgoing feedback) or by an author triaging incoming feedback — is labeled with exactly one of four classes. The taxonomy is shared so reviewer output and author triage use the same vocabulary; nothing has to be translated between them.

| Class          | Receiver action             | Use when                                                                                                                                                         |
| -------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BLOCKING`     | Fix in this PR before merge | The PR introduces a correctness bug, security risk, data-loss risk, production-safety risk, broken required validation, secret exposure, or direct policy break. |
| `NEEDS-ANSWER` | Answer before merge         | A required fact is missing from the diff or PR context, and the answer can clear the concern or convert it to `BLOCKING`.                                        |
| `FOLLOW-UP`    | Track outside this PR       | The concern is valid, but fixing it would widen the PR.                                                                                                          |
| `NOTE`         | No action expected          | Context, praise, explanation, or an observation that does not create work.                                                                                       |

`BLOCKING` and `NEEDS-ANSWER` drive the active PR loop. `FOLLOW-UP` items belong in a short summary and name the owning tracking location when retention is useful (e.g., `Track under: spx/.../ISSUES.md`). `NOTE` items are optional and must be omitted when they add noise.

**Severity-rank labels MUST NOT replace the four classes.** No `P0` / `P1` / `P2` / `P3`, no `critical` / `high` / `medium` / `low`, no `minor` / `nit` headings. Risk words may appear inside rationale only when they add concrete evidence, never as a finding's primary label.

**If a review has no `BLOCKING` or `NEEDS-ANSWER` items, say so directly.** Do not manufacture lower-priority findings to prove that review happened.

Comment format examples:

```text
BLOCKING [correctness]: path/to/file.py:42
Evidence: The changed branch now raises on an empty profile list because ...
Required before merge: Preserve the previous no-op behavior or add evidence that the new failure is intended.
```

```text
NEEDS-ANSWER [scope]: path/to/file.py:108
Evidence: The new helper duplicates logic in <other-module>, but the diff does not say why it cannot reuse it.
Question: Is the duplication intentional? If not, reuse and drop the duplicate.
```

```text
FOLLOW-UP [test-evidence]: spx/.../tests/test_x.py
Evidence: The test covers the happy path but not rollback.
Track under: spx/.../ISSUES.md.
```

```text
NOTE [praise]: path/to/file.py:200
The new error path is clearer than what was there. No action.
```

The bracketed dimension names the concern category and is free-form.

</review_classification>

<action_tokens>

The managing flow emits exactly one of these tokens per heartbeat pass when no autonomous action fires. An autonomous fire (promotion under gate-green-autonomous; merge under gate-green-autonomous) runs the command directly and does not emit a token.

| Token                      | Emitted when                                                                                                                                       |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `WAIT_FOR_CHECKS`          | Required checks are running, queued, pending, or skipped-required; heartbeat will re-fire.                                                         |
| `WAIT_FOR_REVIEW`          | Checks green; no current-head four-class review yet on any inspected surface.                                                                      |
| `WAIT_FOR_REVIEW_WINDOW`   | Checks and review present, but five minutes have not elapsed since the latest push.                                                                |
| `FIX_BLOCKING:<item>`      | At least one `BLOCKING` item remains.                                                                                                              |
| `ANSWER_NEEDED:<item>`     | At least one `NEEDS-ANSWER` item remains.                                                                                                          |
| `MARK_READY`               | Promotion-time predicates pass under overlay-requires-human draft-promotion authority; awaiting the operator's explicit promotion instruction.     |
| `AWAIT_MERGE_INSTRUCTION`  | Merge predicates pass under overlay-requires-human merge authority; awaiting the operator's explicit merge instruction.                            |
| `PRODUCTION_HOLD:<reason>` | PR is project-recognized as production-class; autonomous authority is withheld for both actions regardless of other predicates and overlay topics. |
| `MERGE_BLOCKED:<reason>`   | Merge gate failed for a concrete reason not covered by another token.                                                                              |
| `SYNC_BASE`                | Base branch has advanced; rebase needed before further action.                                                                                     |
| `POST_MERGE_VERIFY`        | PR merged; run post-merge verification per the project's Git workflow.                                                                             |

</action_tokens>

<self_reference>

No "Claude", "AI", "agent", "Co-Authored-By: Claude", or similar identity strings in any merge-flow artifact: branch names, commit messages, PR titles, PR bodies, review comments.

</self_reference>

<success_criteria>

The two flows that consume this vocabulary satisfy their contracts when, at minimum:

- `<branch_hygiene>` predicates hold before every push (initial and every follow-up).
- `<branch_topology>` is classified before every push, with the matching gate passing.
- Every push uses the explicit destination ref form from `<push_semantics>`.
- PRs are opened as draft; promotion runs only when `<pr_authority_gate>` authorizes it under the project's draft-promotion-authority overlay.
- Waiting for CI, review, or checks is delegated to the runtime timer per `<heartbeat>`.
- All three surfaces in `<review_inspection>` are inspected after every push.
- Every finding is labeled with one of `BLOCKING` / `NEEDS-ANSWER` / `FOLLOW-UP` / `NOTE` — never a severity rank.
- Merge runs only when the merge predicates of `<pr_authority_gate>` hold under the project's merge-authority overlay.
- Each pass that does not fire an autonomous action emits exactly one token from `<action_tokens>`.
- No `<self_reference>` violation appears in any artifact.

</success_criteria>
