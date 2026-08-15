# Issues: Worktree Provisioning

## Provisioner extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/init-worktrees/scripts/init_worktrees.py` runs to
476 lines — three-layout classification (single tree, compliant bare-repo pool,
non-compliant), pool provisioning, the push of every local ref to the remote,
and the carry-across of a prior checkout's gitignored state. Past fifty lines
`spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves
into the SPX CLI once the script proves its value; the provisioner has proven
its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository. The same dependency
gates the waiter and the instruction-block generator, tracked in
`spx/13-infrastructure.enabler/13-host-readiness.enabler/ISSUES.md` and
`spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md`.

**Resolution shape**: port layout classification and pool provisioning into the
SPX CLI, publish it, advance the floor, and reduce the shipped skill to its
instruction with no script. Revisit when the capability publishes.

## Four universal Compliance assertions rest on scenario-typed evidence

Four `### Compliance` assertions in `worktree-provisioning.md` state universal
`ALWAYS` rules yet link `tests/test_worktree_provisioning.scenario.l1.py`: the
origin-derived main-checkout name, the push of every local ref, the refusal on a
non-gitignored `.spx/`, and the container-basename requirement. A universal is
never a scenario — a scenario proves one case and cannot establish an
always-true rule — so each needs `compliance` evidence exercising violating
fixtures.

The coupling itself is sound: the test-evidence audit traced every one of the
four to test functions that reach the governing source. The defect is the
declared evidence type, not the coverage.

**Resolution shape**: add `tests/test_worktree_provisioning.compliance.l1.py`,
move the violating-fixture tests that carry these four rules into it — the
refusal and fail-fast cases plus the origin-URL derivation cases — and re-point
the four assertion links. The scenario file keeps its genuinely existential
cases. Route the work through `/test`, which owns assertion typing and level
selection.

## A provisioned pool leaves every linked worktree reporting itself bare

`git` reads `core.bare` from the shared config at the git-common-dir unless `extensions.worktreeConfig` is enabled, which is what scopes that key per worktree. A bare-repository pool sets `core.bare = true` in `{repo}.git/config` by construction, and provisioning enables no per-worktree config, so every linked worktree in the pool inherits it.

The effect is that each linked worktree answers `git rev-parse --is-inside-work-tree` with `false` and `git rev-parse --show-toplevel` with `fatal: this operation must be run in a work tree`, and every command git gates on work-tree-ness — `git switch`, `git checkout`, `git restore`, `git stash` — refuses. Read commands that do not consult that gate still work, so the checkout looks healthy: `git status`, `git log`, `git diff`, `git worktree list`, and `git commit` all succeed, and `spx diagnose` reports the pool `compliant`. The failure appears only at the first branch operation.

Nothing in the tree covers this. `spx/21-spec-tree.enabler/11-repository-layout.pdr.md` declares the pool topology and reads bareness for classification but states nothing about the key's scope; `init-worktrees` and this node's assertions name neither `core.bare` nor `extensions.worktreeConfig`.

**Evidence**: in a pool provisioned at `/Users/shz/Code/outcomeeng/plugins/plugins.git`, `git config --show-origin --get-all core.bare` run from a linked worktree reports the value `true` originating from `file:/Users/shz/Code/outcomeeng/plugins/plugins.git/config`, `git config --get extensions.worktreeConfig` is empty, and `git -c core.bare=false rev-parse --is-inside-work-tree` answers `true` where the unmodified command answers `false`. Observed across the pool's linked worktrees while running the merge lifecycle for PR #524.

**Resolution shape**: enable `extensions.worktreeConfig` when provisioning the pool and move `core.bare` into the bare root's own worktree-scoped config, so linked worktrees resolve it as non-bare. Classification reads bareness from the common dir and is unaffected. Repairing an already-provisioned pool is the same one-time config change, which is why the fix belongs with provisioning rather than with each caller. A `[test]` on the provisioned layout asserting that a linked worktree resolves as a work tree would have caught this at the layer that creates it.

**Revisit condition**: before the next `init-worktrees` provisioning change, and ahead of the provisioner extraction recorded above, since the extracted capability would carry this behavior into the CLI.
