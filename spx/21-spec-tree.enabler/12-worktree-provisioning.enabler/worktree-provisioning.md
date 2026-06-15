# Worktree Provisioning

PROVIDES the `init-worktrees` provisioning flow that classifies a checkout's git layout and brings a single or non-compliant checkout into the bare-repository worktree pool of `spx/21-spec-tree.enabler/11-repository-layout.pdr.md`, pushing every local ref to the remote and carrying a prior checkout's gitignored state across
SO THAT the session, reviewing, and merging workflows
CAN assume the shared-`.spx/` bare-pool topology without re-deriving or repairing it

## Assertions

### Scenarios

- Given a prior non-bare checkout carrying gitignored state, when `init-worktrees` provisions the pool, then `.spx/` sits beside the new `{repo}.git` git-common-dir with its contents preserved byte-for-byte, and every other gitignored path is carried into the main checkout ([test](tests/test_worktree_provisioning.scenario.l1.py))
- Given a request to provision `{repo}` with N pool worktrees against an existing remote, when `init-worktrees` completes, then `{repo}.git` is a bare repository, a sibling main checkout at the repository-name path (`<repo>/<repo-name>`, the container basename being the repository name) tracks the git-resolved default branch `origin/<default>`, and N additional worktrees exist detached at the `origin/<default>` tip ([test](tests/test_worktree_provisioning.scenario.l1.py))
- Given a prior checkout occupying the target container path, when `init-worktrees` provisions in place, then the prior checkout is renamed aside to a husk path reported for operator removal, and the pool is built at the original path ([test](tests/test_worktree_provisioning.scenario.l1.py))
- Given a prior checkout carrying a local-only branch and tag, when `init-worktrees` provisions the pool, then those refs are present on the remote afterwards ([test](tests/test_worktree_provisioning.scenario.l1.py))
- Given a checkout on disk, when its layout is probed and classified, then a lone working tree classifies as `single` and a non-bare checkout carrying a linked worktree classifies as `non-compliant` ([test](tests/test_worktree_provisioning.scenario.l1.py))

### Mappings

- A probed checkout layout maps to a compliance verdict: a lone working tree with no linked worktrees maps to `single`; a bare repository with a sibling main checkout whose basename equals the origin repository name and `.spx/` beside the git-common-dir maps to `pool`, independent of the branch checked out there; one or more linked worktrees on a non-bare repository maps to `non-compliant`; a bare pool missing the repository-name main checkout sibling, or missing the sibling `.spx/`, maps to `non-compliant` ([test](tests/test_worktree_provisioning.mapping.l1.py))

### Properties

- For every worktree in a provisioned pool, the `.spx/` directory resolved from that worktree is the one beside the git-common-dir ([test](tests/test_worktree_provisioning.property.l1.py))

### Compliance

- ALWAYS: `init-worktrees` derives the bare directory and main checkout name from the origin URL it clones — it takes no separate repository-name input — so the provisioned main checkout's basename always matches the name classification resolves from `git remote get-url origin` ([test](tests/test_worktree_provisioning.scenario.l1.py))
- ALWAYS: `init-worktrees` pushes every local branch and tag to the remote before building the pool, so no local-only ref is lost rather than surfacing unpushed refs for the operator to resolve ([test](tests/test_worktree_provisioning.scenario.l1.py))
- ALWAYS: the `init-worktrees` provisioner carries gitignored state to its layout-correct home — `.spx/` beside the git-common-dir at the container level, every other gitignored path into the main checkout — and the skill then purges the regenerable bulk moved into the main checkout by running the repository's declared clean target (`just clean`, `pnpm run clean`, or the command its `AGENTS.md` mandates), leaving `.spx/` untouched because it sits outside the main checkout's working tree. The clean is an agent-run command the skill performs (not provisioner code), so it is verified by audit of the skill's clean step rather than by a provisioner unit test ([audit])
- ALWAYS: `init-worktrees` refuses to provision when the prior checkout's `.spx/` is present but not gitignored — the gitignore-driven carry would skip and abandon it — directing the operator to gitignore `.spx/` first ([test](tests/test_worktree_provisioning.scenario.l1.py))
- ALWAYS: `init-worktrees` requires the container basename to equal the origin repository name, so the pool nests as `<repo>/<repo>` and is never scattered across the multi-repository workspace that holds it ([test](tests/test_worktree_provisioning.scenario.l1.py))
- NEVER: `init-worktrees` deletes a prior checkout's working tree itself — it renames the prior checkout aside to a husk, carries its gitignored state into the new pool, and emits the exact husk-removal command for the operator to run last ([audit])
- ALWAYS: `init-worktrees` keeps the prior-husk removal the operator's action — the skill itself runs only the classification, push, provisioning, and clean commands and never the husk removal; it re-classifies to confirm the `pool` verdict (valid independent of the husk, which sits outside the container) and then emits the husk-removal command as the final step, blocking on the operator's confirmation that it ran ([audit])
- ALWAYS: the provisioning helper complies with `spx/13-plugin-and-runtime-conventions.adr.md` — stdlib `python3` only, paths resolved via `${CLAUDE_SKILL_DIR}` — and reads or writes nothing outside the target container and the installed plugin tree, except pushing an explicitly provided prior checkout's refs to its remote and relocating that prior checkout's gitignored artifacts into the container ([audit])
