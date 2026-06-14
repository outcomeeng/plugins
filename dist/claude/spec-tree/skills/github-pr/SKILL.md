---
name: github-pr
description: >-
  ALWAYS invoke this skill when the user asks to open or manage a GitHub pull request, or runs /github-pr.
  NEVER open or manage a GitHub pull request — whether invoked directly or delegated by /merge — without this skill.
argument-hint: "[instructions describing the change, or empty to use the current changeset]"
allowed-tools: Skill, AskUserQuestion, Bash, Read
---

<objective>
Orchestrate the GitHub-PR merge transport — the lifecycle that takes a changeset from shipping intent to a merged pull request. /github-pr is the GitHub-PR transport's lifecycle orchestration, invoked by `/merge` when it selects this transport, or directly when a pull request is the chosen way to ship. It detects what is being shipped and invokes the skills that own implementation, committing, PR opening, PR management, merge, and closure — autonomously by default, presenting a pre-mutation confirmation first only when the merge overlay opts into it. Transport selection belongs to `/merge`; /github-pr assumes the GitHub-PR transport and never reimplements the lifecycle skills' protocols, per /standardizing-merging.
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

- **Open PR** — `$ARGUMENTS` names a PR number or PR URL, or the injected state shows an existing PR for this branch. The PR already defines lifecycle state; manage it.
- **Instructed** — `$ARGUMENTS` is non-empty. Interpret it as instructions: what to ship, and any constraint on scope, branch, or framing. When the instruction names work that does not yet exist, implementation is part of the job.
- **Existing changeset** — `$ARGUMENTS` is empty and the working tree is dirty, or the branch is ahead of its base. The changeset already defines the work; derive intent from the diff and commits.
- **Empty** — `$ARGUMENTS` is empty, the working tree is clean, and the branch is the base with no commits ahead. Nothing is staged to ship; establish the change through `/interviewing` before any mutation.

</mode_detection>

<workflow>

**Step 1 — Establish intent and route.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke `/understanding` first so the foundation is loaded. Per the detected mode, gather what is being shipped. In Open PR mode, resolve the PR pointer and proceed directly to Step 6. In Empty mode, invoke `/interviewing` to elicit the change. In Instructed mode, resolve the instruction against the repository — when it touches the spec tree, load context through `/contextualizing` first per CLAUDE.md. `spx/local/merging.md` configures this transport (merge command, production-relevance recognition, pre-flight, post-merge) and is read by `/opening-pr`, `/managing-pr`, and `/standardizing-merging`; whether a PR is the transport at all is `/merge`'s selection, not this skill's.

**Step 2 — State the plan; confirm only if the overlay opts in.** Read `spx/local/merging.md` (via `/standardizing-merging` `<repo_local_overlay>`) for the pre-mutation-confirmation setting. By default — no setting declared — state the plan in prose (the change to make, the branch, the commit shape, and that the flow runs through PR open, merge, and closure unless the user instruction says otherwise) and proceed autonomously; there is no confirmation pause. Only when the overlay opts into a pre-mutation confirmation, present that same plan through the runtime's structured-question tool (`AskUserQuestion` on Claude Code, `request_user_input` on Codex) and obtain confirmation before the first mutating action — never branch, commit, push, open, or merge before that confirmation. Establishing *what* to ship in Empty mode (Step 1, `/interviewing`) is requirements work, not this confirmation, and always proceeds.

**Step 3 — Implement if needed.** When the agreed scope requires code that does not exist yet, drive it through the governing skills — `/applying` for a spec-tree node, or the language coding and testing skills — never writing implementation by hand outside them.

**Step 4 — Commit.** Invoke `/committing-changes`. Branch off the base first when the work sits on the base branch.

**Step 5 — Open.** Invoke `/opening-pr`. It evaluates `REVIEW_READINESS` and opens the PR ready. Skip this step in Open PR mode.

**Step 6 — Drive to merge.** Invoke `/managing-pr`. It evaluates `MERGE_READINESS` and `PRODUCTION_READINESS`, merges under the gates, and runs the post-merge steps.

**Step 7 — Close the session.** After merge and post-merge verification, invoke `/handoff` unless the user explicitly asked to stop earlier or the lifecycle overlay declares a different closure — the skill decides session-file creation per continuation state; never pass `--no-session` on the user's behalf.

</workflow>

<constraints>

- MUST drive the lifecycle from a determined changeset autonomously by default — state the plan in prose and proceed without a confirmation pause; present the plan through the runtime's structured-question tool and obtain confirmation before the first mutating action — branch creation, commit, push, PR open, or merge — only when the merge overlay opts into a pre-mutation confirmation.
- MUST drive every stage by invoking its governing skill — `/committing-changes`, `/opening-pr`, `/managing-pr`, and `/applying` or the coding skills — never reimplementing their protocols inline. Drift between a reimplementation and the source skill is the failure this skill exists to prevent.
- MUST read `spx/local/merging.md` for the GitHub-PR transport's configuration (merge command, production-relevance recognition, pre-flight, post-merge) through `/opening-pr`, `/managing-pr`, and `/standardizing-merging`. Transport selection — whether a PR is the transport at all — is `/merge`'s, never this skill's.
- NEVER merge directly — the merge executes only through `/managing-pr`'s `MERGE_READINESS` ∧ `PRODUCTION_READINESS` authority.
- MUST follow CLAUDE.md and the loaded skills exactly — /github-pr changes who invokes the lifecycle, not what the lifecycle does.

</constraints>

<success_criteria>

- The detected mode matches `$ARGUMENTS` and the injected repository state.
- By default the lifecycle ran autonomously from the determined changeset; where the merge overlay opted into a pre-mutation confirmation, the plan was presented through the runtime's structured-question tool and confirmed before the first mutation.
- The GitHub-PR transport was assumed (transport selection having been made by `/merge`), and `spx/local/merging.md` configured the transport through `/opening-pr`, `/managing-pr`, and `/standardizing-merging`.
- Each lifecycle stage ran through its governing skill, not an inline reimplementation.
- The PR reached merged state through `/managing-pr`'s gates and the session closed through `/handoff` (the skill deciding session-file creation per continuation state, never a hardcoded `--no-session`), or the flow stopped at an explicit gate — an unmet `REVIEW_READINESS` or `MERGE_READINESS` predicate, or a withheld `PRODUCTION_READINESS` — surfaced to the user.

</success_criteria>
