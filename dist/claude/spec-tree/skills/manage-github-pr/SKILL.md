---
name: manage-github-pr
description: >-
  ALWAYS invoke this skill when the user asks to open or manage a GitHub pull request, or runs /manage-github-pr.
  NEVER open or manage a GitHub pull request outside this skill.
argument-hint: "[instructions describing the change, or empty to use the current changeset]"
allowed-tools: Skill, AskUserQuestion, Bash(spx worktree status:*), Bash(spx diagnose:*), Bash(git branch:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git rev-parse:*), Bash(gh repo view:*), Bash(gh pr view:*), Bash(head:*), Bash(echo:*), Read
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
!`git status --porcelain 2>/dev/null | head -100`

**Unstaged diff (name/status):**
!`git diff --name-status 2>/dev/null | head -100`

**Staged diff (name/status):**
!`git diff --cached --name-status 2>/dev/null | head -100`

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

**Step 1 — Establish intent and route.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke `/understand` first so the foundation is loaded. Invoke `/merging-standards`, follow its `<reference_index>`, and directly read `merge-policy.md` before consuming `<repo_local_overlay>` or any other tagged merge-policy section. Per the detected mode, gather what is being shipped. In Open PR mode, resolve the PR pointer and proceed directly to Step 6. In Empty mode, invoke `/interview` to elicit the change. In Instructed mode, resolve the instruction against the repository — when it touches the spec tree, load context through `/contextualize` first per CLAUDE.md. `spx/local/merging.md` configures the GitHub-PR transport (merge command, deployment and release declarations, pre-flight) and is read by `/open-pr`, `/manage-pr`, and `/merging-standards`.

**Step 2 — State the plan; confirm only if the overlay opts in.** Read `spx/local/merging.md` (via `/merging-standards` `<repo_local_overlay>`) for the pre-mutation-confirmation setting. By default — no setting declared — state the plan in prose (the change to make, the branch, the commit shape, and that the flow runs through PR open, merge, and closure unless the user instruction says otherwise) and proceed autonomously; there is no confirmation pause. Only when the overlay opts into a pre-mutation confirmation, present that same plan through the runtime's structured-question tool (`AskUserQuestion` on Claude Code, `request_user_input` on Codex) and obtain confirmation before the first mutating action — never branch, commit, push, open, or merge before that confirmation. Establishing *what* to ship in Empty mode (Step 1, `/interview`) is requirements work, not this confirmation, and always proceeds.

After the plan or required confirmation, run `spx worktree status` from the assigned root and require a fresh passing `/merging-standards` `<occupancy_preflight>` before the first branch, commit, or other checkout-sensitive mutation. Then run every overlay-declared preflight check per `<overlay_safety_checks>`. In Open PR mode, Step 6 delegates these boundaries to `/manage-pr`, whose occupancy preflight precedes checkout-sensitive mutation and whose merge cleanup repeats the overlay preflight immediately before merge.

**Step 3 — Implement if needed.** When the agreed scope requires code that does not exist yet, drive it through the governing skills — `/apply` for a spec-tree node, or the language coding and testing skills — never writing implementation by hand outside them.

**Step 4 — Commit.** Invoke `/commit-changes`. Branch off the base first when the work sits on the base branch.

**Step 5 — Open.** Invoke `/open-pr`. It evaluates `VERIFICATION_READINESS` and opens the PR ready. Skip this step in Open PR mode.

**Step 6 — Drive to merge.** Invoke `/manage-pr <pr-pointer> --return-closeout` when the pointer is known, or `/manage-pr --return-closeout` when it resolves from the current branch. The explicit marker keeps broader-goal continuation and session closure in this outer lifecycle. `/manage-pr` evaluates `MERGE_READINESS`, merges under the gate, and runs any declared deploy and release phases.

**Step 7 — Continue or close.** Consume `/manage-pr`'s closeout-ready result. When it carries remaining in-scope work — a further PR, a pending `PLAN.md` item, a `spx/EXCLUDE` entry, a declared-but-unimplemented assertion — continue with it directly. When no in-scope work remains, invoke `/handoff` plain with the carried branch-state record and return its closeout. Do not append a separate merge receipt, and do not hand-author the closeout in place of the `/handoff` invocation — a `/handoff` completed earlier in the same conversation never satisfies this step for work merged after it, because new merged work reopens the session and the handoff workflow's existing-session search makes the repeat invocation cheap, reconciling the earlier handoff's artifact as a same-owner continuation. The `--return-closeout` marker makes this outer lifecycle's ownership explicit.

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

**Failure 4: A prior handoff substituted for Step 7.** Claude merged new work after a `/handoff` had already closed the session in the same conversation, judged a second invocation redundant, and hand-authored the final closeout. Signal: a transport-authored closing summary with no `/handoff` invocation after the merge. Avoid: new merged work reopens the session; invoke `/handoff` plain and let its existing-session search reconcile the earlier handoff's artifact as a same-owner continuation — that reconciliation is what makes the repeat invocation cheap. That cheapness is the reason to invoke it, never the reason to skip it.

</failure_modes>

<success_criteria>

- The detected mode matches `$ARGUMENTS` and the injected repository state.
- By default the lifecycle ran autonomously from the determined changeset; where the merge overlay opted into a pre-mutation confirmation, the plan was presented through the runtime's structured-question tool and confirmed before the first mutation.
- The invocation resolved to the GitHub-PR transport from its arguments and live repository state, and `spx/local/merging.md` configured the transport through `/open-pr`, `/manage-pr`, and `/merging-standards`.
- Each lifecycle stage ran through its governing skill, not an inline reimplementation.
- The PR reached merged state through `/manage-pr`'s gates, `/manage-pr` built the branch-state closeout record and ran safe cleanup, and `--return-closeout` returned that evidence to this outer lifecycle. Remaining in-scope work continued; a complete disposition invoked `/handoff` plain here, after the merge (the skill deciding session-file creation per continuation state, never a hardcoded `--no-session`) — an earlier `/handoff` in the same conversation did not stand in for it, and no closeout was transport-authored. An explicit gate — an unmet `VERIFICATION_READINESS` or `MERGE_READINESS` predicate, or a withheld `DEPLOYMENT_READINESS` or `RELEASE_READINESS` — surfaced to the user.

</success_criteria>
