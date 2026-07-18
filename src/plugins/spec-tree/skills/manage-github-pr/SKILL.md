---
name: manage-github-pr
description: >-
  ALWAYS invoke this skill when the user asks to open or manage a GitHub pull request, or runs /manage-github-pr.
  NEVER open or manage a GitHub pull request outside this skill.
argument-hint: "[instructions describing the change, or empty to use the current changeset]"
allowed-tools: Skill, {{! tool('ask_user') !}}, Bash(git branch:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git rev-parse:*), Bash(gh repo view:*), Bash(gh pr view:*), Bash(head:*), Bash(echo:*), Read
---

<objective>
A changeset merged into the default branch on origin through the GitHub-PR transport.
</objective>

<context>
Live repository state for mode detection, read at invocation.

**Arguments:** `$ARGUMENTS`

**Current branch:**
!`git branch --show-current || echo '(not a git repo)'`

**Working tree indicator (empty = clean):**
!`git rev-parse --is-inside-work-tree >/dev/null 2>&1 && { git status --porcelain 2>/dev/null | head -1; } || echo '(not a git repo)'`

**Commits ahead of base (default branch):**
!`base=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo main); echo "base: ${base}"; git log --format='%H %s' "origin/${base}..HEAD" 2>/dev/null | head -10 || echo '(none)'`

**Existing PR for this branch:**
!`gh pr view --json url --jq '.url' 2>/dev/null || echo '(none)'`

</context>

<mode_detection>
Read `$ARGUMENTS` and the injected state, then evaluate these mutually exclusive modes in order; the first matching predicate wins:

- **Open PR** — First resolve any one-token PR number, PR URL, or branch candidate with `gh pr view "$ARGUMENTS" --json number,url,state,headRefName,headRefOid,baseRefName`. Select this mode only when the returned `state == OPEN`; a syntactic PR number or URL that fails resolution or returns another state stops mode detection with that host-observed result and is never reinterpreted as an instruction. This mode also applies when `$ARGUMENTS` is empty and the injected state shows an existing PR for this branch. The PR already defines lifecycle state; manage it.
- **Instructed** — `$ARGUMENTS` is non-empty and did not resolve as an Open PR pointer. Interpret it as instructions: what to ship, and any constraint on scope, branch, or framing. When the instruction names work that does not yet exist, implementation is part of the job. If the injected state also shows an existing PR for this branch, retain that PR pointer for management after implementing and committing the instruction.
- **Existing changeset** — `$ARGUMENTS` is empty, no existing PR was detected for this branch, and either the working tree is dirty or the branch is ahead of its base. The changeset already defines the work; derive intent from the diff and commits.
- **Empty** — `$ARGUMENTS` is empty, no existing PR was detected for this branch, the working tree is clean, and the branch has no commits ahead of its base. Nothing is staged to ship; establish the change through `/interview` before any mutation.

</mode_detection>

<workflow>

**Step 1 — Establish intent and route.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke `/understand` first so the foundation is loaded. Then invoke `/merging-standards` before reading or applying any merge-overlay confirmation, preflight, gate, deployment, or release policy. Per the detected mode, gather what is being shipped. In Open PR mode with an explicit PR number, URL, or branch pointer, run `gh pr view "<explicit-pr-pointer>" --json number,url,state,headRefName,headRefOid,baseRefName`, require `state == OPEN`, and record the returned full URL as `pr_pointer`; when the injected current-branch state selected the mode without an explicit pointer, run `gh pr view --json number,url,state,headRefName,headRefOid,baseRefName`, require `state == OPEN`, and record the returned full URL as `pr_pointer`. Then proceed directly to Step 6. In Empty mode, invoke `/interview` to elicit the change. In Instructed mode, resolve the instruction against the repository — when it touches the spec tree, load context through `/contextualize` first per {{! file('root_guide') !}}. When Instructed mode also carries an injected current-branch PR, run `gh pr view --json number,url,state,headRefName,headRefOid,baseRefName`, require `state == OPEN`, and record the returned full URL as `pr_pointer` while continuing the instructed implementation path. `spx/local/merging.md` configures the GitHub-PR transport (merge command, deployment and release declarations, pre-flight) and is read by `/open-pr`, `/manage-pr`, and `/merging-standards`.

**Step 2 — State the plan; confirm only if the overlay opts in.** Read `spx/local/merging.md` (via `/merging-standards` `<repo_local_overlay>`) for the pre-mutation-confirmation setting. By default — no setting declared — state the plan in prose (the change to make, the branch, the commit shape, and that the flow runs through PR open, merge, and closure unless the user instruction says otherwise) and proceed autonomously. Normal harness approval for a consumer-defined command remains a tool-security boundary and resumes the same governed step after approval. Only when the overlay opts into a pre-mutation confirmation, present that same plan through the runtime's structured-question tool (`{{! tool('ask_user', 'claude') !}}` on Claude Code, `{{! tool('ask_user', 'codex') !}}` on Codex) and obtain confirmation before the first mutating action — never branch, commit, push, open, or merge before that confirmation. Establishing *what* to ship in Empty mode (Step 1, `/interview`) is requirements work, not this confirmation, and always proceeds.

