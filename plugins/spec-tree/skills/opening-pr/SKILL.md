---
name: opening-pr
description: >-
  ALWAYS invoke this skill when opening a pull request, creating a PR, or pushing a branch for review.
  NEVER run gh pr create without this skill.
allowed-tools: Read, Glob, Grep, Bash, Skill
---

<objective>
Open a pull request for the current branch with a curated title and body, after the merge-flow pre-flight gates defined in `/standardizing-merging` pass. Title and body classification follow `/committing-changes`; branch hygiene, branch topology, push semantics, draft lifecycle, and heartbeat protocol are inherited from `/standardizing-merging`. Post-creation review iteration is governed by `/managing-pr`.
</objective>

<success_criteria>

A successful PR open has:

- `/standardizing-merging` loaded; its branch hygiene, branch topology, push semantics, draft lifecycle, and heartbeat rules followed
- `/committing-changes` loaded for commit type and scope classification used in the PR title
- Title under 70 chars in the commit type/scope/description format defined by `/committing-changes`
- Body delivered to `gh` on stdin via `--body-file -` (real newlines, no `\n` escapes, no temp file)
- PR opened as draft (`gh pr create --draft`); promotion to ready-for-review is a separate `gh pr ready` step that runs only when the prerequisites in `/standardizing-merging` `<draft_lifecycle>` are met
- Heartbeat created or refreshed per `/standardizing-merging` `<heartbeat>` immediately after PR creation, verified by the URL or thread ID returned by the runtime tool, or by user confirmation when the runtime cannot create one directly
- No self-reference in title, body, or branch name
- PR URL printed for the user

</success_criteria>

<anti_patterns>

Patterns that break this skill's flow. Never:

- Stage, commit, or amend here — use `/committing-changes`.
- Force-push or rewrite history.
- Merge, squash, or close the PR — those belong to `/managing-pr` after creation.
- Modify global git configuration or CI/CD workflows.
- Watch CI runs in-shell, poll for status, or use `gh pr checks --watch` — forbidden by `/standardizing-merging` `<cross_cutting_nevers>` item 5.
- Track review feedback or drive the iteration loop after creation — use `/managing-pr`.

</anti_patterns>

<project_specialization>
After loading this skill, check whether `spx/local/opening-pr.md` exists (path is relative to the repository root). If it does, read it and apply its rules as product-specific additions to the PR creation workflow (e.g., extra pre-flight checks, marketplace-specific template sections, push-command overrides, project-specific closure-gate commands).

The project-level file MAY refine: extra pre-flight checks specific to the project, additional required body sections, project-specific push commands.

The project-level file MUST NOT: fold the promotion into `gh pr create` itself, skip the closure gate before promotion, override the always-draft mandate, or weaken the upstream-safety check.

Project-specific draft-lifecycle refinements (recognizing project-specific forms of the explicit human instruction; defining how the closure gate is run; defining when post-ready follow-up pushes may keep the PR ready) belong in `spx/local/merging.md` instead of the per-skill overlay, so `/managing-pr` and `/opening-pr` see the same rules.
</project_specialization>

<context>

**Before opening a PR, gather context:**

| Source                        | Gather                                                          |
| ----------------------------- | --------------------------------------------------------------- |
| **git status**                | Working tree state — clean? uncommitted changes?                |
| **git branch --show-current** | Current branch name (refuse if main/master/HEAD)                |
| **git log <base>..HEAD**      | Commits to be included (drives title and body content)          |
| **gh repo view**              | Default base branch (usually `main`)                            |
| **CLAUDE.md / AGENTS.md**     | Product-specific PR conventions, custom template, push commands |
| **Conversation**              | Issue or spec node references for the Refs footer               |

</context>

<title_format>

**The PR title is one commit-classification subject line under 70 characters, formatted exactly as `/committing-changes` defines for commit subjects.** Type and scope classification is inherited from `/committing-changes` — no separate taxonomy is maintained here.

**Source rules:**

- Single commit on the branch → use that commit's subject as-is (already conforms to `/committing-changes`).
- Multiple commits → synthesize a title that captures the dominant type and scope using the same classification.

**Synthesis procedure for multi-commit branches:**

