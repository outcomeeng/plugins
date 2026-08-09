---
name: open-parent-pr
description: >-
  ALWAYS invoke this skill when opening a pull request against a repository the operator does not control — a fork's parent, or any base whose permission is READ or NONE.
  NEVER open a pull request against such a repository without this skill.
argument-hint: "[what the change does, or empty to describe it from the branch]"
allowed-tools: Read, Glob, Grep, Skill, Agent, AskUserQuestion, Bash(python3 "${CLAUDE_SKILL_DIR}/../contribution-standards/scripts/resolve_target.py":*), Bash(gh auth status:*), Bash(gh repo view:*), Bash(gh pr create:*), Bash(gh pr view:*), Bash(gh pr list:*), Bash(git fetch:*), Bash(git switch:*), Bash(git branch:*), Bash(git status:*), Bash(git rev-parse:*), Bash(git log:*), Bash(git diff:*), Bash(git push -u origin HEAD:refs/heads/*), Bash(printf:*)
---

<objective>
One pull request open against a repository the operator does not control, carrying a change already verified against that repository's own checks.
</objective>

<workflow>

**Step 1 — Load the standards.** Invoke `/contribution-standards` through the runtime's skill-composition surface. Its `<invariants>` govern every step below; this workflow adds ordering and the pull-request specifics.

**Step 2 — GATE: Resolve the target.** Run the resolver named in `/contribution-standards` `<resolution>` and act on its `classification`. Report `base`, `head`, and `permission` verbatim. `controlled`, `fork-absent`, and `blocked` each stop here — `controlled` belongs to a controlled-repository pull-request flow, and the other two stop per the standards. Only `parent-contribution` continues.

**Step 3 — GATE: Obtain authorization.** Present, through the runtime's structured-question tool, the resolved `base`, the resolved `head`, the change in one sentence, and the choice to authorize the pull request against that base or to stop and inspect. Create nothing in the base repository until the operator authorizes it in this turn.

The authorization covers this pull request and its later revisions. It does not carry to a second pull request, an issue, or a comment on an unrelated thread.

**Step 4 — Cut the branch from the base default branch.**

```bash
git fetch origin
base_default=$(gh repo view "$base" --json defaultBranchRef --jq '.defaultBranchRef.name')
git fetch "$base_remote" "$base_default"
```

Branch from that fetched ref, never from the head repository's default branch. When the checkout carries no remote for the base repository, add the change onto a branch cut from the fetched base ref rather than rewriting remotes.

**Step 5 — Conform to the base repository's conventions.** Before writing code, read what that repository declares: its contributing guide, the READMEs governing any fixture or test-data directory the change touches, metadata schemas, the documents a change of this kind updates, and the commit-message style of recent history. Shape the change to those conventions.

**Step 6 — GATE: Run the base repository's own verification.** Locate its declared checks — the commands its contributing guide names, its workflow files, and its build and test targets — and run them locally. They must report success.

Capture verbose output in a directory from `mktemp -d`, inspect the exit status and failing sections, and remove the directory on every exit path. Fix failures and re-run until green. A check that cannot run locally is recorded for Step 8's body with the reason it could not run; never report it as passed and never drop it silently.

**Step 7 — GATE: Review the outward text.** Draft the title and body per `<title_and_body>`, then review them per `/contribution-standards` `<invariants>` "Outward-facing text is permanent". Where the prose plugin is installed, dispatch its `prose-auditor` agent through the runtime's agent-dispatch surface and apply its findings. Where it is not, review against `/contribution-standards` `<outward_text>` and state in the report that the review ran unassisted.

**Step 8 — Push, then open.** Push the branch to the head repository with the explicit destination ref, then open the pull request naming the base repository:

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"
```

Interactive Claude Code and Codex sessions pipe the body through a quoted heredoc:

```bash
GIT_TERMINAL_PROMPT=0 gh pr create \
  --repo "<base>" \
  --base "<base-default-branch>" \
  --head "<head-owner>:<branch>" \
  --title "<subject under 70 chars>" \
  --body-file - <<'EOF'
## Summary

- <bullet>

## Verification

- <base repository check> — passed
- <check that could not run> — unverified, <reason>

## Refs

- <issue or discussion this answers>
EOF
```

Programmatic runners that require one physical command line use one `printf` argument per output line:

```bash
printf '%s\n' '## Summary' '' '- <bullet>' '' '## Verification' '' '- <check> — passed' '' '## Refs' '' '- <ref>' | GIT_TERMINAL_PROMPT=0 gh pr create --repo "<base>" --base "<base-default-branch>" --head "<head-owner>:<branch>" --title "<subject>" --body-file -
```

Pass `--draft` when the contribution is unsolicited or its conformance to the base repository's conventions remains uncertain.

Flag rationale:

- `--repo` — the resolved base. Without it `gh` opens against whatever it resolves from the checkout, which for a fork is the parent, reached by inference rather than by decision.
- `--head <owner>:<branch>` — the head repository and branch, stated explicitly so the head never depends on inference and no fork-selection prompt appears.
- `--base` — the base repository's default branch, resolved in Step 4.
- `--body-file -` — the body arrives on stdin with real newlines. `--body` does not expand escape sequences, and no temporary file, command substitution, or post-hoc repair assembles the body.

**Step 9 — Hand off.** Surface the pull-request URL, then invoke `/manage-parent-pr` on it.

</workflow>

<title_and_body>

The title is one subject line under 70 characters, in the commit-message style of the base repository's recent history — not the operator's own convention.

The body states what the change does, what verification ran, and what it answers. Sections:

- **Summary** — one or two bullets a maintainer can read before the diff.
- **Verification** — each of the base repository's declared checks with its result, and each check that could not run locally marked unverified with its reason.
- **Refs** — the issue or discussion the change answers.

A defect fix adds a **Root cause** paragraph and carries the evidence `/contribution-standards` requires: tool versions, the base commit observed against, the command that produced the observation, and a negative control.

The body explains why; the diff already shows what. Never name the agent or its runtime anywhere in the title, body, or commits.

</title_and_body>

<constraints>

- MUST resolve the target through the bundled resolver before the first write — reading `isFork`, `parent`, and `viewerPermission` by eye is the failure this gate exists to prevent.
- MUST obtain authorization naming the resolved base in the same turn before creating the pull request.
- MUST name the base repository with `--repo` and the head with `--head <owner>:<branch>` on `gh pr create`.
- MUST cut the contribution branch from the base repository's default branch.
- NEVER open against a base whose classification is `controlled`, `fork-absent`, or `blocked`.
- NEVER create the fork — report the destination candidates and stop.
- NEVER report an unrunnable check as passed, or omit it from the body.

</constraints>

<failure_modes>

**A resolved default stood in for a named target.** Claude ran `gh pr create` from a fork checkout without `--repo`, and `gh` resolved the base to the parent. The command would have published to an organization nobody named, and nothing in its output said so. Resolve first, pass `--repo`, and report the resolved values verbatim.

**The branch was cut from the fork's default.** Claude branched from the head repository's default branch, which was thirty-one commits behind the base. The resulting diff carried unrelated divergence, and the maintainer's first comment was about the noise rather than the change. Fetch the base repository's default branch and cut from that ref.

</failure_modes>

<success_criteria>

- The resolver returned `parent-contribution`, and `base`, `head`, and `permission` appear verbatim in the report.
- The operator authorized this pull request against the resolved base in the turn it was created.
- The contribution branch was cut from the base repository's default branch.
- The base repository's declared checks ran locally and reported success; any check that could not run is named in the body as unverified with its reason.
- The title and body passed a prose review, and a review that ran unassisted is reported as such.
- `gh pr create` named the base with `--repo` and the head with `--head <owner>:<branch>`, and the body arrived on stdin.
- The pull-request URL is surfaced and `/manage-parent-pr` has taken over.

</success_criteria>
