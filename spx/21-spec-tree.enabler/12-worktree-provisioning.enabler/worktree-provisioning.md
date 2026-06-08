# Worktree Provisioning

PROVIDES the `init-worktrees` provisioning flow that classifies a checkout's git layout and brings a single or non-compliant checkout into the bare-repository worktree pool of `spx/21-spec-tree.enabler/11-repository-layout.pdr.md`, carrying a prior checkout's `.spx/` across
SO THAT the session, reviewing, and merging workflows
CAN assume the shared-`.spx/` bare-pool topology without re-deriving or repairing it

## Assertions

### Scenarios

- Given a prior non-bare checkout that contains a `.spx/` directory, when `init-worktrees` provisions the pool, then `.spx/` sits beside the new `{repo}.git` git-common-dir with its contents preserved byte-for-byte ([test](tests/test_worktree_provisioning.scenario.l1.py))
- Given a request to provision `{repo}` with N pool worktrees against an existing remote, when `init-worktrees` completes, then `{repo}.git` is a bare repository, a sibling `main` worktree tracks `origin/main`, and N additional worktrees exist detached at the `origin/main` tip ([test](tests/test_worktree_provisioning.scenario.l1.py))
- Given a checkout on disk, when its layout is probed and classified, then a lone working tree classifies as `single` and a non-bare checkout carrying a linked worktree classifies as `non-compliant` ([test](tests/test_worktree_provisioning.scenario.l1.py))

### Mappings

- A probed checkout layout maps to a compliance verdict: a lone working tree with no linked worktrees maps to `single`; a bare repository with a sibling `main` worktree tracking `origin/main` and `.spx/` beside the git-common-dir maps to `pool`; one or more linked worktrees on a non-bare repository maps to `non-compliant`; a bare pool missing the `main` sibling, lacking `main`-to-`origin/main` tracking, or missing the sibling `.spx/` maps to `non-compliant` ([test](tests/test_worktree_provisioning.mapping.l1.py))

### Properties

- For every worktree in a provisioned pool, the `.spx/` directory resolved from that worktree is the one beside the git-common-dir ([test](tests/test_worktree_provisioning.property.l1.py))

### Compliance

- ALWAYS: before emitting any step that removes a prior checkout, `init-worktrees` verifies every local branch is present on the remote and names `.spx/` as the only state not recoverable from the remote ([audit])
- NEVER: `init-worktrees` deletes a prior checkout's working tree itself — it emits the exact removal command for the operator to run after `.spx/` is relocated and remote presence is verified ([audit])
- ALWAYS: the provisioning helper complies with `spx/13-plugin-and-runtime-conventions.adr.md` — stdlib `python3` only, paths resolved via `${CLAUDE_SKILL_DIR}` — and reads or writes nothing outside the target container and the installed plugin tree, except relocating an explicitly provided prior-checkout `.spx/` into the container ([audit])
