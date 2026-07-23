---
name: open-pr
user-invocable: false
description: >-
  PR opening protocol for VERIFICATION_READINESS, branch push, ready PR creation, and first management pass. Loaded by /manage-github-pr.
allowed-tools: Read, Glob, Grep, Agent, Bash(spx worktree status:*), Bash(spx diagnose:*), Bash(just marketplace-source-root:*), Bash(gh auth status:*), Bash(git status:*), Bash(gh repo view:*), Bash(git fetch:*), Bash(git merge-base:*), Bash(git diff:*), Bash(git rev-parse:*), Bash(gh pr view:*), Bash(git branch:*), Bash(git push:*), Bash(git log:*), Bash(gh pr create:*), Bash(gh pr checks:*), Bash(printf:*), Skill
---

<objective>
A pull request opened ready for review.
</objective>

<project_specialization>
After loading this skill, check whether `spx/local/open-pr.md` exists at the repository root. Read it if present and apply it as a product-specific addition to this flow (extra pre-flight checks, additional required body sections, project-specific push commands).

The overlay MUST NOT: skip or weaken the local deterministic-verification, evidence-auditor, or local-review predicates of `VERIFICATION_READINESS`, open the PR before `VERIFICATION_READINESS` holds, open the PR as a draft gating step, or weaken the upstream-safety check.

Production-relevance recognition, merge command, and local deterministic verification scope live in `spx/local/merging.md`, so /manage-pr and /open-pr see the same rules. The local deterministic-verification commands come from the project's own `CLAUDE.md` convention, with the overlay allowed to centralize scope and escalation cases.
</project_specialization>

<the_opening_flow>

Walk these steps in order. Every step is a routine workflow operation — verify, review, push, open — and runs directly. The opening flow contains no operator-confirmation pauses.

**Step 0 — Load references.** Invoke /merging-standards (shared vocabulary) and /commit-changes (commit type/scope classification for the title) via the Skill tool. Follow /merging-standards `<reference_index>` and directly read its `merge-policy.md` reference before Step 1; invoking the compact loader alone does not load the tagged policy sections used below.

**Step 1 — GATE: Pre-flight.** Run `spx worktree status` from the assigned root and require a fresh passing /merging-standards `<occupancy_preflight>` before any checkout-sensitive mutation. Run every overlay-declared preflight check per `<overlay_safety_checks>`, then run `<branch_hygiene>` checks. Every condition must hold or the flow stops at the first failed condition. Run this step before the push even when `/manage-github-pr` already ran the lifecycle-entry preflight before branch or commit work; the later check guards the checkout state at publication time.

**Step 2 — GATE: Classify topology.** Run /merging-standards `<branch_topology>` peer or stacked gate. Repair or reclassify before pushing if the gate fails.

<step name="verification_readiness_decision">

**Step 3 — GATE: Evaluate `VERIFICATION_READINESS`.** Per /merging-standards `<authority_gates>`, the PR opens ready only when `VERIFICATION_READINESS` holds — all predicates below.

*(a) Deterministic verification.* Run the project's local deterministic verification per /merging-standards `<local_deterministic_scope>` — validation and testing for the touched scope, escalating only when the overlay or risk evidence requires a wider local run. Capture verbose stdout/stderr in a temporary log path and inspect only the exit status, summary, and failing sections. It must report success; fix failures and re-run until green.

*(b) Evidence-auditor predicates.* Dispatch every evidence auditor /merging-standards `<authority_gates>` requires for the diff: `test-evidence-auditor` for changed `[test]` assertions, linked tests, or imported test-infrastructure artifacts; `eval-evidence-auditor` for changed `[eval]` assertions, eval artifacts, or producer artifacts for eval-backed assertions. Handle rejected, failing, or unknown verdicts per /merging-standards `<auditor_verdicts>`, re-running deterministic verification and the relevant auditor until the evidence predicate is clean.

*(c) Local review to convergence.* Run the `changes-reviewer` agent on the working diff — it runs in an isolated context, so the verdict is not biased by everything the operator's main context has been doing. Invoke it per /merging-standards `<local_review_invocation>`: let it resolve its own scope — the worktree it runs in and the working diff — with no interpretive scope, no severity pre-filter, and no instruction on what to emphasize; the reviewer reads the repository's own instructions and the shared taxonomy itself. The reviewer emits findings only (no decision/verdict); process its findings by **validity and phase** per /merging-standards `<review_classification>` — this is the before-open phase:

