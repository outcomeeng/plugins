---
name: opening-pr
description: >-
  ALWAYS invoke this skill when opening a pull request, creating a PR, or pushing a branch for review.
  NEVER invoke this skill to manage an open pull request — use /managing-pr for the post-creation loop.
allowed-tools: Read, Glob, Grep, Bash, Skill
---

<objective>
The opening flow. One-shot, linear: pre-flight → topology → local review gate → push → open draft → schedule first heartbeat → exit. Every step is a routine workflow operation that runs without operator confirmation. After exit, /managing-pr governs the post-creation loop.
</objective>

<project_specialization>
After loading this skill, check whether `spx/local/opening-pr.md` exists at the repository root. Read it if present and apply it as a product-specific addition to this flow (extra pre-flight checks, additional required body sections, project-specific push commands).

The overlay MUST NOT: fold promotion into `gh pr create`, skip the closure gate before promotion, skip or weaken the local review gate, override the always-draft mandate, or weaken the upstream-safety check.

Project-specific draft-lifecycle refinements (additional explicit-instruction signal forms; keep-ready rules across follow-up pushes) live in `spx/local/merging.md` instead, so /managing-pr and /opening-pr see the same rules.
</project_specialization>

<the_opening_flow>

Walk these steps in order. Every step is a routine workflow operation — schedule, push, open — and runs directly. The opening flow contains no operator-confirmation pauses.

**Step 0 — Load references.** Invoke /standardizing-merging (shared vocabulary) and /committing-changes (commit type/scope classification for the title) via the Skill tool.

**Step 1 — Pre-flight.** Run /standardizing-merging `<branch_hygiene>` checks. Every condition must hold or the flow stops at the first failed condition.

**Step 2 — Classify topology.** Run /standardizing-merging `<branch_topology>` peer or stacked gate. Repair or reclassify before pushing if the gate fails.

**Step 3 — Local review gate.** Run the changes-reviewer agent (preferred) on the working diff before push. The agent runs in an isolated context, so the verdict is not biased by everything the operator's main agent has been doing. Fall back to the `/review-changes` slash command when the agent is not installed — both invoke the same `reviewing-changes` skill chain and produce the same `review-result.json` / `review.md` artifacts under thread-store.

Apply the acceptance criterion to the resulting `review-result.json`. The gate is **severity-based**: the reviewer emits findings only (no decision/verdict), so the gate reads each finding's `severity` from the `findings` array directly.

- Any finding with `severity == "blocking"` or `severity == "debt"` → STOP. Fix every such finding, commit via /committing-changes, re-invoke the reviewer, and repeat until the `findings` array contains no `blocking` and no `debt` entry.
- Findings with `severity == "follow_up"` → fix the ones whose remediation stays within the PR's intended scope. Defer only those whose fix would widen scope substantively; record deferred items in the relevant node's `ISSUES.md` or `PLAN.md` (per /standardizing-merging `<review_classification>`) before pushing.
- `findings` array contains no `blocking` and no `debt` entry → proceed to Step 4. The severity check is the gate; the result carries no decision field.

The local review gate is stricter than the remote merge gate. The remote gate (per /standardizing-merging `<pr_authority_gate>`) allows `follow_up` findings tracked elsewhere and stops on `blocking` / `debt` only. The local pre-push pass aims for the remote review to surface nothing — every finding fixable in this PR's scope is fixed before push, and only widening-scope `follow_up` items survive to remote.

The iteration loop accumulates commits on the branch — the eventual push at Step 4 sends them all. After every iteration that commits, re-run /standardizing-merging `<branch_hygiene>` before the next reviewer invocation so the predicates stay current.

**Step 4 — Push.** Use the explicit destination ref form from /standardizing-merging `<push_semantics>`:

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"
```

If the product defines a custom branch-push command, follow CLAUDE.md / AGENTS.md instead — the explicit destination ref must remain part of any custom command.

**Step 5 — Open the draft PR.** Pipe the curated body to gh on stdin via `--body-file -`:

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

Flag rationale:

- `--draft` — mandatory on every PR open per /standardizing-merging `<pr_authority_gate>`. Promotion is the managing flow's concern.
- `--title` and `--body-file -` — explicit title plus body-from-stdin; matches /committing-changes conventions without writing to disk.
- `--head` — the feature branch; prevents gh from prompting for fork/push targets.
- `--base` — omit only for peer branches targeting the repo default; specify the previous stack branch for stacked PRs.
- `GIT_TERMINAL_PROMPT=0` — disables git credential prompts. (gh detects non-TTY stdin/stdout and skips its own prompts automatically; no `GH_*` env var is needed.)

The single-quoted heredoc terminator (`<<'EOF'`) disables shell expansion inside the body — backticks, `$variables`, and `!` pass through literally. Use the unquoted form (`<<EOF`) only when the body must interpolate shell variables. Never embed multi-line content in `--body "..."` — gh does not expand `\n` escapes.

Do not use `--fill`. If both `--fill` and `--body-file` are passed, the explicit body wins; `--fill` is then dead weight.

**Step 6 — Schedule the first heartbeat.** Per /standardizing-merging `<heartbeat>`, schedule the first review/check re-inspection through the runtime timer. Verify by capturing the URL or thread ID returned by the runtime tool; only fall back to explicit user confirmation when the runtime cannot create one directly.

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

<success_criteria>

The opening flow has succeeded when:

- /standardizing-merging and /committing-changes are loaded before the flow begins.
- /standardizing-merging `<branch_hygiene>` and `<branch_topology>` gates pass before push.
- The local review gate ran on the diff that will be pushed and `review-result.json` contains no `blocking` or `debt` findings; any `follow_up` items either fixed in-PR or recorded in the relevant node's `ISSUES.md` / `PLAN.md` with widening-scope as the deferral rationale.
- Push uses the explicit destination ref form from /standardizing-merging `<push_semantics>`.
- Title is one commit-subject line under 70 chars per /committing-changes.
- Body is delivered to gh via `--body-file -` on stdin (real newlines).
- PR is opened as draft (`gh pr create --draft`).
- First heartbeat is scheduled per /standardizing-merging `<heartbeat>`.
- PR URL is surfaced to the user.
- No `<self_reference>` violation per /standardizing-merging.

</success_criteria>
