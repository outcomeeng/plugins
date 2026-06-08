---
name: init-worktrees
description: >-
  ALWAYS invoke this skill when setting up a repository's git worktree layout — classifying a checkout as a single tree, a bare-repo worktree pool, or non-compliant, and provisioning the bare-repo pool while carrying a prior checkout's .spx across. NEVER hand-run git clone --bare plus git worktree add to build the pool without this skill.
allowed-tools: Read, Bash
---

<objective>

Bring a repository into one of the two compliant git layouts and keep it there: a single working tree, or a bare-repository worktree pool. The pool is a bare `<repo>.git` repository whose git-common-dir has, as siblings, a `main` worktree tracking `origin/main` and a shared `.spx/` operational directory; additional pool worktrees are created detached at the `origin/main` tip. The layout keeps `main` claimable by no single worktree and lets every worktree resolve one shared `.spx/`, which the session, review, and merge workflows depend on.

Deterministic classification and provisioning run in `scripts/init_worktrees.py`; this skill orchestrates that helper, gathers its inputs, and guards the one destructive step — removing a prior checkout — behind operator confirmation.

</objective>

<workflow>

<step name="classify">

Probe the current checkout and report its layout:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" classify --path .
```

The verdict is `single`, `pool`, or `non-compliant`. A `pool` verdict means the layout is already compliant — report it and stop. A `single` or `non-compliant` verdict means provisioning the pool is the next step.

</step>

<step name="gather">

Gather the provisioning inputs. Infer what you can; ask only for genuine gaps using the runtime's structured-question tool:

- **container** — the directory that will hold `<repo>.git` and the worktrees. For a migration this is normally the parent of the prior checkout.
- **repo name** — the bare directory is `<repo>.git`.
- **origin URL** — derive from the prior checkout (`git -C <prior> remote get-url origin`) or take it from the user.
- **pool worktree names** — default to `<repo>-a`, `<repo>-b`, `<repo>-c`, `<repo>-d`; the `main` worktree is always created.

</step>

<step name="verify_remote">

Before any step that removes a prior checkout, confirm every local branch is present on the remote — the only state not recoverable from the remote is `.spx/`, which provisioning carries across:

```bash
git -C <prior> push --all --dry-run
```

If any branch is unpushed, stop and surface it. Do not proceed to removal until the operator pushes it or explicitly accepts the loss.

</step>

<step name="provision">

Run the provisioner. It clones `<repo>.git` bare, restores the `origin/*` fetch refspec a bare clone omits, adds the sibling `main` worktree tracking `origin/main`, adds one detached pool worktree per name at the `origin/main` tip, and moves the prior checkout's `.spx/` beside the new git-common-dir:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" provision \
  --container <container> --repo <repo> --from <prior> \
  --worktree <repo>-a --worktree <repo>-b --worktree <repo>-c --worktree <repo>-d
```

For a fresh layout with no prior checkout, pass `--origin <url>` in place of `--from <prior>`.

</step>

<step name="hand_off_removal">

Provisioning never deletes the prior checkout. After `.spx/` is relocated and remote presence is verified, emit the exact removal command for the operator to run, and wait for confirmation before treating the layout as complete:

```bash
rm -rf <prior-checkout>
```

</step>

<step name="confirm">

Re-classify the new `main` worktree to confirm a `pool` verdict:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" classify --path <container>/main
```

</step>

</workflow>

<constraints>

- NEVER check out a feature branch in the default-branch (`main`) worktree — keep it on the default branch and create feature branches in a pool worktree. The default-branch worktree is the stable reference other worktrees and external tooling resolve against.
- NEVER delete a prior checkout's working tree from within this skill — emit the `rm` command for the operator and wait, after `.spx/` is relocated and remote presence is verified.
- ALWAYS confirm every local branch is present on the remote before emitting any removal step — `.spx/` is the only state provisioning carries that the remote cannot restore.
- The provisioner runs on stdlib `python3` alone — never add a dependency or reach outside the target container and the skill directory.

</constraints>

<failure_modes>

**A feature branch checked out in the default-branch worktree breaks tooling that resolves against it.** Running `git switch -c <feature>` inside the default-branch worktree moves that worktree off the default branch; every consumer that resolves against the default-branch checkout breaks until it is switched back. Create feature branches in a pool worktree — `git -C <repo>-a switch -c <feature>` — never in the default-branch worktree.

</failure_modes>

<success_criteria>

- [ ] The current checkout classified as `single`, `pool`, or `non-compliant`
- [ ] A compliant `pool` reported and left unchanged
- [ ] Provisioning inputs gathered (container, repo, origin, pool worktree names)
- [ ] Every local branch confirmed present on the remote before any removal
- [ ] Bare `<repo>.git`, sibling `main` worktree tracking `origin/main`, detached pool worktrees, and `.spx/` beside the git-common-dir all created
- [ ] Prior-checkout removal handed to the operator, never run by the skill
- [ ] New `main` worktree re-classified as `pool`

</success_criteria>