- **Validate each finding** against its cited rule, the product-local / language / spec-tree governance, and the PDR/ADR decisions. Drop any finding the citation does not support.
- **Apply every valid finding that belongs.** Treat each valid finding as defect-class evidence: sweep the touched node(s) for parallel instances with the same rule, source contract, evidence pattern, lifecycle step, or generated-source relationship. Fix the cited site and every in-scope parallel instance, commit via /commit-changes, re-invoke the reviewer, and repeat. When a valid finding's fix is too large to belong in this changeset, **split it out** — the work leaves the diff, recorded in the owning node's `ISSUES.md` or `PLAN.md` — instead of applying it here.
- **Converged** when the working diff carries no unapplied valid finding that belongs. Severity never decides; validity and the before-open phase do.

The iteration accumulates commits on the branch — the eventual push at Step 4 sends them all. After every iteration that commits, re-run /merging-standards `<branch_hygiene>`, re-run local deterministic verification, re-run required evidence-auditor predicates for touched evidence surfaces, and re-run the local review — all `VERIFICATION_READINESS` predicates must hold together on the exact tree the push publishes, so loop until a single tree passes all predicates (the joint fixpoint of /manage-pr Step 6: a verification-driven fix is a diff the review has not seen, an evidence-audit fix changes the evidence surface, and a review-driven fix is a tree verification has not covered). `VERIFICATION_READINESS` holds only when (a), (b), and (c) hold; only then proceed. The before-open pass is the strictest point in the lifecycle: every valid finding that belongs is applied here and only split-out work survives to the CI review, which on the open PR must show no unresolved valid `BLOCKING` or `DEBT` finding.

</step>

**Step 4 — GATE: Push.** Use the explicit destination ref form from /merging-standards `<push_semantics>`:

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"
```

If the product defines a custom branch-push command, follow CLAUDE.md instead — the explicit destination ref must remain part of any custom command.

**Step 5 — GATE: Open the PR ready.** Pipe the curated body to gh on stdin via `--body-file -`. The PR opens `ready_for_review` because `VERIFICATION_READINESS` holds (Step 3); `gh pr create` defaults to ready, so no draft flag is passed. Choose the stdin form by harness.

Interactive Claude Code and Codex sessions use a quoted heredoc:

```bash
GIT_TERMINAL_PROMPT=0 gh pr create \
  --title "<commit-subject under 70 chars per /commit-changes>" \
  --body-file - \
  --head "$(git branch --show-current)" <<'EOF'
## Summary

- <bullet>

## Background

<prose>

## Test plan

- [ ] <verification step>

## Refs

- <ref>
EOF
```

Programmatic runners that require one physical command line use `printf` with one argument per output line. The command below may wrap visually in a rendered view; keep it as one physical shell line, with `<branch>` resolved before composing the command:

```bash
printf '%s\n' '## Summary' '' '- <bullet>' '' '## Background' '' '<prose>' '' '## Test plan' '' '- [ ] <verification step>' '' '## Refs' '' '- <ref>' | GIT_TERMINAL_PROMPT=0 gh pr create --title "<commit-subject under 70 chars per /commit-changes>" --body-file - --head "<branch>"
```

Flag rationale:

- No `--draft` — the PR opens ready per /merging-standards `<authority_gates>`; `VERIFICATION_READINESS` (Step 3) is the gate that earns the open, and opening ready fires every CI review (Codex and the CI review) at once. A stacked PR is the one exception — pass `--draft` only when `<branch_topology>` holds it draft until its base merges.
- `--title` and `--body-file -` — explicit title plus body-from-stdin; matches /commit-changes conventions without writing to disk.
- `--head` — the feature branch; prevents gh from prompting for fork/push targets.
- `--base` — omit only for peer branches targeting the repo default; specify the previous stack branch for stacked PRs.
- `GIT_TERMINAL_PROMPT=0` — disables git credential prompts. (gh detects non-TTY stdin/stdout and skips its own prompts automatically; no `GH_*` env var is needed.)

The single-quoted heredoc terminator (`<<'EOF'`) disables shell expansion inside the body — backticks, `$variables`, and `!` pass through literally. Use the unquoted form (`<<EOF`) only when the body must interpolate shell variables. In programmatic runner form, single-quoted `printf` arguments preserve those characters literally; a literal apostrophe inside one line uses `'"'"'`. Never embed multi-line content in `--body "..."` — gh does not expand `\n` escapes. Never use temporary files, helper files, command substitution, or post-hoc text substitution to assemble or repair the body.

Do not use `--fill`. If both `--fill` and `--body-file` are passed, the explicit body wins; `--fill` is then dead weight.

**Step 6 — Start the first management pass.** Resolve the PR number, then invoke /manage-pr on that PR. `/manage-pr` owns pending checks, CI review waits, reinspection, merge gates, and post-merge closeout evidence.

