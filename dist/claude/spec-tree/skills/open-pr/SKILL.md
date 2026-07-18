---
name: open-pr
user-invocable: false
description: >-
  PR opening protocol for VERIFICATION_READINESS, explicit branch publication, topology-appropriate pull-request state, and lifecycle handoff.
allowed-tools: Read, Glob, Grep, Agent, AskUserQuestion, Bash(gh auth status:*), Bash(gh repo view:*), Bash(gh pr view:*), Bash(gh pr create:*), Bash(git status:*), Bash(git fetch:*), Bash(git merge-base:*), Bash(git diff:*), Bash(git rev-parse:*), Bash(git branch:*), Bash(git push:*), Bash(git log:*), Bash(printf:*), Skill
---

<objective>
A pull request opened in the review state its topology permits — ready for a peer branch or draft for a stacked branch awaiting its base.
</objective>

<project_specialization>
Step 0 checks whether `spx/local/open-pr.md` exists at the repository root only after the live foundation gate holds. When present, read it and apply it as a product-specific addition to this flow (extra pre-flight checks and additional required body sections).

The overlay MUST NOT: skip or weaken the local deterministic-verification, evidence-auditor, local-review, or terminal full-deterministic predicates of `VERIFICATION_READINESS`; open the PR before `VERIFICATION_READINESS` holds; open a peer PR as a draft gating step; keep a stacked PR draft after its exact base PR merges and reconstruction succeeds; add another draft-to-ready gate beyond that stack dependency; or weaken the upstream-safety check.

Deployment and release recognition, merge command, and local deterministic verification scope live in `spx/local/merging.md`, giving PR publication and management one policy source. Step 0 reaches that optional overlay through /merging-standards only after the live foundation gate holds. The local deterministic-verification commands come from the project's own `CLAUDE.md` convention, with the overlay allowed to centralize scope and escalation cases.
</project_specialization>

<workflow>

Walk these steps in order. Verification, review, push, and open continue without a separate workflow confirmation. When a consumer-defined command requires normal harness tool approval per `<shell_scope>`, obtain that approval and resume the same step; harness approval and the overlay's pre-mutation confirmation are distinct boundaries.

**Step 0 — Load foundation, references, and overlays.** If `<SPEC_TREE_FOUNDATION>` is absent, invoke /understand first. After the marker is live, invoke /merging-standards (shared vocabulary, including its conditional `spx/local/merging.md` read) and /commit-changes (commit type/scope classification for the title) via the Skill tool. Then check whether `spx/local/open-pr.md` exists; read it only when present. Never read either repository overlay before the foundation marker is live.

**Step 1 — GATE: Classify topology.** Run /merging-standards `<branch_topology>` peer gate or pre-create stacked classification. Start from the peer gate against the repository default; repair as peer when divergence is accidental. When the dependency is intentionally stacked, use an exact `stack_base_pr_pointer` already present in caller state or ask for that pointer through the runtime's structured-question capability. Resolve it with `gh pr view "<stack-base-pr-pointer>" --json number,url,state,headRefName,headRefOid,baseRefName`; require `state == OPEN`, then record the returned full URL as `stack_base_pr_url`, the returned literal `headRefName` as `stack_base`, `topology=stacked`, and `active_base=stack_base`. For a peer branch, record `topology=peer` and set `active_base` to the repository default branch. Run the peer gate against the default `active_base` or the pre-create stacked classification against the recorded `stack_base`; a missing or mismatched stack-base PR fails classification before verification. Carry the resolved `stack_base_pr_url` and `stack_base` unchanged into the `gh pr create --base` argument and complete `## Stack` body section in Step 5.

**Step 2 — GATE: Preliminary branch hygiene.** Run /merging-standards `<branch_hygiene>` with the `active_base` recorded in Step 1. Every condition must hold or the flow stops at the first failed condition. This early pass prevents verification work on an invalid branch; Step 4 repeats hygiene after the verification fixpoint.

<step name="verification_readiness_decision">

**Step 3 — GATE: Evaluate `VERIFICATION_READINESS`.** Per /merging-standards `<authority_gates>`, the PR opens ready only when `VERIFICATION_READINESS` holds — all predicates below.

*(a) Deterministic verification.* Run the project's local deterministic verification per /merging-standards `<local_deterministic_scope>` — validation and testing for the touched scope, escalating only when the overlay or risk evidence requires a wider local run. Capture verbose stdout/stderr in a temporary log path and inspect only the exit status, summary, and failing sections. It must report success; fix failures and re-run until green.

