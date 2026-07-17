---
name: manage-github-pr
description: >-
  ALWAYS invoke this skill when the user asks to open or manage a GitHub pull request, or runs /manage-github-pr.
  NEVER open or manage a GitHub pull request outside this skill.
argument-hint: "[instructions describing the change, or empty to use the current changeset]"
allowed-tools: Skill, AskUserQuestion, Bash(git branch:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git rev-parse:*), Bash(gh repo view:*), Bash(gh pr view:*), Bash(head:*), Bash(echo:*), Bash(spx diagnose:*), Bash(just marketplace-source-root:*), Read
---

<objective>
A changeset merged into the default branch on origin through the GitHub-PR transport.
</objective>

<context>
Live repository state for mode detection, read at invocation.

**Arguments:** `$ARGUMENTS`

**Current branch:**
!`git branch --show-current || echo '(not a git repo)'`

**Working tree (empty = clean):**
!`git status --porcelain || echo '(not a git repo)'`

**Unstaged diff (name/status):**
!`git diff --name-status || echo '(none)'`

**Staged diff (name/status):**
!`git diff --cached --name-status || echo '(none)'`

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
- **Empty** — `$ARGUMENTS` is empty, the working tree is clean, and the branch is the base with no commits ahead. Nothing is staged to ship; establish the change through `/interview` before any mutation.

</mode_detection>

<workflow>

**Step 1 — Establish intent and route.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke `/understand` first so the foundation is loaded. Per the detected mode, gather what is being shipped. In Open PR mode, resolve the PR pointer and proceed directly to Step 6. In Empty mode, invoke `/interview` to elicit the change. In Instructed mode, resolve the instruction against the repository — when it touches the spec tree, load context through `/contextualize` first per CLAUDE.md. `spx/local/merging.md` configures the GitHub-PR transport (merge command, deployment and release declarations, pre-flight) and is read by `/open-pr`, `/manage-pr`, and `/merging-standards`.

**Step 2 — State the plan; confirm only if the overlay opts in.** Read `spx/local/merging.md` (via `/merging-standards` `<repo_local_overlay>`) for the pre-mutation-confirmation setting. By default — no setting declared — state the plan in prose (the change to make, the branch, the commit shape, and that the flow runs through PR open, merge, and closure unless the user instruction says otherwise) and proceed autonomously; there is no confirmation pause. Only when the overlay opts into a pre-mutation confirmation, present that same plan through the runtime's structured-question tool (`AskUserQuestion` on Claude Code, `request_user_input` on Codex) and obtain confirmation before the first mutating action — never branch, commit, push, open, or merge before that confirmation. Establishing *what* to ship in Empty mode (Step 1, `/interview`) is requirements work, not this confirmation, and always proceeds.

After the plan or required confirmation, run every overlay-declared preflight check per `/merging-standards` `<overlay_safety_checks>` immediately before the first branch, commit, or other checkout-sensitive mutation. In Open PR mode, Step 6 delegates this boundary to `/manage-pr`, whose merge cleanup runs the preflight immediately before merge.

**Step 3 — Implement if needed.** When the agreed scope requires code that does not exist yet, drive it through the governing skills — `/apply` for a spec-tree node, or the language coding and testing skills — never writing implementation by hand outside them.

**Step 4 — Commit.** Invoke `/commit-changes`. Branch off the base first when the work sits on the base branch.

**Step 5 — Open.** Invoke `/open-pr`. It evaluates `VERIFICATION_READINESS` and opens the PR ready. Skip this step in Open PR mode.

**Step 6 — Drive to merge.** Invoke `/manage-pr`. It evaluates `MERGE_READINESS`, merges under the gate, and runs any declared deploy and release phases.

