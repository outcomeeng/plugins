# Marketplace Merge Rules

Loaded by `/merging-standards` `<repo_local_overlay>` and `/merge`. The product-specific values the merge skills read; the gates, transport selection, and protocols are injected by those skills.

## Deployment and release recognition

Never ask the operator whether to merge.

Deployment is declared as advancing the designated main checkout to the merged tip, governed by `DEPLOYMENT_READINESS` and detailed under `## Deploy`. It mutates local environment state — a checkout this repository's own later sessions resolve against — and nothing a consumer of the published plugins observes, which is the boundary `spx/15-merging.pdr.md` draws between the two phases. It reaches outside the assigned worktree and surfaces its own approval prompt.

Release is declared as persistent marketplace installation from the merged assigned checkout, governed by `RELEASE_READINESS` and detailed under `## Release`.

## Canonical checkout safety

Run the released default diagnosis before the first merge mutation, without a manifest. `@outcomeeng/spx` 0.6.15 and newer select every registered diagnostic provider when neither a manifest nor a configured check set is supplied, so the default machine report includes `worktree-pool`; the plugin-shipped manifest remains the fully instrumented contract for the user-invoked `/diagnose` skill:

```bash
git rev-parse --show-toplevel
spx diagnose --format json
```

Inspect the JSON record whose `name` is `worktree-pool`; do not gate on the aggregate exit code or `overall`, because an independent check may degrade the aggregate. The preflight holds only when all of these predicates are true:

- the report is valid JSON and contains exactly one `worktree-pool` record;
- that record's `verdict` is `compliant`;
- `readings.mainCheckoutPath` is a non-empty absolute path;
- `readings.mainCheckoutBranchRead` is `true`;
- `readings.mainCheckoutBranch` equals `readings.defaultBranch`;
- the assigned worktree root from `git rev-parse --show-toplevel` differs from `readings.mainCheckoutPath`.

Stop before mutation and report the record verbatim when any predicate fails. A missing, detached, wrong-branch, or unreadable designated main checkout blocks the lifecycle, as does an assigned worktree that is itself the designated main checkout. The merge lifecycle never switches, detaches, or performs feature-branch cleanup in the designated main checkout.

After detach-based feature-worktree cleanup, run `spx diagnose --format json` again and require the same `worktree-pool` health predicates. At that point the assigned feature worktree may be detached, while the designated main checkout must remain readable and attached to the resolved default branch.

## Merge command

Use a merge commit, matching this product's `main` history style and the universal default:

```bash
gh pr merge <pr-number> --merge --delete-branch=false
```

`--delete-branch=false` is explicit because `gh`'s default for the omitted flag is unknowable across environments and its local-cleanup step fails in this multi-worktree checkout. Remote branch deletion remains a separate cleanup action after the post-cleanup diagnosis below passes.

## Post-merge feature-worktree cleanup

After the canonical-checkout preflight proves that the assigned worktree is a distinct feature worktree, detach that feature worktree onto the merged commit, repeat the complete diagnostic predicate set, and only then delete the remote feature branch:

```bash
git fetch origin main
git switch --detach origin/main
git rev-parse --show-toplevel
spx diagnose --format json
```

Stop and inspect the post-cleanup `worktree-pool` record and assigned-root output under the canonical checkout safety predicates. A failed check leaves the feature worktree detached and the remote branch intact for inspection. Only after every predicate passes, run:

```bash
git push origin --delete <branch>
```

## Deterministic verification commands

The touched-scope principle is `/merging-standards` `<local_deterministic_scope>`; these are this repository's commands per scope:

- Spec-only (specs, decisions, coordination notes, Markdown): `spx validation markdown` and `spx spec status --format json`.
- Skill/doc Markdown under `src/plugins/` or `dist/`: `just check-skills` and `just docs-check`.
- Implementation, test, validation-config, or broad changes: the focused node/package/module tests plus the narrow validation lane that covers the changed files, widening to full `just check-full` for shared validation or test infrastructure, package-manager files, generated catalog output, distribution build machinery, or another escalation the governing node or risk evidence requires per `/merging-standards` `<local_deterministic_scope>`. Test infrastructure is shared when a test under more than one node, or `conftest.py`, imports it; a harness or generator imported only by the tests of the node whose changeset carries it is covered by that node's tests. Distribution build machinery is the generator the `dist/` relation in `spx/local/generated-sources.toml` names, `outcomeeng/distribution/`; regenerated `dist/` output that follows a `src/plugins/` edit belongs to the skill/doc Markdown lane above, with source-to-output parity established by the pre-commit `build-skills` run and the gate's `dist-diff` step. Generated catalog output is the marker-bounded plugin catalog section of `README.md`, the output of the README relation `spx/local/generated-sources.toml` declares; its sources are the ones that relation lists. The automatic `just check` selector applies this same boundary through the static import index `spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/21-test-infrastructure-reach.adr.md` declares: a change under `outcomeeng_testing/` selects the tests that import it when they sit under one node, and the full surface when they span nodes, when `conftest.py` imports it, or when the artifact is reached by path rather than import.

