# Marketplace Merge Rules

Loaded by `/merging-standards` `<repo_local_overlay>` and `/merge`. The product-specific values the merge skills read; the gates, transport selection, and protocols are injected by those skills.

## Deployment and release recognition

No deployment action is declared. No release action is declared: a merge to the default branch on origin is itself the publication, as the release marketplace sync section states. Every change proceeds without deployment or release authorization, and both phases are no-ops that never block `CLOSE`. Never ask the operator whether to merge.

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

Stop before mutation and report the record verbatim when any predicate fails. A missing, detached, wrong-branch, or unreadable designated main checkout therefore blocks the lifecycle, as does an assigned worktree that is itself the designated main checkout. The merge lifecycle never switches, detaches, or performs feature-branch cleanup in the designated main checkout.

The preflight reads worktree-pool health only. Plugin delivery is the checkout's own committed agent-harness configuration, so no predicate here reads a marketplace registration, a plugin cache, or any path outside the pool.

After detach-based feature-worktree cleanup, run `spx diagnose --format json` again and require the same `worktree-pool` health predicates. At that point the assigned feature worktree may be detached, while the designated main checkout must remain readable and attached to the resolved default branch.

## Merge command

Use a merge commit (the product's `main` history style), not the default rebase:

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

Stop and inspect the post-cleanup `worktree-pool` record and the worktree-root output under the canonical checkout safety predicates. A failed check leaves the feature worktree detached and the remote branch intact for inspection. Only after every predicate passes, run:

```bash
git push origin --delete <branch>
```

## Deterministic verification commands

The touched-scope principle is `/merging-standards` `<local_deterministic_scope>`; these are this repository's commands per scope:

- Spec-only (specs, decisions, coordination notes, Markdown): `spx validation markdown` and `spx spec status --format json`.
- Skill/doc Markdown under `src/plugins/` or `dist/`: `just check-skills` and `just docs-check`.
- Implementation, test, validation-config, or broad changes: the focused node/package/module tests plus the narrow validation lane that covers the changed files, widening to full `just check-full` for shared validation/test infrastructure, package-manager files, generated catalog output, or distribution build machinery.

When the full `just check-full` bundle is required, it is the terminal local deterministic gate. Run the focused lane first, then all applicable evidence auditors and agentic reviews to convergence, then run `just check-full` once against the clean committed head. Never run `just check-full` before those agentic checks, inside an agent, or concurrently with another heavy command. Any change after it invalidates the result and reopens the affected agentic gates before the next full-gate run.

## Governance surfaces (base-sync review reuse)

A prior local review is reusable across a clean rebase only when the branch patch is unchanged **and** no base-delta path is a governance surface: `AGENTS.md`, `CLAUDE.md`, any `spx/local/*.md`, the bundled review prompt at `src/plugins/spec-tree/skills/review-changes/references/review-prompt.md`, or any standards reference under `src/plugins/*/skills/*-standards/` or `src/plugins/*/skills/**/SKILL.md`.

## Mention-reviewer trigger phrase

`@spec-tree` (configured in `.github/workflows/spec-tree-review.yml` `trigger_phrase`; repository-variable override `SPEC_TREE_REVIEW_TRIGGER_PHRASE`).

## Release marketplace sync

Plugin delivery is the checkout's own committed agent-harness configuration, per `spx/12-marketplace-state.adr.md`. `.claude/settings.json` declares the `outcomeeng` marketplace and the enabled plugin set for Claude Code, and `.agents/plugins/marketplace.json` with `.codex/config.toml` declares them for Codex. A session resolves its plugins from that committed declaration, so landing a change on `origin/main` publishes it.

The merge lifecycle therefore performs no release action. It fast-forwards no worktree, reconciles no marketplace registration, and refreshes no plugin cache — every one of those is user-scope state the toolchain never reaches into. `RELEASE` is a no-op phase and never blocks `CLOSE`.

Picking up newly published plugin versions is a developer's own operation, outside this lifecycle. Registering a local Directory source at a single worktree is a preview affordance for inspecting that worktree's uncommitted plugin changes; it is never a delivery path, and no gate in this overlay reads one.