1. Read all commit subjects: `git log --format=%s <base>..HEAD`.
2. Pick the dominant type from `/committing-changes` `<commit_types>` (the type that describes the umbrella change).
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

**Rules** — defined in `/committing-changes` (subject-line constraints: length, mood, type vocabulary, banned words, self-reference). Do not maintain a copy here; load `/committing-changes` and follow what it states.

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

**Step 0: Load references.** Invoke `/standardizing-merging` (cross-cutting merge-flow standards) and `/committing-changes` (commit type/scope classification used in the title) via the Skill tool.

**Step 1: Pre-flight.** Run `/standardizing-merging` `<branch_hygiene>` checks. Every condition must hold or the gate STOPs the flow.

**Step 2: Classify branch topology.** Run `/standardizing-merging` `<branch_topology>` peer or stacked gate. Repair or reclassify before pushing if the gate fails.

**Step 3: Push the branch.** Use the explicit-destination-ref form from `/standardizing-merging` `<push_semantics>`:

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"
```

If the product defines a custom branch-push command, follow CLAUDE.md / AGENTS.md instead.

**Step 4: Open the PR with body piped via stdin.**

Pass the curated body to `gh pr create` on stdin via `--body-file -`. A Bash heredoc preserves real newlines, avoids any temp file, and removes the cleanup step (and its permission prompt for users with strict `Bash(rm:*)` rules):

```bash
GIT_TERMINAL_PROMPT=0 gh pr create \
  --draft \
  --title "<commit-subject under 70 chars per /committing-changes>" \
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

- `--draft` — mandatory on every `gh pr create`. See `/standardizing-merging` `<draft_lifecycle>` rule 1.
- `--title` and `--body-file -` — explicit title plus body-from-stdin matches `/committing-changes` conventions without writing to disk.
- `--head` — the feature branch; prevents gh from prompting for fork/push targets.
- `--base` — omit only for peer branches targeting the repo default; specify the previous stack branch for stacked PRs.
- `GIT_TERMINAL_PROMPT=0` — disables git credential prompts. (gh detects non-TTY stdin/stdout and skips its own prompts automatically; no `GH_*` env var is needed.)

**Do not use `--fill` with this skill.** `--fill` is gh's autofill from commit messages. If both `--fill` and `--body-file` are passed, the explicit body wins — but `--fill` is then dead weight.

**Step 5: Surface the PR URL.** `gh pr create` prints the URL on the last line of stdout. Surface it to the user verbatim.

**Step 6: Create or refresh the heartbeat.** Per `/standardizing-merging` `<heartbeat>`, create the runtime heartbeat for the first review/check re-inspection. If a heartbeat for this PR already exists, refresh it instead of creating a second one. Verify creation by capturing the URL or thread ID returned by the runtime tool, or by explicit user confirmation when the runtime cannot create one directly.

**Step 7: Hand off to `/managing-pr`.** Once the PR is open and the heartbeat is in place, post-creation review iteration (classifying review feedback, addressing BLOCKING items, follow-up pushes, promotion to ready) is governed by `/managing-pr`. This skill's responsibility ends here.

**Promotion to ready** runs as a separate `gh pr ready <pr-number>` invocation, only when the four prerequisites in `/standardizing-merging` `<draft_lifecycle>` rule 3 hold. When the user-approved plan calls for a ready PR after the closure gate passes, the `gh pr ready` step may run immediately after `gh pr create` in the same flow — the two commands remain distinct.

</workflow>

<commands_reference>

For pre-flight (`gh auth status`, working-tree state, ahead-of-base, upstream safety) and the push command, see `/standardizing-merging` `<branch_hygiene>` and `<push_semantics>`. The recipes below are the opening-pr-specific commands not covered there.

```bash
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

# View / promote — see /standardizing-merging <draft_lifecycle>
gh pr view --web
gh pr ready <pr-number>          # draft → ready (fires expensive CI)
gh pr ready --undo <pr-number>   # ready → draft (use before pushing more commits)
```

For everything else — branch topology repair, the full draft lifecycle table, the heartbeat protocol, the three-surface review inspection — see `/standardizing-merging`.

</commands_reference>
