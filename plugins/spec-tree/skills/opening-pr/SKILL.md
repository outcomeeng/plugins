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
- Body delivered via `--body-file` (real newlines, no `\n` escapes) using the project PR template
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
After loading this skill, check for `spx/local/opening-pr.md` at the repository root. If it exists, read it and apply its rules as project-specific additions to the PR workflow (e.g., extra pre-flight checks, marketplace-specific template sections, push-command overrides, draft-policy overrides).
</project_specialization>

<context_gathering>

**Before opening a PR, gather context:**

| Source                        | Gather                                                          |
| ----------------------------- | --------------------------------------------------------------- |
| **git status**                | Working tree state — clean? uncommitted changes?                |
| **git branch --show-current** | Current branch name (refuse if main/master/HEAD)                |
| **git log <base>..HEAD**      | Commits to be included (drives title and body content)          |
| **gh repo view**              | Default base branch (usually `main`)                            |
| **CLAUDE.md / AGENTS.md**     | Project-specific PR conventions, custom template, push commands |
| **Conversation**              | Issue or spec node references for the Refs footer               |

</context_gathering>

<branch_hygiene>

**Pre-flight checks — MUST pass before pushing or opening the PR.**

| Check                                                    | Failure response                                               |
| -------------------------------------------------------- | -------------------------------------------------------------- |
| Current branch is not `main`, `master`, or detached HEAD | STOP. PRs are opened from feature branches.                    |
| Working tree is clean (no uncommitted changes)           | STOP. Direct the user to `/committing-changes` or to stash.    |
| Branch has commits ahead of base                         | STOP. Nothing to PR — verify the base branch.                  |
| Branch is current with the base                          | Warn. Offer to rebase; proceed only if the user confirms.      |
| No PR already exists for this branch                     | STOP. Surface the existing PR URL via `gh pr view --json url`. |

**Commands:**

```bash
# Branch identity
git branch --show-current

# Working tree state (empty output = clean)
git status --porcelain

# Default base branch
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'

# Commits ahead of base (substitute the resolved base)
git log --oneline origin/main..HEAD

# Diff stats against base
git diff origin/main...HEAD --stat

# Existing PR for current branch
gh pr view --json url,state 2>/dev/null
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

**The PR body is markdown prose written to a temp file and passed via `--body-file`.**

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

<creating_pr>

**Step 1: Push the branch**

```bash
# First push (sets upstream)
git push -u origin "$(git branch --show-current)"

# Subsequent pushes
git push
```

If the project defines a custom push command (e.g., `just push-marketplace` for the outcomeeng marketplace repo), follow the project convention from CLAUDE.md / AGENTS.md instead of bare `git push`.

**Step 2: Write the body to a temp file**

Write the curated body to `/tmp/pr-body-<branch>.md` via a Bash heredoc so newlines land as real `\n` bytes. The file lives outside the working tree so it is never staged. Do not pass multi-line content via `--body "..."` — gh does not expand `\n` escapes.

```bash
cat > "/tmp/pr-body-$(git branch --show-current).md" <<'EOF'
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

Use the unquoted heredoc form (`<<EOF`) instead of `<<'EOF'` only when the body must expand shell variables — and prefer composing the body in the agent's context first.

**Step 3: Open the PR**

```bash
GH_PROMPT_DISABLED=1 GIT_TERMINAL_PROMPT=0 gh pr create \
  --draft \
  --title "<conventional-commits subject under 70 chars>" \
  --body-file /tmp/pr-body-<branch>.md \
  --head "$(git branch --show-current)"
```

**Flag rationale:**

- `--draft` — default for this skill; promote to ready-for-review only on explicit request.
- `--title` and `--body-file` — explicit content matching `/committing-changes` conventions.
- `--head` — the feature branch; prevents gh from prompting for fork/push targets.
- `--base` — omit to use the repo default; specify only when targeting a non-default base.
- `GH_PROMPT_DISABLED=1` — disables interactive gh prompts.
- `GIT_TERMINAL_PROMPT=0` — disables git credential prompts.

**Do not use `--fill` with this skill.** `--fill` is gh's autofill from commit messages. If both `--fill` and `--body-file` are passed, the explicit body wins — but `--fill` is then dead weight. Use the curated body alone.

**Step 4: Surface the PR URL**

`gh pr create` prints the URL on the last line of stdout. Surface it to the user verbatim.

**Step 5: Clean up the temp file**

```bash
rm /tmp/pr-body-<branch>.md
```

**Step 6 (optional, on user request): Mark ready for review**

```bash
gh pr ready <pr-number>
```

</creating_pr>

<critical_rules>

1. **NEVER push from `main` with bare `git push`** — use the project's push command (e.g., `just push-marketplace`) when one is defined.
2. **NEVER include self-reference** in title, body, or branch name — no "Claude", "AI", "agent", "Co-Authored-By: Claude".
3. **NEVER use `--body "..."` for multi-line content** — gh does not expand `\n`. Use `--body-file`.
4. **NEVER use `--fill`** with this skill — it adds nothing once `--body-file` is present.
5. **DRAFT BY DEFAULT** — `--draft` is mandatory unless the user explicitly says "ready for review".
6. **NEVER `gh run watch`** — for CI status, surface a single `gh pr checks` or `gh run view` and stop. Polling is forbidden.

</critical_rules>

<commands_reference>

```bash
# Pre-flight
git status --porcelain
git branch --show-current
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
git log --oneline origin/main..HEAD
git diff origin/main...HEAD --stat
gh pr view --json url,state 2>/dev/null

# Push
git push -u origin "$(git branch --show-current)"

# Open draft PR with curated title and body
GH_PROMPT_DISABLED=1 GIT_TERMINAL_PROMPT=0 gh pr create \
  --draft \
  --title "feat(scope): summary under 70 chars" \
  --body-file /tmp/pr-body-<branch>.md \
  --head "$(git branch --show-current)"

# View / promote / inspect
gh pr view --web
gh pr ready <pr-number>
gh pr checks <pr-number>
```

</commands_reference>
