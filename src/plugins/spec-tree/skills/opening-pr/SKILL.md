---
name: opening-pr
description: >-
  ALWAYS invoke this skill when opening a pull request, creating a PR, or pushing a branch for review.
  NEVER invoke this skill to manage an open pull request — use /managing-pr for the post-creation loop.
allowed-tools: Read, Glob, Grep, Bash, Skill
---

<objective>
The opening flow. One-shot, linear: pre-flight → topology → REVIEW_READINESS (deterministic verification + local review) → push → open ready → schedule first heartbeat → exit. Every step is a routine workflow operation that runs without operator confirmation. After exit, /managing-pr governs the post-creation loop.
</objective>

<project_specialization>
After loading this skill, check whether `spx/local/opening-pr.md` exists at the repository root. Read it if present and apply it as a product-specific addition to this flow (extra pre-flight checks, additional required body sections, project-specific push commands).

The overlay MUST NOT: skip or weaken the deterministic-verification or local-review predicates of `REVIEW_READINESS`, open the PR before `REVIEW_READINESS` holds, open the PR as a draft gating step, or weaken the upstream-safety check.

Production-relevance recognition and the merge command live in `spx/local/merging.md`, so /managing-pr and /opening-pr see the same rules. The deterministic-verification command is the project's own `CLAUDE.md` / `AGENTS.md` convention, which an overlay MAY centralize there too.
</project_specialization>

<the_opening_flow>

Walk these steps in order. Every step is a routine workflow operation — verify, review, push, open — and runs directly. The opening flow contains no operator-confirmation pauses.

**Step 0 — Load references.** Invoke /standardizing-merging (shared vocabulary), /committing-changes (commit type/scope classification for the title), and /tracking-tasks (runtime tracking rules) via the Skill tool.

**Step 1 — Pre-flight.** Run /standardizing-merging `<branch_hygiene>` checks. Every condition must hold or the flow stops at the first failed condition.

**Step 2 — Classify topology.** Run /standardizing-merging `<branch_topology>` peer or stacked gate. Repair or reclassify before pushing if the gate fails.

**Step 3 — Evaluate `REVIEW_READINESS`.** Per /standardizing-merging `<authority_gates>`, the PR opens ready only when `REVIEW_READINESS` holds — both predicates below.

*(a) Deterministic verification.* Run the project's full validation-and-testing command — the command the project documents in its `CLAUDE.md` / `AGENTS.md` (for example `just check` / `pnpm test`; an overlay MAY centralize it in `spx/local/merging.md`). It must report success; fix failures and re-run until green.

*(b) Local review to convergence.* Run the changes-reviewer agent (preferred) on the working diff — it runs in an isolated context, so the verdict is not biased by everything the operator's main agent has been doing. Fall back to the `/review-changes` slash command when the agent is not installed; both invoke the same `reviewing-changes` skill chain and produce the same `review-result.json` / `review.md` artifacts under thread-store. Invoke it per /standardizing-merging `<local_review_invocation>`: pass only the repository/worktree and the working diff range, with no interpretive scope, no severity pre-filter, and no instruction on what to emphasize — the reviewer reads the repository's own instructions and the shared taxonomy itself. The reviewer emits findings only (no decision/verdict); process them by **validity and phase** per /standardizing-merging `<review_classification>` — this is the before-open phase:

- **Validate each finding** against its cited rule, the product-local / language / spec-tree governance, and the PDR/ADR decisions. Drop any finding the citation does not support.
- **Apply every valid finding that belongs.** Fix it, commit via /committing-changes, re-invoke the reviewer, and repeat. When a valid finding's fix is too large to belong in this changeset, **split it out** — the work leaves the diff, recorded in the owning node's `ISSUES.md` or `PLAN.md` — instead of applying it here.
- **Converged** when the working diff carries no unapplied valid finding that belongs. Severity never decides; validity and the before-open phase do.

The iteration accumulates commits on the branch — the eventual push at Step 4 sends them all. After every iteration that commits, re-run /standardizing-merging `<branch_hygiene>`, re-run deterministic verification, and re-run the local review — both `REVIEW_READINESS` predicates must hold together on the exact tree the push publishes, so loop until a single tree passes both (the joint fixpoint of /managing-pr Step 6: a verification-driven fix is a diff the review has not seen, and a review-driven fix is a tree verification has not covered). `REVIEW_READINESS` holds only when (a) and (b) both hold; only then proceed. The before-open pass is the strictest point in the lifecycle: every valid finding that belongs is applied here and only split-out work survives to the CI review, which on the open PR must show no unresolved valid `BLOCKING` or `DEBT` finding.

**Step 4 — Push.** Use the explicit destination ref form from /standardizing-merging `<push_semantics>`:

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"
```

If the product defines a custom branch-push command, follow CLAUDE.md / AGENTS.md instead — the explicit destination ref must remain part of any custom command.

**Step 5 — Open the PR ready.** Pipe the curated body to gh on stdin via `--body-file -`. The PR opens `ready_for_review` because `REVIEW_READINESS` holds (Step 3); `gh pr create` defaults to ready, so no draft flag is passed:

```bash
GIT_TERMINAL_PROMPT=0 gh pr create \
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

