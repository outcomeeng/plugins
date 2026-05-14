---
name: opening-pr
description: >-
  ALWAYS invoke this skill when opening a pull request, creating a PR, or pushing a branch for review.
  NEVER run gh pr create without this skill.
allowed-tools: Read, Glob, Grep, Bash
---

<objective>
Open a pull request for the current branch with a curated title and body that follow Conventional Commits and a structured PR template, after pre-flight branch-hygiene checks.
</objective>

<success_criteria>

A successful PR open has:

- Branch hygiene verified (not main/master, working tree clean, branch ahead of base)
- Branch topology classified as a peer branch or a stacked branch before push
- Title under 70 chars in Conventional Commits format (matches `/committing-changes`)
- Body delivered to `gh` on stdin via `--body-file -` (real newlines, no `\n` escapes, no temp file)
- Always opened as draft; promoted to ready-for-review only when the author asserts the change is mergeable and the project's local closure gate has just passed (see `<draft_lifecycle>`)
- Runtime heartbeat created or requested immediately after PR creation for the first review/check re-inspection
- No self-reference in title, body, or branch name
- PR URL printed for the user

</success_criteria>

<context>

This skill does NOT:

- Stage, commit, or amend (use `/committing-changes`)
- Force-push or rewrite history
- Merge, squash, or close the PR
- Modify global git configuration or CI/CD workflows
- Watch CI runs (polling is forbidden — see `<critical_rules>`)

</context>

