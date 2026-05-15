---
name: standardizing-merging
user-invocable: false
description: >-
  Cross-cutting standards for the merge flow — branch hygiene, branch topology, push semantics, draft/ready lifecycle, heartbeat protocol, and three-surface review inspection.
  Loaded by other skills, not invoked directly.
allowed-tools: Read
---

<objective>
Canonical standards for moving a change from a feature branch to a merged pull request without polluting the branch graph, bypassing the upstream-safety check, burning expensive CI on guesses, polling CI in-shell, or missing review feedback that lands on the comments surface instead of the reviews surface. Every rule that opening-pr and managing-pr enforce at the merge-flow boundary lives here.
</objective>

<success_criteria>

A skill that loads this reference satisfies the merge-flow standards when, at minimum:

- Pre-flight gates (auth, clean tree, ahead of base, upstream safety, no existing PR) are run before any push
- Branch topology is classified (peer or stacked) before any push, with the matching gate passing
- Every push uses an explicit destination ref (`HEAD:refs/heads/<branch>`)
- Pull requests are opened as draft and promoted to ready only on explicit human instruction with the closure gate freshly passed
- Waiting for CI, review, or check resolution is delegated to the runtime timer (no shell `sleep`, no `gh pr checks --watch`, no `until`/`while` polling)
- Review state is inspected on all three surfaces — formal `reviews`, PR-level `comments`, AND review-thread comments via `gh api .../pulls/<n>/comments` — never one or two alone

</success_criteria>

<reference_note>
This is a reference skill. opening-pr and managing-pr load these standards. Do not invoke directly.
</reference_note>

<repo_local_overlay>
When another skill loads this reference inside a repository, check for `spx/local/merging.md` at the repository root. Read that file after this reference if it exists and apply it as the repo-local specialization (e.g., extra pre-flight checks, project-specific closure gate command, push command overrides, draft-lifecycle refinements).

The repo-local file CANNOT override the always-draft mandate — `gh pr create --draft` remains mandatory on every PR open, and promotion to ready remains a separate `gh pr ready` command.
</repo_local_overlay>

<branch_hygiene>

**Pre-flight checks — MUST pass before pushing or opening a PR, AND before every follow-up push.**

Each row states the **condition that must hold**; the failure response applies when the condition is not met.

| Condition (must hold)                                        | Failure response (when condition does not hold)                                            |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| Current branch is not `main`, `master`, or detached HEAD     | STOP. PRs are opened from feature branches.                                                |
| Working tree is clean (no uncommitted changes)               | STOP. Direct the user to `/committing-changes` or to stash.                                |
| Branch is at least one commit ahead of the resolved base     | STOP. Nothing to PR — verify the base branch.                                              |
| Branch is not behind the resolved base (no upstream commits) | Warn. Offer to rebase; proceed only if the user confirms.                                  |
| Branch topology is classified as peer or stacked             | STOP. Do not push an ambiguous branch graph for review.                                    |
| Work branch is not tracking the default branch               | STOP. Replace the upstream before pushing.                                                 |
| No PR already exists for this branch (initial push only)     | STOP. Surface the existing PR URL via `gh pr view --json url`.                             |
| `gh auth status` reports an authenticated token              | STOP. Resolve auth before continuing — non-interactive `gh` calls fail opaquely otherwise. |

**Commands:**

```bash
# Auth status (non-interactive gh calls fail opaquely without this)
gh auth status

# Branch identity
git branch --show-current

# Working tree state (empty output = clean)
git status --porcelain

# Resolve the base branch first — never hardcode "main"; repos may use
# develop, master, or another default, in which case main..HEAD is wrong.
base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git fetch origin "${base}"

# Commits ahead of base
git log --oneline "origin/${base}..HEAD"

# Diff stats against base
git diff "origin/${base}...HEAD" --stat

# Upstream safety — abort if the work branch tracks the default branch
# (push.default=tracking would route feature-branch commits to origin/main).
git branch -vv
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
if [ "${upstream}" = "origin/${base}" ]; then
  echo "STOP: work branch tracks the default branch" >&2
  exit 1
fi

# Existing PR for current branch — extract .url directly via --jq
existing_url=$(gh pr view --json url --jq '.url' 2>/dev/null)
[ -n "$existing_url" ] && echo "PR already exists: $existing_url"
```

The `exit 1` inside the upstream-safety check is read by the agent's Bash tool as a non-zero exit — that is the STOP. The flow halts; do not continue past a STOP without resolving the named condition.

</branch_hygiene>

<branch_topology>

**Classify topology before pushing.** Every PR branch is one of two shapes:

| Shape       | Meaning                                                                                      | Required handling                                                                                         |
| ----------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Peer branch | The PR targets the repository default branch and contains only its own review payload.       | Create from the current default branch. Refuse stale sibling merge commits.                               |
| Stacked     | The PR intentionally depends on another unmerged branch and targets that branch as its base. | Name the dependency in the PR body. Keep draft until the base merges, then reconstruct onto default base. |

**Peer-gate commands:**