Marketplace installation changes include `just verify-marketplace-installation` in the focused deterministic scope. This command runs the repository-installation node's complete pytest-discovered evidence in disposable homes and performs no persistent installation.

When the full `just check-full` bundle is required, it is the terminal local deterministic gate. Run the focused lane first, then all applicable evidence auditors and agentic reviews to convergence, then run `just check-full` once against the clean committed head. Never run `just check-full` before those agentic checks, inside an agent, or concurrently with another heavy command. Any change after it invalidates the result and reopens the affected agentic gates before the next full-gate run.

## Governance surfaces (base-sync review reuse)

A prior local review is reusable across a clean rebase only when the branch patch is unchanged **and** no base-delta path is a governance surface: `AGENTS.md`, `CLAUDE.md`, any `spx/local/*.md`, the bundled review prompt at `src/plugins/spec-tree/skills/review-changes/references/review-prompt.md`, or any standards reference under `src/plugins/*/skills/*-standards/` or `src/plugins/*/skills/**/SKILL.md`.

## Mention-reviewer trigger phrase

`@spec-tree` (configured in `.github/workflows/spec-tree-review.yml` `trigger_phrase`; repository-variable override `SPEC_TREE_REVIEW_TRIGGER_PHRASE`).

## Deploy: advance the designated main checkout

The `DEPLOY` phase, governed by `DEPLOYMENT_READINESS`, runs after the merge and before `RELEASE`. Phase order is the merge skill's; this overlay declares only what each phase does, never when it runs relative to a transport's cleanup or closeout step.

The merge moved `origin/main` while `readings.mainCheckoutPath` stayed at the pre-merge commit, so every worktree and later context load resolving against the local `main` reads a stale commit until that one checkout moves. The canonical-checkout preflight above already resolved and health-checked it; occupancy is a separate reading, because a clean working tree never proves a checkout is free.

```bash
spx -C <main-checkout-path> worktree status --format json
git -C <main-checkout-path> status --porcelain
git -C <main-checkout-path> merge --ff-only origin/main
```

The global `-C` option is how every cross-checkout `spx` invocation in this repository selects its target, and `@outcomeeng/spx@0.6.15` — the pinned floor — answers `-C <path> worktree status --format json` with the free/running record this step reads. A positional path after `worktree status` is a different shape that no other call site uses and that no floor capability records; it belongs to no version this repository has established.

Advance only when `status` is `free` and `status --porcelain` prints nothing. A `running` status skips with `reason=held-by-live-session` naming the reported session; any porcelain output skips with `reason=uncommitted-work`, because a fast-forward would carry those changes onto a different commit. `--ff-only` advances the branch pointer only when the local branch is already an ancestor of the merged tip, so a checkout carrying its own unmerged commits fails the command and is reported with `reason=not-fast-forwardable`. Every skip leaves that checkout exactly as found and is a reported condition, never a reason to force, reset, stash, or check `main` out anywhere else.

The fast-forward writes outside the assigned worktree, so it surfaces its own approval prompt in a harness that enforces the working-directory boundary, and that prompt names the exact checkout being advanced. Never add a tool grant to suppress it.

Record the checkout's full path and its new full HEAD SHA, or the named skip reason, among the deploy facts the closeout carries.

## Release: refresh persistent plugin installation

The `RELEASE` phase, governed by `RELEASE_READINESS`, runs after `DEPLOY`. Switch the assigned worktree to `origin/main` (detached; never check out `main` anywhere other than the main checkout), then refresh the selected persistent Claude Code project and Codex home from that checkout:

```bash
just install-marketplace
```

The command inspects each agent's installed `outcomeeng` plugins, bounds and orders them through the merged checkout's committed catalog, enforces the canonical GitHub source, and refreshes exactly that set in Claude Code project scope and the selected `CODEX_HOME`. Empty agent state receives only `spec-tree` with a warning; nonempty state without `spec-tree` withholds `RELEASE_READINESS` before mutation. It reconciles the selected plugins' generated Codex definitions into the selected `CODEX_HOME/agents/` registry under the marketplace ownership record: one current owned definition per authored agent of a selected plugin, stale owned definitions pruned only while their recorded digest matches, and every foreign or modified collision preserved and reported. A plugin-owned checkout definition whose invoked skills live in the selected home is a scope-split fault; byte-identical generated copies receive directed-removal guidance, changed or unrecognized copies require inspection, and either class stops the release before mutation. A colliding Claude Code user-scope `outcomeeng` registration likewise withholds `RELEASE_READINESS` before mutation. Preserve the structured first-failure diagnostic when the command fails. After a successful refresh, reload the harness plugin index or start a new session before judging role availability, because a running session retains its already-loaded registry.