**Step 7 — Continue or close.** A merged PR is one step, not necessarily the session's end. Carry forward `/manage-pr`'s branch-state closeout record, including the **Remaining Branches** groups and safe cleanup results. If any in-scope part of the user's stated goal remains — a further PR, a pending `PLAN.md` item, a `spx/EXCLUDE` entry, a declared-but-unimplemented assertion — continue with it directly; a merge is not a license to stop. Invoke `/handoff` plain only when the session is complete — the goal is met with no in-scope work remaining, or continuation by Claude is impossible (the user halted, context is exhausted, or an external blocker prevents the next action) — per live `/understand` `<closing_protocol>` and the `/handoff` precondition; the skill then decides session-file creation per continuation state and never receives `--no-session` on the user's behalf. The final operator-facing closeout comes from `/handoff` and includes the carried branch-state record. Do not append a separate merge receipt before or after it.

</workflow>

<constraints>

- MUST drive the lifecycle from a determined changeset autonomously by default — state the plan in prose and proceed without a confirmation pause; present the plan through the runtime's structured-question tool and obtain confirmation before the first mutating action — branch creation, commit, push, PR open, or merge — only when the merge overlay opts into a pre-mutation confirmation.
- MUST drive every stage by invoking its governing skill — `/commit-changes`, `/open-pr`, `/manage-pr`, and `/apply` or the coding skills — never reimplementing their protocols inline. Drift between a reimplementation and the source skill is the failure this skill exists to prevent.
- MUST read `spx/local/merging.md` for the GitHub-PR transport's configuration (merge command, deployment and release declarations, pre-flight) through `/open-pr`, `/manage-pr`, and `/merging-standards`.
- NEVER merge directly — the merge executes only through `/manage-pr`'s `MERGE_READINESS` authority, with any declared deploy or release action handled after merge through `DEPLOYMENT_READINESS` or `RELEASE_READINESS`.
- MUST follow CLAUDE.md and the loaded skills exactly.

</constraints>

<failure_modes>

**Failure 1: Mode detection waited for another transport decision.** Claude stalled even though the injected state already identified an existing PR, dirty changeset, branch-ahead changeset, or empty workspace. Avoid: once mode detection selects Open PR, Instructed, Existing changeset, or Empty, continue through the GitHub-PR workflow.

**Failure 2: Default autonomy became a confirmation prompt.** Claude stated a plan and then asked whether to push, open, or continue even though `spx/local/merging.md` did not opt into pre-mutation confirmation. Signal: an operator question before branch creation, commit, push, PR open, or merge with no overlay opt-in. Avoid: by default, state the plan and proceed; use the structured-question tool only when the overlay explicitly opts into pre-mutation confirmation.

**Failure 3: The lifecycle was reimplemented inline.** Claude opened, managed, merged, or cleaned up the PR by running ad hoc `git` or `gh` commands from this skill instead of invoking the governing lifecycle skills. Signal: inline commit, open, manage, merge, branch cleanup, or closeout logic appears in the main flow after mode detection. Avoid: after intent is established, delegate each lifecycle stage to `/commit-changes`, `/open-pr`, `/manage-pr`, and `/handoff` as specified; this skill owns orchestration, not the stage protocols.

</failure_modes>

<success_criteria>

- The detected mode matches `$ARGUMENTS` and the injected repository state.
- By default the lifecycle ran autonomously from the determined changeset; where the merge overlay opted into a pre-mutation confirmation, the plan was presented through the runtime's structured-question tool and confirmed before the first mutation.
- The invocation resolved to the GitHub-PR transport from its arguments and live repository state, and `spx/local/merging.md` configured the transport through `/open-pr`, `/manage-pr`, and `/merging-standards`.
- Each lifecycle stage ran through its governing skill, not an inline reimplementation.
- The PR reached merged state through `/manage-pr`'s gates, `/manage-pr` built the branch-state closeout record and ran safe cleanup, and then, with in-scope goal work remaining, the lifecycle continued to the next part rather than closing; the session closed through `/handoff` plain only when continuation by Claude was impossible (the skill deciding session-file creation per continuation state, never a hardcoded `--no-session`), or the flow stopped at an explicit gate — an unmet `VERIFICATION_READINESS` or `MERGE_READINESS` predicate, or a withheld `DEPLOYMENT_READINESS` or `RELEASE_READINESS` — surfaced to the user.

</success_criteria>
