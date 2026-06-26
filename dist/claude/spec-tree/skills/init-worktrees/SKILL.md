---
name: init-worktrees
description: >-
  ALWAYS invoke this skill when setting up a repository's git worktree layout — classifying a checkout as a single tree, a bare-repo worktree pool, or non-compliant, and provisioning the bare-repo pool while pushing every local ref to the remote and carrying a prior checkout's gitignored state across. NEVER run git clone --bare plus git worktree add to build the pool outside this skill.
allowed-tools: Read, Bash(git:*), Bash(python3:*), Bash(just:*), Bash(pnpm:*), AskUserQuestion
---

<objective>

A repository in one of the two compliant git layouts: a single working tree, or a bare-repository worktree pool shaped `<repo>/{<repo>.git, <repo>, <repo>-a…, .spx}` — a bare `<repo>.git`, a main checkout tracking `origin/<default>`, a shared `.spx/`, and detached pool worktrees at the `origin/<default>` tip — so the default branch is claimable by no single worktree and every worktree resolves one shared `.spx/`.

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

Gather the provisioning inputs. Infer them; ask only for a genuine gap using the runtime's structured-question tool:

- **origin URL** — derive from the prior checkout (`git -C <prior> remote get-url origin`) or take it from the user. The provisioner reads the repository name `<repo>` from this URL; the bare directory and the main checkout are both named for it, so no separate repository name is passed.
- **container** — the repository-name directory beside the prior checkout: `<parent-of-prior>/<repo>`. In the common case the prior checkout already sits there (a clone names the directory for the repository), so the container **is** the prior checkout's own path and provisioning renames it aside to build the pool in place — never use the prior checkout's parent (the multi-repository workspace) as the container.
- **pool worktree names** — default to `<repo>-a`, `<repo>-b`, `<repo>-c`, `<repo>-d`; the main checkout, named for the repository, is always created.

</step>

<step name="provision">

Run the provisioner. It derives the repository name from the prior checkout's origin, pushes every local branch and tag to the remote so no local-only ref is lost, renames the prior checkout aside to a `<name>.migrate` husk when it occupies the target container path, clones `<repo>.git` bare, restores the `origin/*` fetch refspec a bare clone omits, resolves the default branch from the clone, adds the sibling main checkout tracking `origin/<default>`, adds one detached pool worktree per name at the `origin/<default>` tip, and carries the prior checkout's gitignored state across — `.spx/` beside the new git-common-dir, every other gitignored path into the main checkout:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" provision \
  --container <parent-of-prior>/<repo> --from <prior> \
  --worktree <repo>-a --worktree <repo>-b --worktree <repo>-c --worktree <repo>-d
```

For a fresh layout with no prior checkout, pass `--origin <url>` in place of `--from <prior>` (no push or carry runs). The command prints a JSON object including `main_worktree` and `prior_husk` — the renamed-aside prior checkout (or `null` when no in-place rename occurred). A non-zero exit is an error, not a partial success: surface it and resolve its cause (a diverged branch that fails to push, an unreachable remote, or a carried path whose home is already occupied) before re-running.

</step>

<step name="clean">

The carry moves **every** gitignored path into the main checkout — including regenerable bulk (`node_modules/`, `.venv/`, build output) whose absolute-path references break once moved. Purge it by running the repository's declared clean target in the main checkout, regenerating it fresh:

```bash
just -d <main_worktree> clean   # or `pnpm --dir <main_worktree> run clean`, or the command the repo's CLAUDE.md mandates
```

`.spx/` sits at the container level, outside the main checkout's working tree, so the clean never touches it — it is the one delicate piece of gitignored state, preserved. Skip this step only when the prior checkout carried no regenerable gitignored bulk.

</step>

<step name="confirm">

Re-classify the new main checkout to confirm a `pool` verdict:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_worktrees.py" classify --path <main_worktree>
```

This runs before the husk is removed, and the verdict is unaffected: the husk sits outside the pool's container, so classifying `<main_worktree>` reads only the pool. Confirming the pool before handing off removal keeps the husk as a safety net should provisioning be wrong.

</step>

<step name="hand_off_removal">

Provisioning never deletes the prior checkout — it renamed it aside. Emit the exact removal command for the operator to run, using the `prior_husk` the provisioner reported (or the original prior-checkout path when `prior_husk` was `null`):

```bash
rm -rf <prior_husk>
```

