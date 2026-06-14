---
name: init-worktrees
description: >-
  ALWAYS invoke this skill when setting up a repository's git worktree layout — classifying a checkout as a single tree, a bare-repo worktree pool, or non-compliant, and provisioning the bare-repo pool while carrying a prior checkout's .spx across. NEVER run git clone --bare plus git worktree add to build the pool outside this skill.
allowed-tools: Read, Bash(git:*), Bash(python3:*), AskUserQuestion
---

<objective>

Bring a repository into one of the two compliant git layouts and keep it there: a single working tree, or a bare-repository worktree pool. The pool is a bare `<repo>.git` repository whose git-common-dir has, as siblings, a **main checkout** — the worktree whose directory basename is the repository name, tracking the repository's git-resolved default branch `origin/<default>` — and a shared `.spx/` operational directory; additional pool worktrees are created detached at the `origin/<default>` tip. The layout keeps the default branch claimable by no single worktree and lets every worktree resolve one shared `.spx/`, which the session, review, and merge workflows depend on.

Deterministic classification and provisioning run in `scripts/init_worktrees.py`; this skill orchestrates that helper, gathers its inputs, and guards the one destructive step — removing a prior checkout — behind operator confirmation.

</objective>

<workflow>

<step name="classify">

Probe the current checkout and report its layout:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" classify --path .
```

On success the command exits 0 and prints one JSON object — `{"layout": "pool", "facts": {…}}` — whose `layout` is `single`, `pool`, or `non-compliant`. Read the verdict from that field; a non-zero exit or output that is not a single JSON object with a `layout` key is an error, not a verdict. A `pool` verdict means the layout is already compliant — report it and stop. A `single` or `non-compliant` verdict means provisioning the pool is the next step.

</step>

<step name="gather">

Gather the provisioning inputs. Infer what you can; ask only for genuine gaps using the runtime's structured-question tool:

- **container** — the directory that will hold `<repo>.git` and the worktrees. For a migration this is normally the parent of the prior checkout.
- **origin URL** — derive from the prior checkout (`git -C <prior> remote get-url origin`) or take it from the user. The provisioner reads the repository name from this URL; the bare directory and the main checkout are both named for it, so no separate repository name is passed.
- **pool worktree names** — default to `<repo>-a`, `<repo>-b`, `<repo>-c`, `<repo>-d`; the main checkout, named for the repository, is always created.

</step>

<step name="verify_remote">

Before any step that removes a prior checkout, confirm every local branch is present on the remote — the only state not recoverable from the remote is `.spx/`, which provisioning carries across:

```bash
git -C <prior> push --all --dry-run
```

If any branch is unpushed, stop and surface it. Do not proceed to removal until the operator pushes it or explicitly accepts the loss.

</step>

<step name="provision">

Run the provisioner. It reads the repository name from the origin URL, clones `<repo>.git` bare, restores the `origin/*` fetch refspec a bare clone omits, resolves the default branch from the clone, adds the sibling main checkout (named for the repository) tracking `origin/<default>`, adds one detached pool worktree per name at the `origin/<default>` tip, and moves the prior checkout's `.spx/` beside the new git-common-dir:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" provision \
  --container <container> --from <prior> \
  --worktree <repo>-a --worktree <repo>-b --worktree <repo>-c --worktree <repo>-d
```

For a fresh layout with no prior checkout, pass `--origin <url>` in place of `--from <prior>`.

</step>

<step name="hand_off_removal">

Provisioning never deletes the prior checkout. After `.spx/` is relocated and remote presence is verified, emit the exact removal command for the operator to run:

```bash
rm -rf <prior-checkout>
```

Then block on the runtime's structured-question tool (`AskUserQuestion` on Claude Code, `request_user_input` on Codex) asking the operator to confirm the removal ran. Do not run the removal — the operator runs it — and do not advance to `confirm` until the structured-question tool returns confirmation. A re-classification before the prior checkout is gone reports a `pool` verdict while the old checkout still exists on disk; the gate exists to prevent that false completion.

</step>

<step name="confirm">

Only after the `hand_off_removal` gate returns the operator's confirmation, re-classify the new main checkout to confirm a `pool` verdict:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" classify --path <container>/<repo>
```

</step>

</workflow>

<constraints>

- NEVER check out a feature branch in the main checkout — keep it on the default branch and create feature branches in a pool worktree. The main checkout is the stable default-branch reference other worktrees and external tooling resolve against.
- NEVER delete a prior checkout's working tree from within this skill — emit the `rm` command for the operator, then block on the structured-question gate for their confirmation, after `.spx/` is relocated and remote presence is verified. The skill itself runs only the classification, provisioning, and remote-check commands — never the removal — so the emitted `rm -rf` stays the operator's action.
- ALWAYS confirm every local branch is present on the remote before emitting any removal step — `.spx/` is the only state provisioning carries that the remote cannot restore.
- NEVER add a dependency to the provisioner or reach outside the target container and the skill directory — it runs on stdlib `python3` alone.

</constraints>

<failure_modes>

**Claude checks out a feature branch in the main checkout, breaking tooling that resolves against it.** Running `git switch -c <feature>` inside the main checkout moves it off the default branch; every consumer that resolves against the default-branch checkout breaks until it is switched back. Create feature branches in a pool worktree — `git -C <repo>-a switch -c <feature>` — never in the main checkout.

**Claude advances to `confirm` before the operator removes the prior checkout, reporting a false `pool`.** The `confirm` step classifies the new pool path, which is already a compliant `pool` whether or not the old checkout still exists, so re-classifying early reports completion while the prior checkout remains on disk. The `hand_off_removal` step blocks on the structured-question tool for exactly this reason — do not run `confirm` until the operator confirms the removal ran.

</failure_modes>

<success_criteria>

- [ ] The current checkout classified as `single`, `pool`, or `non-compliant`
- [ ] A compliant `pool` reported and left unchanged
- [ ] Provisioning inputs gathered (container, origin, pool worktree names)
- [ ] Every local branch confirmed present on the remote before any removal
- [ ] Bare `<repo>.git`, sibling main checkout (named for the repository) tracking `origin/<default>`, detached pool worktrees, and `.spx/` beside the git-common-dir all created
- [ ] Prior-checkout removal handed to the operator, never run by the skill
- [ ] Operator confirmation of the removal obtained through the structured-question gate before re-classifying
- [ ] New main checkout re-classified as `pool`

</success_criteria>