```bash
base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git fetch origin "${base}"
# Exit code 1 means origin/${base} is NOT an ancestor of HEAD →
# peer gate fails. Either classify as stacked or repair the branch.
git merge-base --is-ancestor "origin/${base}" HEAD
# A non-empty result here means the branch carries merge commits from
# sibling work. Peer-gate criterion "no merge commits from sibling work" fails.
git log --merges "origin/${base}..HEAD"
git log --oneline "origin/${base}..HEAD"
git diff --name-only "origin/${base}...HEAD"
```

The peer gate passes only when:

- `origin/${base}` is an ancestor of `HEAD`
- the commit list contains only the intended payload
- the changed file list matches the PR scope
- the branch has no merge commits from sibling work (`git log --merges …` returns empty)

**Peer-gate failure path.** Pick exactly one of two repair actions before pushing:

1. **Repair as a peer branch** — when divergence is unintentional (stale sibling-merge commits crept in, the branch is missing recent default-branch commits, or it was created from the wrong base). Rebase onto `origin/${base}`, drop sibling merge commits, re-run the peer gate.
2. **Reclassify as stacked** — when the dependency on an unmerged base branch is intentional. Identify the actual base branch (see stacked-branch gate below), update the `<base>` argument used at `gh pr create` time, and run the stacked gate against it.

Do not push until one repair action completes and its gate passes.

**Stacked-branch gate:**

Before running the gate, identify `<previous-stack-branch>` from context — the parent branch the stack depends on. Sources, in order: the PR description's `Stack` or `Merge order` note (use the named ref); the branch naming convention if the product uses one; an explicit user instruction. If none of those sources yields a ref, invoke `AskUserQuestion` to ask the user for the base branch name before continuing; do not stall silently or guess.

```bash
base_branch="<previous-stack-branch>"
git fetch origin "${base_branch}"
git merge-base --is-ancestor "origin/${base_branch}" HEAD
git log --oneline "origin/${base_branch}..HEAD"
git diff --name-only "origin/${base_branch}...HEAD"
```

The stacked gate passes only when:

- the PR base is the previous stack branch
- the PR body has a `Stack` or `Merge order` note naming the base dependency
- the PR remains draft while the base branch is unmerged
- after the base branch merges, the branch is reconstructed or rebased onto the updated default branch before final merge

**Post-merge reconstruction.** Once the stack base merges, the author re-invokes `/opening-pr` (or runs the equivalent rebase manually) to re-target the PR at the default branch and re-classify it as a peer branch. GitHub auto-retargets the PR base on the API side, but the local branch must still be rebased onto the updated default and the manifest version re-evaluated against the new base.

**Repair rule:** If a branch has accumulated sibling merge commits and the intended payload is small, reconstruct from the current base and cherry-pick only the payload commits. Do this before review rather than publishing an ambiguous branch graph.

</branch_topology>

<push_semantics>

**Always push with an explicit destination ref.**

```bash
# First push (sets upstream)
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"

# Subsequent pushes
branch=$(git branch --show-current)
git push origin HEAD:refs/heads/"${branch}"
```

The bare `git push` and `git push -u origin <branch>` forms are forbidden because `push.default=tracking` would publish feature-branch commits to whatever upstream is configured locally — including `main` when the branch was created from `main` without an upstream reset. The `HEAD:refs/heads/<branch>` form makes the remote branch explicit and removes the dependency on local upstream configuration.

If the product defines a custom branch-push command for pull-request branches, follow the product convention from CLAUDE.md / AGENTS.md instead of bare `git push` — but the explicit destination ref must remain part of any custom command.

</push_semantics>

<draft_lifecycle>

**A pull request's draft/ready state is a cost signal to CI and a readiness signal to reviewers.** Most CI configurations gate expensive verification — full end-to-end suites, integration tests, deploy-then-verify workflows — behind `ready_for_review` while bot reviewers and lightweight checks (lint, unit) run on every push regardless. The lifecycle:

| Phase          | PR state      | What runs                                                         | What the author does                                                                                      |
| -------------- | ------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Open**       | draft         | Bot reviewers, lightweight checks, preview deployment             | Read bot feedback; decide what to address                                                                 |
| **Iterate**    | draft         | Same as Open — each follow-up push re-fires only the cheap checks | Address bot comments; refactor; push more commits; run local checks                                       |
| **Closure**    | draft → ready | Expensive verification fires once at the flip                     | Run the project's local closure gate; confirm pass; **the human author** issues the promotion instruction |
| **Post-ready** | ready         | Every push re-fires expensive verification                        | Revert to draft with `gh pr ready --undo` before pushing; flip back to ready when done                    |

**Rules:**