After the plan or required confirmation, run every overlay-declared preflight check per `/merging-standards` `<overlay_safety_checks>` immediately before the first branch, commit, or other checkout-sensitive mutation. In Open PR mode, Step 6 delegates this boundary to `/manage-pr`, whose merge cleanup runs the preflight immediately before merge.

**Step 3 — Implement if needed.** When the agreed scope requires code that does not exist yet, drive it through the governing skills — `/apply` for a spec-tree node, or the language coding and testing skills — never writing implementation by hand outside them.

**Step 4 — Commit.** Invoke `/commit-changes`. Branch off the base first when the work sits on the base branch.

**Step 5 — Open.** When `pr_pointer` is absent, invoke `/open-pr`. It evaluates `VERIFICATION_READINESS` and opens the PR in the review state its topology permits — ready for a peer branch, or draft for a stacked branch awaiting its base. Record the returned full PR number as `pr_pointer`. When Open PR mode or an Instructed mode on a branch with an existing PR already recorded `pr_pointer`, skip this step.

**Step 6 — Tail-delegate management and closeout.** Invoke `/manage-pr <pr_pointer>` with the exact pointer recorded by Step 1 or Step 5. It evaluates `MERGE_READINESS`, merges under the gate, runs any declared deploy and release phases, continues remaining in-scope work, and invokes `/handoff` plain when the session is complete. Treat `/manage-pr` as the terminal lifecycle protocol once invoked: do not run a second continuation or closeout path after it returns.

</workflow>

<constraints>

- MUST drive the lifecycle from a determined changeset autonomously by default — state the plan in prose, handle any required harness tool approval as a security boundary that resumes the governed step, and proceed without a separate lifecycle-confirmation pause; present the plan through the runtime's structured-question tool and obtain confirmation before the first mutating action — branch creation, commit, push, PR open, or merge — only when the merge overlay opts into a pre-mutation confirmation.
- MUST drive every stage by invoking its governing skill — `/commit-changes`, `/open-pr`, `/manage-pr`, and `/apply` or the coding skills — never reimplementing their protocols inline. Drift between a reimplementation and the source skill is the failure this skill exists to prevent.
- MUST read `spx/local/merging.md` for the GitHub-PR transport's configuration (merge command, deployment and release declarations, pre-flight) through `/open-pr`, `/manage-pr`, and `/merging-standards`.
- NEVER merge directly — the merge executes only through `/manage-pr`'s `MERGE_READINESS` authority, with any declared deploy or release action handled after merge through `DEPLOYMENT_READINESS` or `RELEASE_READINESS`.
- MUST follow {{! file('root_guide') !}} and the loaded skills exactly.

</constraints>

<failure_modes>

**Failure 1: Mode detection waited for another transport decision.** Claude stalled even though the injected state already identified an existing PR, dirty changeset, branch-ahead changeset, or empty workspace. Avoid: once mode detection selects Open PR, Instructed, Existing changeset, or Empty, continue through the GitHub-PR workflow.

**Failure 2: Default autonomy became a confirmation prompt.** Claude stated a plan and then asked whether to push, open, or continue even though `spx/local/merging.md` did not opt into pre-mutation confirmation. Signal: an operator question before branch creation, commit, push, PR open, or merge with no overlay opt-in. Avoid: by default, state the plan and proceed; use the structured-question tool only when the overlay explicitly opts into pre-mutation confirmation.

**Failure 3: The lifecycle was reimplemented inline.** Claude opened, managed, merged, or cleaned up the PR by running ad hoc `git` or `gh` commands from this skill instead of invoking the governing lifecycle skills. Signal: inline commit, open, manage, merge, branch cleanup, or closeout logic appears in the main flow after mode detection. Avoid: after intent is established, delegate commit to `/commit-changes`, opening to `/open-pr`, and the remaining management-through-handoff lifecycle to `/manage-pr`; this skill owns routing, not the stage protocols.

</failure_modes>

<success_criteria>

- The detected mode matches `$ARGUMENTS` and the injected repository state.
- By default the lifecycle ran autonomously from the determined changeset; where the merge overlay opted into a pre-mutation confirmation, the plan was presented through the runtime's structured-question tool and confirmed before the first mutation.
- The invocation resolved to the GitHub-PR transport from its arguments and live repository state, and `spx/local/merging.md` configured the transport through `/open-pr`, `/manage-pr`, and `/merging-standards`.
- Each lifecycle stage ran through its governing skill, not an inline reimplementation.
- `/manage-pr` received the exact `pr_pointer` resolved or returned earlier and owned the terminal management lifecycle after delegation: merge, safe cleanup, declared deploy and release phases, continuation of in-scope work, and `/handoff` plain only when the session was complete; or it stopped at an explicit gate — an unmet `VERIFICATION_READINESS` or `MERGE_READINESS` predicate, or a withheld `DEPLOYMENT_READINESS` or `RELEASE_READINESS` — surfaced to the user.

</success_criteria>