*(b) Evidence-auditor predicates.* Dispatch every evidence auditor /merging-standards `<authority_gates>` requires for the diff: `test-evidence-auditor` for changed `[test]` assertions, linked tests, or imported test-infrastructure artifacts; `eval-evidence-auditor` for changed `[eval]` assertions, eval artifacts, or producer artifacts for eval-backed assertions. Handle rejected, failing, or unknown verdicts per /merging-standards `<auditor_verdicts>`, re-running deterministic verification and the relevant auditor until the evidence predicate is clean.

*(c) Local review to convergence.* Run the `changes-reviewer` agent on the working diff — it runs in an isolated context, so the verdict is not biased by everything the operator's main context has been doing. Invoke it per /merging-standards `<local_review_invocation>`: for a peer branch pass only the raw scope `HEAD`; for a stacked branch pass only the raw scope `origin/<active-base>...HEAD`, replacing `<active-base>` with the recorded stack-base branch. Add no interpretive scope, severity pre-filter, or instruction on what to emphasize; the reviewer reads the repository's own instructions and the shared taxonomy itself. The reviewer emits findings only (no decision/verdict); process its findings by **validity and phase** per /merging-standards `<review_classification>` — this is the before-open phase:

- **Validate each finding** against its cited rule, the product-local / language / spec-tree governance, and the PDR/ADR decisions. Drop any finding the citation does not support.
- **Apply every valid finding that belongs.** Treat each valid finding as defect-class evidence: sweep the touched node(s) for parallel instances with the same rule, source contract, evidence pattern, lifecycle step, or generated-source relationship. Fix the cited site and every in-scope parallel instance, commit via /commit-changes, re-invoke the reviewer, and repeat. When a valid finding's fix is too large to belong in this changeset, **split it out** — the work leaves the diff, recorded in the owning node's `ISSUES.md` or `PLAN.md` — instead of applying it here.
- **Converged** when the working diff carries no unapplied valid finding that belongs. Severity never decides; validity and the before-open phase do.

*(d) Terminal full deterministic gate.* When the project overlay requires a full deterministic bundle, commit the converged subject, require a clean worktree, and run the declared full-gate command once after the evidence auditors and local review converge on that exact committed head. Never run it concurrently with another heavy command. A later change invalidates this predicate, reopens every affected agentic predicate, and requires the full gate again only after those predicates reconverge.

The iteration accumulates commits on the branch — the eventual push at Step 4 sends them all. After every iteration that commits, re-run /merging-standards `<branch_hygiene>`, re-run local deterministic verification, re-run required evidence-auditor predicates for touched evidence surfaces, and re-run the local review before the terminal full deterministic gate — all `VERIFICATION_READINESS` predicates must hold together on the exact tree the push publishes, so loop until a single tree passes all predicates (the joint fixpoint of /manage-pr Step 6: a verification-driven fix is a diff the review has not seen, an evidence-audit fix changes the evidence surface, and a review-driven fix is a tree verification has not covered). `VERIFICATION_READINESS` holds only when (a), (b), (c), and applicable (d) hold; only then proceed. The before-open pass is the strictest point in the lifecycle: every valid finding that belongs is applied here and only split-out work survives to the CI review, which on the open PR must show no unresolved valid `BLOCKING` or `DEBT` finding.

</step>

**Step 4 — GATE: Publication preflight and push.** Run every overlay-declared preflight check per /merging-standards `<overlay_safety_checks>`, then repeat `<branch_hygiene>` with the Step 1 `active_base` so the complete preflight guards the exact checkout state the remote receives. Use the explicit destination ref form from /merging-standards `<push_semantics>`:

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"
```

If `spx/local/merging.md` defines a custom branch-push command, follow that overlay instead — the explicit destination ref must remain part of any custom command.

**Step 5 — GATE: Open the PR in its topology state.** Pipe the curated body to gh on stdin via `--body-file -`. A peer PR opens `ready_for_review` because `VERIFICATION_READINESS` holds (Step 3). A stacked PR targets its previous stack branch and remains draft until that base merges. Choose the stdin form by harness.

Bind the topology-specific arguments and body inside the same shell invocation as `gh pr create`. A peer branch passes no additional arguments and omits the `## Stack` section. A stacked branch targets its previous stack branch, remains draft until the exact base PR merges, and includes a `## Stack` section whose merge-order line names the recorded full `stack_base_pr_url` and `stack_base` branch. Replace both placeholders in the body with those host-observed values before executing the command.

