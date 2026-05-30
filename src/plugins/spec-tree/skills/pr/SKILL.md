---
name: pr
description: >-
  ALWAYS invoke this skill when the user asks to open a PR, ship a change, or take work from changes to merged, or runs /pr. It proposes a plan through the runtime's structured-question tool, then drives committing, opening, and merging through the governed lifecycle skills. NEVER chain the commit-to-merge flow by hand when /pr applies.
argument-hint: "[instructions describing the change, or empty to use the current changeset]"
allowed-tools: Skill, AskUserQuestion, Bash, Read
---

<objective>
Drive a changeset from intent to merged through one entry point. /pr detects what the user is shipping, proposes a plan, and on confirmation chains the governed lifecycle skills — implementation, committing, opening, and merging — without the user invoking each by hand. The lifecycle skills own their protocols; /pr orchestrates them and never reimplements them.
</objective>

<context>
Live repository state for mode detection, read at invocation.

**Arguments:** `$ARGUMENTS`

**Current branch:**
!`git branch --show-current || echo '(not a git repo)'`

**Working tree (empty = clean):**
!`git status --porcelain || echo '(not a git repo)'`

**Commits ahead of base (default branch):**
!`base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo main); echo "base: ${base}"; git log --oneline "origin/${base}..HEAD" 2>/dev/null | head -10 || echo '(none)'`

**Existing PR for this branch:**
!`gh pr view --json url --jq '.url' 2>/dev/null || echo '(none)'`

</context>

<mode_detection>
Read `$ARGUMENTS` and the injected state, then pick exactly one mode:

- **Instructed** — `$ARGUMENTS` is non-empty. Interpret it as instructions: what to ship, and any constraint on scope, branch, or framing. When the instruction names work that does not yet exist, implementation is part of the job.
- **Existing changeset** — `$ARGUMENTS` is empty and the working tree is dirty, or the branch is ahead of its base. The changeset already defines the work; derive intent from the diff and commits.
- **Empty** — `$ARGUMENTS` is empty, the working tree is clean, and the branch is the base with no commits ahead. Nothing is staged to ship; establish the change through `/interviewing` before any mutation.

</mode_detection>

<workflow>

**Step 1 — Establish intent.** Per the detected mode, gather what is being shipped. In Empty mode, invoke `/interviewing` to elicit the change. In Instructed mode, resolve the instruction against the repository — when it touches the spec tree, load context through `/contextualizing` first per CLAUDE.md.

**Step 2 — Propose and confirm.** Present the plan through the runtime's structured-question tool (`AskUserQuestion` on Claude Code, `request_user_input` on Codex): the change to make, the branch, the commit shape, and that the flow runs through merge. Obtain confirmation before any mutating action. This pause is mandatory — Claude never branches, commits, pushes, opens, or merges before the user confirms the proposal.

**Step 3 — Implement if needed.** When the agreed scope requires code that does not exist yet, drive it through the governing skills — `/applying` for a spec-tree node, or the language coding and testing skills — never writing implementation by hand outside them.

**Step 4 — Commit.** Invoke `/committing-changes`. Branch off the base first when the work sits on the base branch.

**Step 5 — Open.** Invoke `/opening-pr`. It evaluates `REVIEW_READINESS` and opens the PR ready.

**Step 6 — Drive to merge.** Invoke `/managing-pr`. It evaluates `MERGE_READINESS` and `PRODUCTION_READINESS`, merges under the gates, and runs the post-merge steps.

</workflow>

<constraints>

- MUST present the plan through the runtime's structured-question tool and obtain confirmation before any mutating action — branch creation, commit, push, PR open, or merge. The proposal is the contract the rest of the flow executes.
- MUST drive every stage by invoking its governing skill — `/committing-changes`, `/opening-pr`, `/managing-pr`, and `/applying` or the coding skills — never reimplementing their protocols inline. Drift between a reimplementation and the source skill is the failure this skill exists to prevent.
- NEVER merge directly — the merge executes only through `/managing-pr`'s `MERGE_READINESS` ∧ `PRODUCTION_READINESS` authority.
- MUST follow CLAUDE.md and the loaded skills exactly — /pr changes who invokes the lifecycle, not what the lifecycle does.

</constraints>

<success_criteria>

- The detected mode matches `$ARGUMENTS` and the injected repository state.
- A proposal was presented through the runtime's structured-question tool and confirmed before the first mutation.
- Each lifecycle stage ran through its governing skill, not an inline reimplementation.
- The PR reached merged state through `/managing-pr`'s gates, or the flow stopped at an explicit gate — an unmet `REVIEW_READINESS` or `MERGE_READINESS` predicate, or a withheld `PRODUCTION_READINESS` — surfaced to the user.

</success_criteria>