Flag rationale:

- No `--draft` — the PR opens ready per /standardizing-merging `<authority_gates>`; `REVIEW_READINESS` (Step 3) is the gate that earns the open, and opening ready fires every CI review (Codex and the CI review) at once. A stacked PR is the one exception — pass `--draft` only when `<branch_topology>` holds it draft until its base merges.
- `--title` and `--body-file -` — explicit title plus body-from-stdin; matches /committing-changes conventions without writing to disk.
- `--head` — the feature branch; prevents gh from prompting for fork/push targets.
- `--base` — omit only for peer branches targeting the repo default; specify the previous stack branch for stacked PRs.
- `GIT_TERMINAL_PROMPT=0` — disables git credential prompts. (gh detects non-TTY stdin/stdout and skips its own prompts automatically; no `GH_*` env var is needed.)

The single-quoted heredoc terminator (`<<'EOF'`) disables shell expansion inside the body — backticks, `$variables`, and `!` pass through literally. Use the unquoted form (`<<EOF`) only when the body must interpolate shell variables. Never embed multi-line content in `--body "..."` — gh does not expand `\n` escapes.

Do not use `--fill`. If both `--fill` and `--body-file` are passed, the explicit body wins; `--fill` is then dead weight.

**Step 6 — Schedule the first heartbeat.** Per /standardizing-merging `<heartbeat>` and /tracking-tasks, schedule the first review/check re-inspection through the runtime timer. Verify by capturing the URL or thread ID returned by the runtime tool. Fall back to explicit user confirmation only when the runtime cannot create one directly.

**Exit.** Surface the PR URL. The managing flow takes over.

</the_opening_flow>

<title_format>

The PR title is one commit-subject line under 70 characters per /committing-changes:

- Single commit on the branch → use that commit's subject as-is.
- Multiple commits → synthesize one subject capturing the dominant type and scope. Read `git log --format=%s <base>..HEAD`, pick the dominant type from /committing-changes `<commit_types>`, write a description that summarizes the change across the commits (not a commit list).

Examples:

```text
feat(auth): add OAuth2 token refresh
feat(auth): add SMS and authenticator-app two-factor support
refactor: extract validation into dedicated module
fix(parser): handle nested expressions and empty operands
```

</title_format>

<body_template>

The PR body is markdown prose passed to gh on stdin. Default template:

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

Adapt by change type:

| Change type | Adaptation                                                                                |
| ----------- | ----------------------------------------------------------------------------------------- |
| Bug fix     | Add a **Root cause** subsection in Background. Test plan includes the failing repro.      |
| Feature     | Expand Summary into a short user-facing description. Test plan lists acceptance criteria. |
| Refactor    | State the no-behavior-change invariant. Test plan: "existing tests still pass".           |
| Spec        | Link the spec nodes affected; describe what is now declared.                              |
| Docs        | Drop Test plan; describe what readers gain.                                               |

Body explains WHY for the reviewer; the diff already shows WHAT. Reference spec nodes by full path from `spx/`. No `<self_reference>` violations per /standardizing-merging.

</body_template>

<failure_modes>

**Opened a PR gated on an earlier tree.** Claude established `REVIEW_READINESS`, then committed review-driven fixes during the convergence loop, and opened the PR without re-running deterministic verification and the local review on the final accumulated tree — so the opened diff was gated at an earlier state than the one CI receives. After every iteration that commits, re-run /standardizing-merging `<branch_hygiene>`, deterministic verification, AND the local review, treating `REVIEW_READINESS` as holding only when both predicates pass together on the exact tree the push publishes — never with the later-fixed predicate established before the last commit (Step 3b).

</failure_modes>

<success_criteria>

The opening flow has succeeded when:

- /standardizing-merging, /committing-changes, and /tracking-tasks are loaded before the flow begins.
- /standardizing-merging `<branch_hygiene>` and `<branch_topology>` gates pass before push.
- `REVIEW_READINESS` held before the PR opened: deterministic verification passed on the diff that will be pushed, and the local review converged — every valid finding that belongs was applied, any valid finding too large to belong was split out (recorded in the relevant node's `ISSUES.md` / `PLAN.md`), and unbacked findings were dropped. Severity did not gate; validity and the before-open phase did.
- Push uses the explicit destination ref form from /standardizing-merging `<push_semantics>`.
- Title is one commit-subject line under 70 chars per /committing-changes.
- Body is delivered to gh via `--body-file -` on stdin (real newlines).
- The PR is opened `ready_for_review` (`gh pr create` with no `--draft`) once `REVIEW_READINESS` holds — except a stacked PR held draft per `<branch_topology>`.
- First heartbeat is scheduled per /standardizing-merging `<heartbeat>` and /tracking-tasks.
- PR URL is surfaced to the user.
- No `<self_reference>` violation per /standardizing-merging.

</success_criteria>