Interactive Claude Code and Codex sessions use a quoted heredoc. Peer PRs use this form and omit the stack section:

```bash
GIT_TERMINAL_PROMPT=0 gh pr create \
  --title "<commit-subject under 70 chars per /commit-changes>" \
  --body-file - \
  --head "$(git branch --show-current)" <<'EOF'
## Summary

- <bullet>

## Background

<prose>

## Changes

- <change>

## Test plan

- [ ] <verification step>

## Refs

- <ref>
EOF
```

Stacked PRs use this form, replacing `<stack-base-pr-url>` and `<stack-base>` in the body with the recorded host-observed values before execution:

```bash
GIT_TERMINAL_PROMPT=0 gh pr create \
  --title "<commit-subject under 70 chars per /commit-changes>" \
  --body-file - \
  --head "$(git branch --show-current)" \
  --base "<stack-base>" \
  --draft <<'EOF'
## Summary

- <bullet>

## Background

<prose>

## Changes

- <change>

## Stack

- Merge after <stack-base-pr-url> (branch: <stack-base>).

## Test plan

- [ ] <verification step>

## Refs

- <ref>
EOF
```

Programmatic runners that require one physical command line use `printf` with one argument per output line. Select the peer or stacked form after topology classification. Each command may wrap visually in a rendered view; keep each as one physical shell line, with `<branch>`, `<stack-base-pr-url>`, and `<stack-base>` replaced by their recorded literal values before composing it.

Peer PR:

```bash
printf '%s\n' '## Summary' '' '- <bullet>' '' '## Background' '' '<prose>' '' '## Changes' '' '- <change>' '' '## Test plan' '' '- [ ] <verification step>' '' '## Refs' '' '- <ref>' | GIT_TERMINAL_PROMPT=0 gh pr create --title "<commit-subject under 70 chars per /commit-changes>" --body-file - --head "<branch>"
```

Stacked PR:

```bash
printf '%s\n' '## Summary' '' '- <bullet>' '' '## Background' '' '<prose>' '' '## Changes' '' '- <change>' '' '## Stack' '' '- Merge after <stack-base-pr-url> (branch: <stack-base>).' '' '## Test plan' '' '- [ ] <verification step>' '' '## Refs' '' '- <ref>' | GIT_TERMINAL_PROMPT=0 gh pr create --title "<commit-subject under 70 chars per /commit-changes>" --body-file - --head "<branch>" --base "<stack-base>" --draft
```

Flag rationale:

- No `--draft` — the PR opens ready per /merging-standards `<authority_gates>`; `VERIFICATION_READINESS` (Step 3) is the gate that earns the open, and opening ready fires every CI review (Codex and the CI review) at once. A stacked PR is the one exception — pass `--draft` only when `<branch_topology>` holds it draft until its base merges.
- `--title` and `--body-file -` — explicit title plus body-from-stdin; matches /commit-changes conventions without writing to disk.
- `--head` — the feature branch; prevents gh from prompting for fork/push targets.
- `--base` — omit only for peer branches targeting the repo default; specify the previous stack branch for stacked PRs.
- `GIT_TERMINAL_PROMPT=0` — disables git credential prompts. (gh detects non-TTY stdin/stdout and skips its own prompts automatically; no `GH_*` env var is needed.)

The single-quoted heredoc terminator (`<<'EOF'`) disables shell expansion inside the body — backticks, `$variables`, and `!` pass through literally. Use the unquoted form (`<<EOF`) only when the body must interpolate shell variables. In programmatic runner form, single-quoted `printf` arguments preserve those characters literally; a literal apostrophe inside one line uses `'"'"'`. Never embed multi-line content in `--body "..."` — gh does not expand `\n` escapes. Never use temporary files, helper files, command substitution, or post-hoc text substitution to assemble or repair the body.

Do not use `--fill`. If both `--fill` and `--body-file` are passed, the explicit body wins; `--fill` is then dead weight.

**Step 6 — Capture the opened PR identity.** Read the host-observed identity after creation:

```bash
gh pr view --json number,url,body,headRefName,headRefOid,baseRefName,state,isDraft,reviews,comments
```