<project_specialization>
After loading this skill, check whether `spx/local/opening-pr.md` exists (path is relative to the repository root). If it does, read it and apply its rules as product-specific additions to the PR workflow (e.g., extra pre-flight checks, marketplace-specific template sections, push-command overrides, project-specific closure-gate commands). The project-level file cannot override the always-draft policy in critical rule 5 — it can only add detail to the lifecycle (e.g., name the project's closure-gate command, list project-specific reviewers, refine the post-ready guidance).
</project_specialization>

<context_gathering>

**Before opening a PR, gather context:**

| Source                        | Gather                                                          |
| ----------------------------- | --------------------------------------------------------------- |
| **git status**                | Working tree state — clean? uncommitted changes?                |
| **git branch --show-current** | Current branch name (refuse if main/master/HEAD)                |
| **git log <base>..HEAD**      | Commits to be included (drives title and body content)          |
| **gh repo view**              | Default base branch (usually `main`)                            |
| **CLAUDE.md / AGENTS.md**     | Product-specific PR conventions, custom template, push commands |
| **Conversation**              | Issue or spec node references for the Refs footer               |

</context_gathering>

<branch_hygiene>

**Pre-flight checks — MUST pass before pushing or opening the PR.**

Each row states the **condition that must hold**; the failure response applies when the condition is not met.

| Condition (must hold)                                        | Failure response (when condition does not hold)                                            |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| Current branch is not `main`, `master`, or detached HEAD     | STOP. PRs are opened from feature branches.                                                |
| Working tree is clean (no uncommitted changes)               | STOP. Direct the user to `/committing-changes` or to stash.                                |
| Branch is at least one commit ahead of the resolved base     | STOP. Nothing to PR — verify the base branch.                                              |
| Branch is not behind the resolved base (no upstream commits) | Warn. Offer to rebase; proceed only if the user confirms.                                  |
| Branch topology is classified as peer or stacked             | STOP. Do not push an ambiguous branch graph for review.                                    |
| Work branch is not tracking the default branch               | STOP. Replace the upstream before pushing.                                                 |
| No PR already exists for this branch                         | STOP. Surface the existing PR URL via `gh pr view --json url`.                             |
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
# The agent runs this as a Bash tool call; a non-zero exit (from `exit 1`
# below) is read as a tool failure and stops the flow — that is the STOP.
git branch -vv
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
if [ "${upstream}" = "origin/${base}" ]; then
  echo "STOP: work branch tracks the default branch" >&2
  exit 1
fi

# Existing PR for current branch — extract .url directly via --jq
# (gh exits non-zero when no PR exists; redirect stderr to suppress its message)
existing_url=$(gh pr view --json url --jq '.url' 2>/dev/null)
[ -n "$existing_url" ] && echo "PR already exists: $existing_url"
```

</branch_hygiene>

<branch_topology>

**Classify topology before pushing.**

Every PR branch is one of two shapes:

| Shape       | Meaning                                                                                      | Required handling                                                                                         |
| ----------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Peer branch | The PR targets the repository default branch and contains only its own review payload.       | Create from the current default branch. Refuse stale sibling merge commits.                               |
| Stacked     | The PR intentionally depends on another unmerged branch and targets that branch as its base. | Name the dependency in the PR body. Keep draft until the base merges, then reconstruct onto default base. |

**Peer branch gate:**

```bash
base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git fetch origin "${base}"
# Exit code 1 means origin/${base} is NOT an ancestor of HEAD →
# peer gate fails. Either classify as stacked or repair the branch.
git merge-base --is-ancestor "origin/${base}" HEAD
# A non-empty result here means the branch carries merge commits from
# sibling work. The peer-gate criterion "no merge commits from sibling
# work" fails; follow the peer-gate failure path below.
git log --merges "origin/${base}..HEAD"
git log --oneline "origin/${base}..HEAD"
git diff --name-only "origin/${base}...HEAD"
```

The peer gate passes only when:

- `origin/${base}` is an ancestor of `HEAD`
- the commit list contains only the intended payload
- the changed file list matches the PR scope
- the branch has no merge commits from sibling work (`git log --merges …` returns empty)

**Peer-gate failure path.** The peer gate fails when either (a) `git merge-base --is-ancestor "origin/${base}" HEAD` exits non-zero (origin/base is not an ancestor of HEAD), or (b) `git log --merges "origin/${base}..HEAD"` returns non-empty output (the branch carries merge commits from sibling work). In either case, pick exactly one of two repair actions before pushing:

1. **Repair as a peer branch** — when the divergence is unintentional (stale merges from sibling work crept in, the branch is missing recent default-branch commits, or the local branch was created from the wrong base). Rebase onto `origin/${base}`, drop sibling merge commits, and re-run the peer gate.
2. **Reclassify as stacked** — when the dependency on an unmerged base branch is intentional. Identify the actual base branch (see the stacked-branch gate below), update the `<base>` argument used at `gh pr create` time, and run the stacked gate against it.

Do not push until one of the two repair actions completes and its gate passes.

**Stacked branch gate:**

Before running the gate, identify `<previous-stack-branch>` from context — the parent branch the stack depends on. Sources, in order: the PR description's `Stack` or `Merge order` note (use the named ref); the branch naming convention if the product uses one; an explicit user instruction. Do not run the gate against a guessed base — substitute a ref resolved from one of the sources above and proceed only then. When none of those sources yields a ref, invoke `AskUserQuestion` to ask the user for the base branch name before continuing; do not stall silently or guess.

```bash
base_branch="<previous-stack-branch>"
git fetch origin "${base_branch}"
# Same exit-code semantics as the peer gate: 1 means
# origin/${base_branch} is NOT an ancestor → the stack base is wrong.
git merge-base --is-ancestor "origin/${base_branch}" HEAD
git log --oneline "origin/${base_branch}..HEAD"
git diff --name-only "origin/${base_branch}...HEAD"
```

The stacked gate passes only when:

- the PR base is the previous stack branch
- the PR body has a `Stack` or `Merge order` note naming the base dependency
- the PR remains draft while the base branch is unmerged
- after the base branch merges, the branch is reconstructed or rebased onto the updated default branch before final merge

**Post-merge reconstruction.** Once the stack base merges, the author re-invokes `/opening-pr` (or runs the equivalent rebase manually) to re-target the PR at the default branch and re-classify it as a peer branch. The reconstruction does not happen automatically — GitHub auto-retargets the PR base on the API side, but the local branch must still be rebased onto the updated default and the manifest version re-evaluated against the new base. Track this as a follow-up the moment the stack base lands.

**Repair rule:**

If a branch has accumulated sibling merge commits and the intended payload is small, reconstruct from the current base and cherry-pick only the payload commits. Do this before review rather than publishing an ambiguous branch graph.

</branch_topology>

<title_format>

**The PR title is one Conventional Commits subject line under 70 characters.**

**Source rules:**

- Single commit on the branch → use that commit's subject as-is (already conforms to `/committing-changes`).
- Multiple commits → synthesize a title that captures the dominant type and scope.

**Synthesis procedure for multi-commit branches:**

1. Read all commit subjects: `git log --format=%s <base>..HEAD`.
2. Pick the dominant type (the type that describes the umbrella change).
3. Pick the dominant scope, or omit if changes span scopes.
4. Write a description that summarizes the umbrella change — not a list of commits.
5. Verify the result is ≤70 chars; trim or drop scope if needed.

**Examples:**

```text
# Single commit on branch
feat(auth): add OAuth2 token refresh

# Multi-commit feature branch
feat(auth): add SMS and authenticator-app two-factor support

# Multi-commit refactor spanning files
refactor: extract validation into dedicated module

# Multi-commit fix
fix(parser): handle nested expressions and empty operands
```

**Rules** (mirror `/committing-changes`):

- ≤70 chars
- Imperative mood, no period
- No `chore:` — pick the specific type
- No state words ("missing", "broken", "wrong")
- No self-reference ("Claude", "AI", "agent")

</title_format>

<body_template>

**The PR body is markdown prose passed to `gh` on stdin via `--body-file -`.**

Default template — adapt sections to the change type; drop or expand as the work warrants:

```text
## Summary

- <one or two short bullets describing the change at a glance>

## Background

<context: what motivated this change, what problem it solves, what user-visible behavior it affects>

## Changes

- <bulleted list of what was modified, grouped by area>

## Test plan

- [ ] <verification step the reviewer can run>
- [ ] <additional check>

## Refs

- <spec nodes touched, e.g. spx/21-foo.enabler/32-bar.outcome>
- <issue refs, e.g. Closes #123>
```

**Adapt by change type:**

| Change type | Adaptation                                                                                |
| ----------- | ----------------------------------------------------------------------------------------- |
| Bug fix     | Add a **Root cause** subsection in Background. Test plan includes the failing repro.      |
| Feature     | Expand Summary into a short user-facing description. Test plan lists acceptance criteria. |
| Refactor    | State the no-behavior-change invariant. Test plan: "existing tests still pass".           |
| Spec        | Link the spec nodes affected; describe what is now declared.                              |
| Docs        | Drop Test plan; describe what readers gain.                                               |

**Rules:**

- Real newlines — never embed `\n` in `--body "..."`. Always use `--body-file`.
- No self-reference — no "Claude", no "Co-Authored-By: Claude", no agent attribution.
- Body explains WHY for the reviewer; the diff already shows WHAT.
- Reference spec nodes by path (e.g. `spx/21-foo.enabler/32-bar.outcome`), not by ADR/PDR ID.
- Reviewers read top-down — keep Summary scannable, push detail to Background.

</body_template>

<workflow>

**Step 1: Push the branch**

```bash
# First push (sets upstream)
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"

# Subsequent pushes
branch=$(git branch --show-current)
git push origin HEAD:refs/heads/"${branch}"
```

If the product defines a custom push command (e.g., `just push-marketplace` for the outcomeeng marketplace repo), follow the product convention from CLAUDE.md / AGENTS.md instead of bare `git push`.

**Step 2: Open the PR with body piped via stdin**

Pass the curated body to `gh pr create` on stdin via `--body-file -`. A Bash heredoc preserves real newlines, avoids any temp file, and removes the cleanup step (and its permission prompt for users with strict `Bash(rm:*)` rules):

```bash
GIT_TERMINAL_PROMPT=0 gh pr create \
  --draft \
  --title "<conventional-commits subject under 70 chars>" \
  --body-file - \
  --head "$(git branch --show-current)" <<'EOF'
## Summary

- <bullet>

## Background

<prose>

## Test plan

- [ ] <step>

## Refs

- <ref>
EOF
```

The single-quoted heredoc terminator (`<<'EOF'`) disables shell expansion inside the body — backticks, `$variables`, and `!` pass through literally. Use the unquoted form (`<<EOF`) only when the body must interpolate shell variables, and never embed multi-line content in `--body "..."` — gh does not expand `\n` escapes.

**Flag rationale:**

- `--draft` — mandatory on every `gh pr create`. Promotion to ready-for-review is a separate, explicit step performed via `gh pr ready` in Step 6, with the lifecycle prerequisites checked first. See `<draft_lifecycle>` for the rationale.
- `--title` and `--body-file -` — explicit title plus body-from-stdin matches `/committing-changes` conventions without writing to disk.
- `--head` — the feature branch; prevents gh from prompting for fork/push targets.
- `--base` — omit only for peer branches targeting the repo default; specify the previous stack branch for stacked PRs.
- `GIT_TERMINAL_PROMPT=0` — disables git credential prompts. (gh detects non-TTY stdin/stdout and skips its own prompts automatically; no `GH_*` env var is needed.)

**Do not use `--fill` with this skill.** `--fill` is gh's autofill from commit messages. If both `--fill` and `--body-file` are passed, the explicit body wins — but `--fill` is then dead weight. Use the curated body alone.

**Step 3: Surface the PR URL**

`gh pr create` prints the URL on the last line of stdout. Surface it to the user verbatim.

**Step 4: Create the review/check heartbeat**

After opening the PR, create or request a thread heartbeat with the runtime's automation tool so the first re-inspection runs after GitHub has had time to process review workflows. This replaces shell waits, `gh run watch`, and polling loops.

For Codex, use a thread automation or heartbeat. The runtime may start a new thread, so seed the heartbeat with the repository, PR number, branch, current thread purpose, and the next repository-governed action. Give it a minute-based cadence, for example every five minutes, and a durable prompt that instructs Codex to inspect checks, formal reviews, PR-level comments, and review-thread comments on each wake-up. The prompt MUST tell Codex to report only material changes and stop the heartbeat when the PR is merged, closed, or no further repository-governed action remains.

For Claude Code, use the runtime timer mechanism documented by the product, such as `/loop` or `ScheduleWakeup`, with the same continuation prompt. Do not keep a shell process open for the wait.

**Step 5: After follow-up pushes, check for re-reviews**

Automated reviewers (and humans) often re-fire on follow-up pushes. They may post as **formal reviews** OR as **PR-level issue comments** — checking only one surface misses half the feedback. Run this once after each follow-up push, then triage:

```bash
gh pr view <pr-number> --json reviews,comments \
  --jq '{
    reviews: [.reviews[] | {author: .author.login, state, submittedAt}],
    comments: [.comments[] | {author: .author.login, createdAt, excerpt: .body[0:160]}]
  }'
