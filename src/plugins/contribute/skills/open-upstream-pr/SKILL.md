---
name: open-upstream-pr
description: >-
  ALWAYS invoke this skill when opening a pull request against a repository the operator does not control — a fork's upstream, or any base whose permission is READ, TRIAGE, or NONE.
  NEVER open a pull request against such a repository without this skill.
argument-hint: "[what the change does, or empty to describe it from the branch]"
allowed-tools: Read, Glob, Skill,{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}},{!% endif %!} {{! tool('ask_user') !}}, Bash(git remote get-url origin), Bash(gh repo view:*), Bash(gh api users/*), Bash(gh pr create:*), Bash(git fetch:*), Bash(git rev-parse:*), Bash(git switch:*), Bash(git cherry-pick:*), Bash(git diff:*), Bash(git status --porcelain), Bash(git add:*), Bash(git commit:*), Bash(git branch --show-current), Bash(git log:*), Bash(git push -u origin HEAD:refs/heads/*), Bash(mktemp -d), Bash(printf:*)
---

<objective>
One pull request open against a repository the operator does not control, carrying a change verified against every one of that repository's own checks that could run locally, with any that could not named in the body as unverified.
</objective>

<workflow>

**Step 1 — Load the standards and read the invocation input.** Invoke `/contribution-standards` through the runtime's skill-composition surface. Its `<invariants>` govern every step below; this workflow adds ordering and the pull-request specifics.

`$ARGUMENTS`, when non-empty, is the one-sentence description of the change used in Step 3's authorization and in the Step 9 body. When it is empty, derive that sentence from the checkout's current branch at invocation — the branch the change was written on, distinct from the `<branch>` Step 4 cuts — and its own commit subjects (`git log --format=%s origin/HEAD..HEAD`), which needs nothing a later step resolves.

**Step 2 — GATE: Establish the target.** Read the live `<UPSTREAM_TARGET>` marker; invoke `/upstream` when none is live. Report `base`, `head`, and `permission` verbatim.

Only `upstream-contribution` continues — a pull request needs a head to push from. `controlled` belongs to a controlled-repository pull-request flow. `head-ambiguous` and `fork-absent` each stop per `/contribution-standards` `<resolution>`, and `blocked` stops with the resolver's `detail` verbatim.

**Step 3 — GATE: Obtain authorization.** Present, through the runtime's structured-question tool, the resolved `base`, the resolved `head`, the change in one sentence, and the choice to authorize the pull request against that base or to stop and inspect. Create nothing in the base repository until the operator authorizes it in this turn.

The authorization covers this pull request and its later revisions. It does not carry to a second pull request, an issue, or a comment on an unrelated thread.

**Step 4 — Cut the branch from the base default branch.** Fetch it by URL so the step never depends on a remote name the checkout may not carry:

```bash
gh repo view "<base>" --json defaultBranchRef --jq '.defaultBranchRef.name'
```

Derive `<branch>` from the one-sentence description Step 1 resolved: lowercase it, drop every word that names neither the action nor its subject, join what remains with hyphens, and stop at five words. "Fix the flaky retry timeout in the webhook handler" keeps six words and stops at five, giving `fix-flaky-retry-timeout-webhook`. The branch names the change and nothing else — never the operator, the fork, or Claude. Resolve it here, because Step 9 reads it back from the checkout and a branch that does not exist yet answers nothing.

Read the default-branch name, then fetch and branch in a second block:

```bash
git fetch "https://github.com/<base>.git" "<base-default-branch>"
git rev-parse FETCH_HEAD
```

Record what `git rev-parse` printed as `<base-tip>` and use that SHA in every later comparison, starting with the next command. `FETCH_HEAD` is overwritten by the next fetch from any source — one inside a check Step 6 runs, or inside a commit hook — so a later `FETCH_HEAD...HEAD` diff can silently compare against an unrelated commit and report a real contribution as empty.

Read whether this branch already exists before creating it:

```bash
git rev-parse --verify --quiet "refs/heads/<branch>"
```

It prints a SHA when an earlier pass already cut the branch — the name derives from the description, so a retry after a failed replay, an aborted cherry-pick, or a failed creation lands on the same one. `git switch -c` refuses an existing branch, so decide here rather than stopping on its error with no instruction:

- **Nothing printed.** The branch is new; cut it below.
- **The printed SHA equals `<base-tip>`.** The earlier pass cut the branch and got no further. Take it with plain `git switch "<branch>"`, then continue at the replay below.
- **Any other SHA.** The branch carries commits from an earlier attempt. Report the branch, that SHA, and `git log --format='%h %s' <base-tip>..<branch>`, then stop. Whether those commits are the contribution to keep or the wreckage of an aborted replay is a decision about the contribution; discarding them or building on them silently makes it for the operator.

```bash
git switch -c "<branch>" FETCH_HEAD
```

Branch from `FETCH_HEAD`, never from the head repository's default branch, which is behind by however long since the last sync.

**When the contribution already exists as commits on the invocation branch**, cutting at `FETCH_HEAD` alone abandons them and pushes the base tip. Replay them onto the new branch before continuing, and confirm the diff against `<base-tip>` carries the intended change:

```bash
git cherry-pick <first-commit>^..<last-commit>
git diff --stat <base-tip>...HEAD
```

The `^` is required. `A..B` means every commit reachable from `B` but not from `A`, so naming the first contribution commit as `A` excludes it: a multi-commit contribution silently loses its earliest commit, and a single-commit contribution replays nothing at all while the empty result still looks like a completed replay. `<first-commit>^` names that commit's parent, which is the range's exclusive end.

An empty diff **from that replay** means the cherry-pick range named no commit and the contribution was left behind; stop rather than carrying an empty branch forward. This gate belongs to the replay and runs only when one ran. A contribution that exists as uncommitted edits enters no replay at all — `git switch -c` carries those edits onto the new branch — so it reaches Step 8, where the commit gate stages them and the same diff is read against a tree that now holds a commit.

A conflict stops the replay mid-pick and leaves the checkout in that state. Run `git cherry-pick --abort` to return it to the branch tip, then report the conflicting commit and stop. The replay conflicts because the base moved under the change, and reconciling it is a decision about the contribution rather than a step of cutting the branch.

**Step 5 — Conform to the base repository's conventions.** Before writing code, read what that repository declares: its contributing guide, the READMEs governing any fixture or test-data directory the change touches, metadata schemas, the documents a change of this kind updates, and the commit-message style of recent history. Locate them by pattern rather than by guessing at paths — `**/CONTRIBUTING*`, `**/README*`, and the directories the change touches — then read each one. Shape the change to those conventions.

**Step 6 — GATE: Run the base repository's own verification.** Locate its declared checks — the commands its contributing guide names, its workflow files, and its build and test targets — and run them locally. They must report success. Those commands belong to that repository and cannot be enumerated here, so they run per `/contribution-standards` `<capability_scope>` rather than from this skill's grants; the same applies to editing the files Step 5 shapes.

Capture verbose output in a directory from `mktemp -d`, inspect the exit status and failing sections, and remove the directory on every exit path. Fix failures and re-run until green. A check that cannot run locally is recorded for Step 9's body with the reason it could not run; never report it as passed and never drop it silently.

**Step 7 — GATE: Review the outward text.** Draft the title and body per `<title_and_body>`, then review them per `/contribution-standards` `<invariants>` "Outward-facing text is permanent". Where the prose plugin is installed, dispatch its `prose-auditor` thin agent through the runtime's agent-dispatch surface and apply its findings. Where it is not, review against `/contribution-standards` `<outward_text>` and state in the report that the review ran unassisted.

**Step 8 — GATE: Commit what the push will carry.** A push transfers commits. Everything above — the branch cut, the conventions, the base repository's own checks, the outward-text review — can run against edits sitting in the working tree, and none of them reach the pull request. Read the tree before pushing:

```bash
git status --porcelain
```

Empty output means every verified change is already committed. Any output is the contribution, or part of it, still uncommitted: commit it in the base repository's commit style and re-run Step 6, because the checks passed against a tree that is now the commit.

```bash
git add <contribution-paths>
git commit -m "<message in the base repository's commit style>"
```

Confirm the branch carries a change before continuing. `git diff --stat <base-tip>...HEAD` empty here means the pull request would be empty; stop rather than opening it.

**Step 9 — Push, then open.** Confirm `origin` resolves to the resolved head per `/contribution-standards` `<resolution>` "Verify `origin` before pushing or fetching through it" — a remote name is a local label, and pushing through the wrong one publishes the contribution to a repository nobody named:

```bash
gh repo view "$(git remote get-url origin)" --json nameWithOwner --jq '.nameWithOwner'
```

**STOP when that does not equal the resolved `head`.** Then push the branch with the explicit destination ref and open the pull request naming the base repository.

Derive `<head-owner>` from the resolved `head`, which the resolver reports as `owner/name`: take the portion before the `/`. `gh pr create --head` reads `owner:branch`, so passing the whole `owner/name` there names no head at all.

```bash
branch=$(git branch --show-current)
git push -u origin HEAD:refs/heads/"${branch}"
```

`gh pr create --head <owner>:<branch>` resolves a user-owned head; `gh` does not support an organization as that owner. Read which one this head has, because the resolver reports fork candidates only when no fork exists — the classification this flow never continues on — so its candidate list is empty here and answers nothing:

```bash
gh api users/"<head-owner>" --jq '.type'
```

`User` takes `--head <head-owner>:<branch>`. `Organization` cannot be selected that way at all: run the creation from a checkout whose `origin` is that head repository and pass `--head <branch>` alone. Stop with the resolved head named when neither form selects it — never fall back to a head `gh` picks.

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
- `--head <head-owner>:<branch>` — the head repository's owner and the branch, both resolved above, stated explicitly so the head never depends on inference and no fork-selection prompt appears. An organization-owned head drops the owner and passes `--head <branch>` from a checkout whose `origin` is that repository, per the account-type read above.
- `--base` — the base repository's default branch, resolved in Step 4.
- `--body-file -` — the body arrives on stdin with real newlines. `--body` does not expand escape sequences, and no temporary file, command substitution, or post-hoc repair assembles the body.

**Step 10 — Hand off.** Surface the pull-request URL, then invoke `/manage-upstream-pr` on it.

</workflow>

<title_and_body>

The title is one subject line under 70 characters, in the commit-message style of the base repository's recent history — not the operator's own convention.

The body states what the change does, what verification ran, and what it answers. Sections:

- **Summary** — one or two bullets a maintainer can read before the diff.
- **Verification** — each of the base repository's declared checks with its result, and each check that could not run locally marked unverified with its reason.
- **Refs** — the issue or discussion the change answers.

A defect fix adds a **Root cause** paragraph and carries the evidence `/contribution-standards` requires: tool versions, the base commit observed against, the command that produced the observation, and a negative control.

The body explains why; the diff already shows what.

</title_and_body>

<constraints>

- MUST establish the target through `/upstream` before the first write — reading `isFork`, `parent`, and `viewerPermission` by eye is the failure that gate exists to prevent.
- MUST obtain authorization naming the resolved base in the same turn before creating the pull request.
- MUST name the base repository with `--repo` on `gh pr create`, and name the head explicitly rather than letting `gh` resolve one: `--head <head-owner>:<branch>` for a user-owned head, `--head <branch>` from a checkout whose `origin` is the head repository when that head is organization-owned. `gh` documents the qualified form as `<user>:<branch>`, so requiring it unconditionally steers an organization-owned head back into the form that cannot select it.
- MUST cut the contribution branch from the base repository's default branch, under a name derived in Step 4 before the first command that uses it.
- NEVER discard or build on commits an earlier pass left on the derived branch. Read whether the branch exists before `git switch -c`, take it only when its tip is `<base-tip>`, and otherwise report its commits and stop.
- NEVER force-push. The `Bash(git push -u origin HEAD:refs/heads/*)` grant matches by prefix, so it admits `--force` and `--force-with-lease` too; this constraint is the whole containment for those flags.
- NEVER pass `--force` or `--discard-changes` to `git switch` — the `Bash(git switch:*)` grant matches by prefix and admits both, and either one drops uncommitted work in the invocation checkout. Cutting the contribution branch never needs them.
- NEVER write through `gh api users`. The `Bash(gh api users/*)` grant matches by prefix, so it admits `-X PATCH` and `-X DELETE` after the owner segment; this constraint is the whole containment for those verbs. It reads the head owner's account type and nothing else.
- NEVER stage by wildcard. The `Bash(git add:*)` grant matches by prefix, so it admits `-A` and `.`, either of which sweeps unrelated work in the invocation checkout into a commit bound for someone else's repository. Name the contribution's paths.
- NEVER pass `--no-verify` to `git commit`. The `Bash(git commit:*)` grant matches by prefix and admits it. Hooks run from this checkout's own configuration, which conforming to the base repository's conventions is what installs, so skipping them drops part of the verification Step 6 requires.
- NEVER cherry-pick a commit outside the invocation branch's own range. The `Bash(git cherry-pick:*)` grant matches by prefix, so it admits any revision the checkout can name; Step 4 replays that branch's commits and nothing else.
- NEVER open a pull request whose diff against `<base-tip>` is empty at the Step 8 commit gate — the pull request would carry nothing. Step 4's identical check belongs to the replay and applies only to a pass that ran one; an uncommitted contribution is empty there by construction and is committed in Step 8.
- NEVER open against a base whose classification is `controlled`, `fork-absent`, or `blocked`.
- NEVER create the fork — report the destination candidates and stop.
- NEVER report an unrunnable check as passed, or omit it from the body.

</constraints>

<failure_modes>

**A resolved default stood in for a named target.** Claude ran `gh pr create` from a fork checkout without `--repo`, and `gh` resolved the base to the parent. The command would have published to an organization nobody named, and nothing in its output said so. Resolve first, pass `--repo`, and report the resolved values verbatim.

**The branch was cut from the fork's default.** Claude branched from the head repository's default branch, which was thirty-one commits behind the base. The resulting diff carried unrelated divergence, and the maintainer's first comment was about the noise rather than the change. Fetch the base repository's default branch and cut from that ref.

</failure_modes>

<success_criteria>

- The resolver returned `upstream-contribution`, and `base`, `head`, and `permission` appear verbatim in the report.
- The operator authorized this pull request against the resolved base in the turn it was created.
- The contribution branch was cut from the base repository's default branch, and a branch an earlier pass had already cut was taken only at `<base-tip>`; one carrying commits stopped the flow with those commits named.
- The branch's diff against `<base-tip>` carried the change before the push; an empty diff at either gate stopped the flow with nothing opened, and every criterion below covers a pass that opened.
- The base repository's declared checks ran locally and reported success; any check that could not run is named in the body as unverified with its reason.
- The title and body passed a prose review, and a review that ran unassisted is reported as such.
- The head owner's account type was read before the head form was chosen, and `gh pr create` named the base with `--repo` and named the head explicitly — `<head-owner>:<branch>` for a user, `<branch>` alone for an organization — with the body arriving on stdin.
- The pull-request URL is surfaced and `/manage-upstream-pr` has taken over.

</success_criteria>