Require `headRefOid` to equal the full published branch HEAD and the observed topology fields to match Step 5. For a peer PR, require the observed `body` to contain no complete `## Stack` section. For a stacked PR, run /merging-standards `<branch_topology>` existing-PR stacked gate: require the observed base to equal the recorded `stack_base`, the PR to remain draft, and the observed `body` to contain one complete `## Stack` section whose merge-order line contains the exact recorded `stack_base_pr_url` and `stack_base`; missing, placeholder, duplicate, or mismatched stack metadata fails the opening protocol. Surface the PR number, URL, full head SHA, head branch, base branch, and draft state as this protocol's result. This opening protocol performs no PR-management action.

**Exit.** End after surfacing the opened PR identity and topology state.

</workflow>

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
| Stacked PR  | Add `## Stack` with a merge-order line naming the exact base PR URL and full branch.      |

Body explains WHY for the reviewer; the diff already shows WHAT. Reference spec nodes by full path from `spx/`. No `<self_reference>` violations per /merging-standards.

</body_template>

<shell_scope>

The narrow Bash grants in frontmatter authorize approval-free execution; they do not prohibit a consumer-defined command that the harness approves per call. Run commands from `CLAUDE.md` or `spx/local/merging.md` through that normal tool-approval path when they fall outside those grants. Never widen `allowed-tools` during execution.
After approval, continue the governed step without introducing a separate lifecycle-confirmation decision.
When the harness exposes no approval path for a required project command, stop with `MERGE_BLOCKED:project-command-approval-unavailable`; never skip the command or add repository-specific grants to this portable skill.

</shell_scope>

<failure_modes>

**Opened a PR gated on an earlier tree.** Claude established `VERIFICATION_READINESS`, then committed fixes during the convergence loop, and opened the PR without re-running deterministic verification, required evidence-auditor predicates, local review, and the applicable terminal full deterministic gate on the final accumulated tree — so the opened diff was gated at an earlier state than the one CI receives. After every iteration that commits, re-run /merging-standards `<branch_hygiene>`, local deterministic verification, required evidence-auditor predicates, and the local review before running the required terminal full gate, treating `VERIFICATION_READINESS` as holding only when all predicates pass together on the exact tree the push publishes — never with the later-fixed predicate established before the last commit (Step 3).

**Push rejection after local readiness.** Claude reached `VERIFICATION_READINESS`, then the explicit destination push was rejected because the remote branch advanced or credentials failed. Re-run /sync-base for a remote advancement, re-establish `VERIFICATION_READINESS` on the resulting tree, and push again; for credentials or permission failure, stop with the exact command output and no PR mutation.

**Duplicate PR already exists.** Claude attempted `gh pr create` even though the branch already had an open PR. Detect an existing PR before creation or classify the `gh pr create` failure; switch to /manage-pr for that PR instead of opening a second PR or changing the branch name.

**Stacked topology opened ready too early.** Claude treated a stacked branch like a peer branch and opened it ready against the default base. When `<branch_topology>` classifies a stack, set the previous stack branch as `--base` and keep the PR draft until its base merges; do not satisfy `VERIFICATION_READINESS` against the wrong base.

**Convergence stall.** Claude repeated deterministic, evidence-audit, and review fixes without reaching one tree where all predicates held. Stop the loop when the next fix would expand the changeset beyond the requested scope, record the split-out concern in the owning node's coordination note, and run one final deterministic verification, required evidence-auditor predicates, and review on the narrowed branch, followed by the terminal full deterministic gate when required, before opening.

</failure_modes>

<success_criteria>

The opened pull request is sound when:

- Its URL, number, head branch, head SHA, base branch, and draft state are observable from the host and match the published branch.
- A peer PR targets the repository default branch and is ready for review; a stacked PR targets its declared stack base, is draft, and records the host-observed base PR URL and branch in `## Stack`.
- The published head is the exact clean committed tree for which every `VERIFICATION_READINESS` predicate holds.
- The title is one Conventional Commit subject under 70 characters, and the body contains every section required by `<body_template>` and the active project overlay; conditional sections appear only when their applicability rules require them, with real newlines throughout.
- The remote branch was published through an explicit `HEAD:refs/heads/<branch>` destination.
- The surfaced result contains the PR number, URL, full `headRefOid`, head branch, base branch, and draft state, and no identity string prohibited by /merging-standards `<self_reference>`.

</success_criteria>