Then block on the runtime's structured-question tool (`AskUserQuestion` on Claude Code, `request_user_input` on Codex) asking the operator to confirm the removal ran. Do not run the removal — the operator runs it. The husk is fully redundant by this point: its branches and tags are on the remote and its gitignored state is in the new pool, so removing it loses nothing. Once the operator confirms the husk is removed, the provisioning flow is complete.

</step>

</workflow>

<constraints>

- NEVER check out a feature branch in the main checkout — keep it on the default branch and create feature branches in a pool worktree. The main checkout is the stable default-branch reference other worktrees and external tooling resolve against.
- NEVER use the prior checkout's parent (the multi-repository workspace) as the container — the container is the repository-name directory `<parent-of-prior>/<repo>`, so the pool nests as `<repo>/<repo>` rather than scattering the bare repo, `.spx/`, and worktrees across the workspace.
- NEVER delete a prior checkout's working tree from within this skill — the provisioner renames it aside, and the skill emits the husk-removal `rm` command for the operator, then blocks on the structured-question gate for their confirmation. The skill itself runs only the classification, provisioning, and clean commands — never the husk removal.
- NEVER add a dependency to the provisioner or reach outside the target container and the skill directory — it runs on stdlib `python3` alone, pushing the prior checkout's refs to its remote and relocating its gitignored artifacts into the container.

</constraints>

<failure_modes>

**Claude uses the prior checkout's parent as the container, scattering the pool across the workspace.** The target is `<repo>/<repo>` — a repository-name container holding the bare repo, main checkout, `.spx/`, and worktrees. Passing the workspace root (the prior checkout's parent) as `--container` dumps `<repo>.git`, `.spx/`, and every worktree beside every other repository in the workspace; the classifier still reports `pool` because it only checks placement relative to the git-common-dir, so the scatter goes unnoticed. The container is always `<parent-of-prior>/<repo>`.

**Claude checks out a feature branch in the main checkout, breaking tooling that resolves against it.** Running `git switch -c <feature>` inside the main checkout moves it off the default branch; every consumer that resolves against the default-branch checkout breaks until it is switched back. Create feature branches in a pool worktree — `git -C <repo>-a switch -c <feature>` — never in the main checkout.

**Claude skips the clean step and the moved `node_modules`/`.venv` breaks the main checkout.** The carry moves every gitignored path verbatim, including build artifacts whose absolute-path references (pnpm symlinks, venv shebangs) no longer resolve at the new location. Running the repository's clean target purges the regenerable bulk so it regenerates fresh; `.spx/` is untouched because it sits outside the main checkout's working tree.

**Claude re-runs `provision` after a script error instead of surfacing it.** The push and the `.spx/` pre-check both run before any building, so a diverged local branch the remote rejects, an origin URL that yields no repository name (`ValueError`), or a container that already holds `.spx/` (`FileExistsError`) leaves nothing built — surface the error and resolve its cause before re-running. A failure *after* an in-place rename is different: if the bare clone or a `git worktree add` fails once the prior checkout has been renamed to `<name>.migrate`, the husk persists and the container is empty or partially built. Recover by removing the partial container, renaming the husk back to the original path, resolving the underlying cause (restore remote access, free disk), then re-running — never re-run blindly onto the partial state. For a non-in-place provision (a fresh `--origin` build or a `--from` whose container differs from the prior path) there is no husk: a failed clone leaves only an empty container directory, which must be removed before re-running.

</failure_modes>

<success_criteria>

- [ ] `classify --path .` exits 0 and emits a `layout` of `single`, `pool`, or `non-compliant`
- [ ] A `pool` verdict ends the flow with no provisioning run
- [ ] Provisioning inputs gathered (origin, container as `<parent-of-prior>/<repo>`, pool worktree names)
- [ ] `provision` pushed every local branch and tag to the remote and carried the prior checkout's gitignored state across
- [ ] Bare `<repo>.git`, sibling main checkout (named for the repository) tracking `origin/<default>`, detached pool worktrees, and `.spx/` beside the git-common-dir all created under the repository-name container
- [ ] The repository's clean target ran in the main checkout to purge moved regenerable bulk
- [ ] `classify --path <main_worktree>` on the new main checkout emits `{"layout": "pool"}`
- [ ] Prior-husk removal handed to the operator, never run by the skill, with confirmation obtained through the structured-question gate

</success_criteria>