```

Compare timestamps against your last push. New entries after the push are re-reviews of the latest state — read them in full before declaring the PR done. Never assume "no new review" without checking both surfaces.

**Step 6 (only on explicit human instruction AND the prerequisites in `<draft_lifecycle>` are met): Mark ready for review**

```bash
# Promote draft → ready. This is a deliberate signal; expensive CI fires here.
gh pr ready <pr-number>

# Revert ready → draft. Use this before pushing follow-up commits to a ready PR
# so subsequent pushes do not re-fire expensive verification.
gh pr ready --undo <pr-number>
```

Confirm before promoting:

- A human author has explicitly instructed the promotion (not an agent inference that the work looks done).
- The author just ran the project's local closure gate.
- The gate passed.
- The author asserts the change is mergeable as-is.

If any answer is no, stay in draft.

</workflow>

<draft_lifecycle>

**A pull request's draft/ready state is a cost signal to CI and a readiness signal to reviewers.** Most CI configurations gate expensive verification — full end-to-end suites, integration tests, deploy-then-verify workflows — behind `ready_for_review` while bot reviewers and lightweight checks (lint, unit) run on every push regardless. The lifecycle this skill enforces:

| Phase          | PR state      | What runs                                                         | What the author does                                                                                      |
| -------------- | ------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Open**       | draft         | Bot reviewers, lightweight checks, preview deployment             | Read bot feedback; decide what to address                                                                 |
| **Iterate**    | draft         | Same as Open — each follow-up push re-fires only the cheap checks | Address bot comments; refactor; push more commits; run local checks                                       |
| **Closure**    | draft → ready | Expensive verification fires once at the flip                     | Run the project's local closure gate; confirm pass; **the human author** issues the promotion instruction |
| **Post-ready** | ready         | Every push re-fires expensive verification                        | Revert to draft with `gh pr ready --undo` before pushing; flip back to ready when done                    |

**Rules:**

1. **Always open as draft.** The PR enters the iteration phase. Mandatory — see critical rule 5.
2. **Stay draft through the entire iteration phase.** Push as many commits as needed; bot reviewers and cheap checks run every time, expensive CI stays silent. The local closure gate (project-specific full-test command — examples: `pnpm check:full`, `make test`, `cargo test --all`; see `spx/local/opening-pr.md` if the project defines its own) is the author's responsibility during this phase.
3. **Promote to ready only when ready means ready, and only on explicit human instruction.** Never promote as a side effect of opening, pushing, or "the work looks done" — agent inference is not a substitute for the human author saying "this is ready." Promotion is a deliberate human signal: the author has just run the local closure gate, it passed, and the change is mergeable. CI spends expensive budget on that signal.
4. **For post-ready follow-ups, always revert to draft first.** GitHub does not auto-revert state on push. If review feedback after the ready flip requires more commits, run `gh pr ready --undo <pr-number>`, iterate while draft, then promote again when the closure gate passes anew and the human author re-instructs the promotion. No exception — "just one small fix" is the path every PR walks into uncontrolled expensive-CI cost.

**The local closure gate is the author's responsibility, not CI's.** CI is the validation; the gate is the assertion that validation is worth spending budget on. Skipping the gate makes the ready flip a guess instead of a signal — and turns the rest of the team's CI budget into the cost of that guess.

</draft_lifecycle>

<critical_rules>

1. **NEVER push from `main` with bare `git push`** — use the product's push command (e.g., `just push-marketplace`) when one is defined.
2. **NEVER include self-reference** in title, body, or branch name — no "Claude", "AI", "agent", "Co-Authored-By: Claude".
3. **NEVER use `--body "..."` for multi-line content** — gh does not expand `\n`. Use `--body-file`.
4. **NEVER use `--fill`** with this skill — it adds nothing once `--body-file` is present.
5. **ALWAYS OPEN AS DRAFT** — `--draft` is mandatory on `gh pr create`, with no exceptions. Promotion to ready-for-review is a separate, deliberate signal performed via `gh pr ready` (see `<draft_lifecycle>` and Step 6), and only on explicit human instruction. Never combine "open" and "promote" in the same action, even when a user appears to ask for a ready PR — open as draft, then wait for the human to issue the promotion as a second step so the lifecycle prerequisites are checked.
6. **ALWAYS CREATE OR REQUEST A PR HEARTBEAT AFTER OPENING** — schedule a thread heartbeat for review/check re-inspection immediately after surfacing the PR URL. If the runtime cannot create the heartbeat directly, ask the user to create one with a prompt that can resume the review loop from a new thread.
7. **NEVER `gh run watch`** — for CI status, surface a single `gh pr checks` or `gh run view` and stop. Polling is forbidden.
8. **AFTER FOLLOW-UP PUSHES, check both `reviews` AND `comments`** — bots often post re-reviews as PR-level issue comments rather than formal reviews. Checking only `reviews` will silently miss re-feedback on the latest commit.
9. **CLASSIFY BRANCH TOPOLOGY BEFORE PUSH** — peer branches target the default branch and contain only their payload; stacked branches target the previous stack branch and remain draft until their base merges.
10. **PUSH WITH AN EXPLICIT DESTINATION REF** — use `HEAD:refs/heads/<branch>` so local upstream configuration cannot publish to the wrong remote branch.

</critical_rules>

<commands_reference>

```bash
# Pre-flight (resolve base; never hardcode main)
gh auth status
git status --porcelain
git branch --show-current
base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git fetch origin "${base}"
git branch -vv
git merge-base --is-ancestor "origin/${base}" HEAD
git log --oneline "origin/${base}..HEAD"
git diff "origin/${base}...HEAD" --stat
existing_url=$(gh pr view --json url --jq '.url' 2>/dev/null); [ -n "$existing_url" ] && echo "PR exists: $existing_url"

# Push
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"

# Open draft PR against the repo default base
GIT_TERMINAL_PROMPT=0 gh pr create \
  --draft \
  --title "feat(scope): summary under 70 chars" \
  --body-file - \
  --head "$(git branch --show-current)" <<'EOF'
## Summary
...
EOF

# Open draft PR against a non-default base (e.g., a release branch)
GIT_TERMINAL_PROMPT=0 gh pr create \
  --draft \
  --base release/v2 \
  --title "fix(scope): backport summary under 70 chars" \
  --body-file - \
  --head "$(git branch --show-current)" <<'EOF'
## Summary
...
EOF

# View / promote / inspect
gh pr view --web
gh pr ready <pr-number>          # draft → ready (fires expensive CI; see <draft_lifecycle>)
gh pr ready --undo <pr-number>   # ready → draft (use before pushing more commits to a ready PR)
gh pr checks <pr-number>
```

</commands_reference>