**Exit.** Surface the PR URL. The managing flow takes over.

</the_opening_flow>

<title_format>

The PR title is one commit-subject line under 70 characters per /commit-changes:

- Single commit on the branch -> use that commit's subject as-is.
- Multiple commits -> synthesize one subject capturing the dominant type and scope. Read `git log --format=%s <base>..HEAD`, pick the dominant type from /commit-changes `<commit_types>`, write a description that summarizes the change across the commits (not a commit list).

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

- <full spec node path>
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

Body explains WHY for the reviewer; the diff already shows WHAT. Reference spec nodes by full path from `spx/`. No `<self_reference>` violations per /merging-standards.

</body_template>

<shell_scope>

The narrow Bash grants in frontmatter authorize approval-free execution. Run required consumer-declared commands from the product's root guide or active PR-opening specialization through normal harness per-call approval when they fall outside those grants, then continue the governed step without a separate lifecycle confirmation. When the harness exposes no approval path, stop with `MERGE_BLOCKED:project-command-approval-unavailable`, naming the command and declaring surface; never skip the command, widen `allowed-tools` during execution, or add repository-specific grants to this portable skill.

</shell_scope>

<failure_modes>

**Opened a PR gated on an earlier tree.** Claude established `VERIFICATION_READINESS`, then committed fixes during the convergence loop, and opened the PR without re-running deterministic verification, required evidence-auditor predicates, and local review on the final accumulated tree — so the opened diff was gated at an earlier state than the one CI receives. After every iteration that commits, re-run /merging-standards `<branch_hygiene>`, local deterministic verification, required evidence-auditor predicates, and the local review, treating `VERIFICATION_READINESS` as holding only when all predicates pass together on the exact tree the push publishes — never with the later-fixed predicate established before the last commit (Step 3).

**Push rejection after local readiness.** Claude reached `VERIFICATION_READINESS`, then the explicit destination push was rejected because the remote branch advanced or credentials failed. Re-run /sync-base for a remote advancement, re-establish `VERIFICATION_READINESS` on the resulting tree, and push again; for credentials or permission failure, stop with the exact command output and no PR mutation.

**Duplicate PR already exists.** Claude attempted `gh pr create` even though the branch already had an open PR. Detect an existing PR before creation or classify the `gh pr create` failure; switch to /manage-pr for that PR instead of opening a second PR or changing the branch name.

**Stacked topology opened ready too early.** Claude treated a stacked branch like a peer branch and opened it ready against the default base. When `<branch_topology>` classifies a stack, set the previous stack branch as `--base` and keep the PR draft until its base merges; do not satisfy `VERIFICATION_READINESS` against the wrong base.

**Convergence stall.** Claude repeated deterministic, evidence-audit, and review fixes without reaching one tree where all predicates held. Stop the loop when the next fix would expand the changeset beyond the requested scope, record the split-out concern in the owning node's coordination note, and run one final deterministic verification, required evidence-auditor predicates, and review on the narrowed branch before opening.

</failure_modes>

<success_criteria>

The opening flow has succeeded when:

- /merging-standards and /commit-changes are loaded before the flow begins, `merge-policy.md` is read directly from /merging-standards `<reference_index>` before any tagged policy section is used, and a fresh `spx worktree status` reading passes `<occupancy_preflight>` before checkout-sensitive mutation.
- /merging-standards `<branch_hygiene>` and `<branch_topology>` gates pass before push.
- `VERIFICATION_READINESS` held before the PR opened: local deterministic verification passed on the diff that will be pushed, every required evidence-auditor predicate passed, and the local review converged — every valid finding that belongs was applied, any valid finding too large to belong was split out (recorded in the relevant node's `ISSUES.md` / `PLAN.md`), and unbacked findings were dropped. Severity did not gate; validity and the before-open phase did.
- Push uses the explicit destination ref form from /merging-standards `<push_semantics>`.
- Title is one commit-subject line under 70 chars per /commit-changes.
- Body is delivered to gh via `--body-file -` on stdin (real newlines).
- The PR is opened `ready_for_review` (`gh pr create` with no `--draft`) once `VERIFICATION_READINESS` holds — except a stacked PR held draft per `<branch_topology>`.
- The first management pass starts after the PR opens; `/manage-pr` owns any pending checks, CI review waits, reinspection, merge gates, and post-merge closeout evidence, including /merging-standards `<pr_check_wait>`.
- PR URL is surfaced to the user.
- No `<self_reference>` violation per /merging-standards.

</success_criteria>