1. **Always open as draft.** Mandatory. `gh pr create --draft` on every PR open, no exceptions.
2. **Stay draft through the entire iteration phase.** Push as many commits as needed; bot reviewers and cheap checks run every time, expensive CI stays silent. The local closure gate (project-specific full-test command — examples: `pnpm check:full`, `make test`, `cargo test --all`; `spx/local/merging.md` may name a project-specific gate) is the author's responsibility during this phase.
3. **Promote to ready only when ready means ready, and only on explicit human instruction.** Agent inference that "the work looks done" never qualifies. The explicit instruction may take either of two forms: (a) a direct chat command from the user ("mark ready", "promote to ready"); or (b) a user-approved implementation plan that specifies opening a ready PR after the closure gate passes. Project-local rules in `spx/local/merging.md` may declare additional signal forms specific to the repository. In every case the promotion is a deliberate human signal: the local closure gate has just passed, the change is mergeable, and CI spends expensive budget on that signal. When the explicit instruction is a user-approved plan, `gh pr ready` runs immediately after the draft `gh pr create` — as a separate command, never folded into `gh pr create` itself.
4. **For post-ready follow-ups, default to reverting to draft first.** GitHub does not auto-revert state on push, so the default is `gh pr ready --undo <pr-number>` before the follow-up push; iterate while draft; promote again when the closure gate passes anew and the human author re-instructs the promotion. Project-local rules in `spx/local/merging.md` may permit keeping the PR ready when the project's closure gate has just re-passed immediately before the follow-up push — in that case the follow-up push re-fires expensive CI exactly once, with a fresh gate-passed signal backing it.

**Promotion command:**

```bash
# Promote draft → ready. This is a deliberate signal; expensive CI fires here.
gh pr ready <pr-number>

# Revert ready → draft.
gh pr ready --undo <pr-number>
```

**Confirm before promoting** (all four must hold):

- An explicit human instruction to mark the PR ready exists (chat command or user-approved plan; agent inference does NOT count).
- The project's local closure gate has just been run.
- The gate passed.
- The change is asserted mergeable as-is.

If any answer is no, stay in draft.

**The local closure gate is the author's responsibility, not CI's.** CI is the validation; the gate is the assertion that validation is worth spending budget on. Skipping the gate makes the ready flip a guess instead of a signal — and turns the rest of the team's CI budget into the cost of that guess.

</draft_lifecycle>

<heartbeat>

**Waiting for CI runs, reviews, or check completion never happens in-shell.**

After opening a PR or after a follow-up push, hand the wait to the runtime timer so the next inspection runs after GitHub has had time to process review workflows. This replaces shell waits, `gh pr checks --watch`, `gh run watch`, and polling loops.

**Claude Code:** use `/loop` for recurring re-inspection or `ScheduleWakeup` for a single delayed re-check. Pass the continuation prompt so the next firing resumes the review loop. Do not keep a shell process open for the wait.

**Codex:** use a thread automation or heartbeat. The runtime may start a new thread, so seed the heartbeat with the repository, PR number, branch, current thread purpose, and the next repository-governed action. Give it a minute-based cadence (typically every five minutes) and a durable prompt that instructs Codex to inspect checks, formal reviews, PR-level comments, and review-thread comments on each wake-up. The prompt MUST tell Codex to report only material changes and stop the heartbeat when the PR is merged, closed, or no further repository-governed action remains.

**One heartbeat per PR.** Whichever skill is the first to need a heartbeat for a given PR creates it; later skills reuse and refresh that heartbeat instead of creating a second one. Detect an existing heartbeat before creating; if one exists, update its prompt to reflect the current review-loop state.

</heartbeat>

<review_inspection>

**After opening a PR and after every follow-up push, inspect both review surfaces.**

Automated reviewers (and humans) often re-fire on follow-up pushes. They may post as **formal reviews** OR as **PR-level issue comments** OR as **review-thread comments on specific lines** — checking only one surface misses feedback. Run this once after each push, then triage:

```bash
# Formal reviews + PR-level issue comments
gh pr view <pr-number> --json reviews,comments \
  --jq '{
    reviews: [.reviews[] | {author: .author.login, state, submittedAt}],
    comments: [.comments[] | {author: .author.login, createdAt, excerpt: .body[0:160]}]
  }'

# Review-thread comments tied to specific lines
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments \
  --jq '.[] | {author: .user.login, path, line, createdAt: .created_at, excerpt: .body[0:160]}'
```

Compare timestamps against the most recent push. New entries after that push are re-reviews of the latest state — read them in full before declaring the PR done. Never assume "no new review" without checking all three surfaces.

</review_inspection>

<cross_cutting_nevers>

These NEVERs cut across the named sections above. Each one is enforced by the section in parentheses; this list exists so consuming skills can cite it without re-stating the rule body.

1. NEVER push from `main` — feature branches only.
2. NEVER push without an explicit destination ref (`<push_semantics>`).
3. NEVER open a PR without `--draft` (`<draft_lifecycle>`).
4. NEVER promote draft → ready without explicit human instruction AND a freshly-passed closure gate (`<draft_lifecycle>` rule 3).
5. NEVER `gh pr checks --watch`, `gh run watch`, `until`/`while` polling, or in-shell `sleep` to wait for CI (`<heartbeat>`).
6. NEVER check only `reviews` after a push (`<review_inspection>`).
7. NEVER include self-reference in any merge-flow artifact — no "Claude", "AI", "agent", "Co-Authored-By: Claude".
8. NEVER push an ambiguous branch graph (`<branch_topology>`).
9. NEVER duplicate the heartbeat — one per PR (`<heartbeat>`).

</cross_cutting_nevers>
