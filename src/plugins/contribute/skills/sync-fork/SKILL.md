---
name: sync-fork
description: >-
  ALWAYS invoke this skill when bringing a fork's default branch current with the repository it was forked from.
  NEVER bring a fork's default branch current with `gh repo sync`, `git merge`, or `git reset` run directly.
allowed-tools: Read, Skill, Bash(git remote get-url origin), Bash(gh repo view:*), Bash(gh repo sync:*), Bash(git fetch:*), Bash(git rev-list:*), Bash(git log:*)
---

<objective>
The fork's default branch current with its upstream's default branch, or the divergence that prevents it named commit by commit.
</objective>

<workflow>

**Step 1 — Load the standards.** Invoke `/contribution-standards` through the runtime's skill-composition surface for the upstream, base, and head vocabulary.

**Step 2 — GATE: Establish the target.** Read the live `<UPSTREAM_TARGET>` marker; invoke `/upstream` when none is live. Only `upstream-contribution` continues — it is the classification that reports both a head repository and the upstream it was forked from. `head-ambiguous` names several forks, and choosing which to sync is the operator's. `fork-absent` has nothing to sync, `controlled` describes a repository that is not a fork of another party's, and `blocked` stops with the resolver's `detail` verbatim.

**Step 3 — Read the two default branches.** Substitute the resolved values literally per `/contribution-standards` `<resolution>`:

```bash
gh repo view "<head>" --json defaultBranchRef --jq '.defaultBranchRef.name'
gh repo view "<base>" --json defaultBranchRef --jq '.defaultBranchRef.name'
```

**Step 4 — GATE: Establish behind versus diverged.** Confirm `origin` resolves to the resolved head per `/contribution-standards` `<resolution>` before fetching through it — a remote name is a local label, and this step decides whether to discard commits:

```bash
gh repo view "$(git remote get-url origin)" --json nameWithOwner --jq '.nameWithOwner'
```

**STOP when that does not equal the resolved `head`.** Fetch the base default branch by URL, so the count never depends on a remote name the checkout may not carry, then count commits on each side:

```bash
git fetch origin "<head-default-branch>"
git fetch "https://github.com/<base>.git" "<base-default-branch>"
git rev-list --left-right --count "origin/<head-default-branch>...FETCH_HEAD"
```

The left count is commits the fork's default branch carries that the upstream does not. When it is zero the fork is behind and Step 5 syncs it. When it is greater than zero the fork's default branch is **diverged**: someone committed there, and syncing would discard that work.

A diverged default branch stops the flow. Read the commits the count reported on the left, which is the side `origin/<head-default-branch>` carries and the upstream does not:

```bash
git log --format='%h %s (%an)' "FETCH_HEAD..origin/<head-default-branch>"
```

Report each one with its subject and author, and the branch or pull request that could preserve it. Never resolve divergence by discarding.

**Step 5 — Sync.**

```bash
gh repo sync "<head>" --source "<base>" --branch "<head-default-branch>"
```

`--branch` names the branch to update in the destination, so it is the head's default branch — the one Step 4 compared. Naming the base's default instead updates a differently-named branch, or fails, and either way leaves the fork's default stale. When the two defaults carry different names, report both and stop: `gh repo sync` matches by name, and choosing which branch tracks which is the operator's call.

NEVER pass `--force`. The flag exists to make the fork's default branch match the upstream's by discarding whatever the fork carries, which is the outcome Step 4 stops for.

**Step 6 — Report.** State the head repository, the upstream, the branch synced, and the commit count the sync advanced. When Step 4 found divergence, state that instead and leave both repositories untouched.

</workflow>

<worked_example>

One diverged fork, `operator-org/parser` forked from `acme/parser`, to compare a report against. Step 4's count decides the whole flow:

```console
$ git rev-list --left-right --count "origin/main...FETCH_HEAD"
2	17
```

The left number is 2, so `main` carries two commits `acme/parser` has never seen and Step 5 never runs. `0	17` would read as behind-only and sync. Name what the left side holds:

```console
$ git log --format='%h %s (%an)' "FETCH_HEAD..origin/main"
c41d09e Pin the parser version for the demo (R. Ellis)
8a2f7b1 Add local notes on the strict flag (R. Ellis)
```

The report:

```text
operator-org/parser's default branch `main` has diverged from acme/parser's. It
carries 2 commits the upstream does not, and it is 17 behind:

- c41d09e Pin the parser version for the demo (R. Ellis)
- 8a2f7b1 Add local notes on the strict flag (R. Ellis)

Syncing discards both. `git switch -c demo-pins main` in this checkout keeps
them, and whichever belongs upstream can go through /open-upstream-pr. Neither
repository was changed.
```

The report names every commit by subject and author, so the operator recognizes the work before deciding its fate. It offers the branch that preserves them rather than asking whether to discard, and it says plainly that nothing moved — a divergence report that ends without that sentence reads like a failed sync.

</worked_example>

<constraints>

- MUST establish the upstream through `/upstream`, never from a remote carrying that name — a remote name is a local label that identifies no repository.
- MUST classify behind versus diverged before syncing.
- NEVER pass `--force` to `gh repo sync`. The `Bash(gh repo sync:*)` grant matches by prefix, so it admits `--force` too — the allow-list cannot express "every flag but this one". This constraint is the whole containment for that flag, not a restatement of what the grant already blocks.
- NEVER resolve divergence by discarding commits; report them and stop.
- NEVER treat a stale fork default branch as a blocker for opening a contribution — a contribution branch is cut from the base repository's default branch.

</constraints>

<success_criteria>

- The `<UPSTREAM_TARGET>` marker read for this pass carries `upstream-contribution`, and `base` and `head` appear verbatim.
- Behind and diverged were distinguished by commit count before any mutation.
- A behind fork's default branch matches its upstream's, and the advanced commit count is reported.
- A diverged fork's default branch is untouched, with every commit unique to it named by subject and author.
- No force flag and no reset appears in any executed command.

</success_criteria>
