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
- Title under 70 chars in Conventional Commits format (matches `/committing-changes`)
- Body delivered to `gh` on stdin via `--body-file -` (real newlines, no `\n` escapes, no temp file)
- Draft by default; ready-for-review only when explicitly requested
- No self-reference in title, body, or branch name
- PR URL printed for the user

</success_criteria>

<context>

This skill does NOT:

- Stage, commit, or amend (use `/committing-changes`)
- Force-push or rewrite history
- Merge, squash, or close the PR
- Modify CI/CD workflows
- Watch CI runs (polling is forbidden — see `<critical_rules>`)

</context>

<project_specialization>
After loading this skill, check whether `spx/local/opening-pr.md` exists (path is relative to the repository root). If it does, read it and apply its rules as product-specific additions to the PR workflow (e.g., extra pre-flight checks, marketplace-specific template sections, push-command overrides, draft-policy overrides).
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

# Commits ahead of base
git log --oneline "origin/${base}..HEAD"

# Diff stats against base
git diff "origin/${base}...HEAD" --stat

# Existing PR for current branch — extract .url directly via --jq
# (gh exits non-zero when no PR exists; redirect stderr to suppress its message)
existing_url=$(gh pr view --json url --jq '.url' 2>/dev/null)
[ -n "$existing_url" ] && echo "PR already exists: $existing_url"
```

</branch_hygiene>

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
git push -u origin "$(git branch --show-current)"

# Subsequent pushes
git push
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

- `--draft` — default for this skill; promote to ready-for-review only on explicit request.
- `--title` and `--body-file -` — explicit title plus body-from-stdin matches `/committing-changes` conventions without writing to disk.
- `--head` — the feature branch; prevents gh from prompting for fork/push targets.
- `--base` — omit to use the repo default; specify only when targeting a non-default base.
- `GIT_TERMINAL_PROMPT=0` — disables git credential prompts. (gh detects non-TTY stdin/stdout and skips its own prompts automatically; no `GH_*` env var is needed.)

**Do not use `--fill` with this skill.** `--fill` is gh's autofill from commit messages. If both `--fill` and `--body-file` are passed, the explicit body wins — but `--fill` is then dead weight. Use the curated body alone.

**Step 3: Surface the PR URL**

`gh pr create` prints the URL on the last line of stdout. Surface it to the user verbatim.

**Step 4: After follow-up pushes, check for re-reviews**

Automated reviewers (and humans) often re-fire on follow-up pushes. They may post as **formal reviews** OR as **PR-level issue comments** — checking only one surface misses half the feedback. Run this once after each follow-up push, then triage:

```bash
gh pr view <pr-number> --json reviews,comments \
  --jq '{
    reviews: [.reviews[] | {author: .author.login, state, submittedAt}],
    comments: [.comments[] | {author: .author.login, createdAt, excerpt: .body[0:160]}]
  }'
```

Compare timestamps against your last push. New entries after the push are re-reviews of the latest state — read them in full before declaring the PR done. Never assume "no new review" without checking both surfaces.

**Step 5 (optional, on user request): Mark ready for review**

```bash
gh pr ready <pr-number>
```

</workflow>

<critical_rules>

1. **NEVER push from `main` with bare `git push`** — use the product's push command (e.g., `just push-marketplace`) when one is defined.
2. **NEVER include self-reference** in title, body, or branch name — no "Claude", "AI", "agent", "Co-Authored-By: Claude".
3. **NEVER use `--body "..."` for multi-line content** — gh does not expand `\n`. Use `--body-file`.
4. **NEVER use `--fill`** with this skill — it adds nothing once `--body-file` is present.
5. **DRAFT BY DEFAULT** — `--draft` is mandatory unless the user explicitly says "ready for review".
6. **NEVER `gh run watch`** — for CI status, surface a single `gh pr checks` or `gh run view` and stop. Polling is forbidden.
7. **AFTER FOLLOW-UP PUSHES, check both `reviews` AND `comments`** — bots often post re-reviews as PR-level issue comments rather than formal reviews. Checking only `reviews` will silently miss re-feedback on the latest commit.

</critical_rules>

<commands_reference>

```bash
# Pre-flight (resolve base; never hardcode main)
gh auth status
git status --porcelain
git branch --show-current
base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git log --oneline "origin/${base}..HEAD"
git diff "origin/${base}...HEAD" --stat
existing_url=$(gh pr view --json url --jq '.url' 2>/dev/null); [ -n "$existing_url" ] && echo "PR exists: $existing_url"

# Push
git push -u origin "$(git branch --show-current)"

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
gh pr ready <pr-number>
gh pr checks <pr-number>
```

</commands_reference>
