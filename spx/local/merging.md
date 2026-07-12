# Marketplace Merge Rules

Loaded by `/merging-standards` `<repo_local_overlay>` and `/merge`. The product-specific values the merge skills read; the gates, transport selection, and protocols are injected by those skills.

## Deployment and release recognition

No deployment action is declared. Every change proceeds without deployment authorization. Release is declared as the marketplace-source refresh in the release marketplace sync section, governed by `RELEASE_READINESS`; the command owns distribution-change detection. Never ask the operator whether to merge.

## Canonical checkout safety

Run the released default diagnosis before the first merge mutation, without a manifest:

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

Stop before mutation and report the record verbatim when any predicate fails. A missing, detached, wrong-branch, or unreadable designated main checkout therefore blocks the lifecycle, as does an assigned worktree that is itself the designated main checkout. The merge lifecycle never switches, detaches, or performs feature-branch cleanup in the designated main checkout. The release phase may access that checkout only through the explicit `git -C "$src"` fast-forward commands below after the preflight has established its identity and branch standing.

After detach-based feature-worktree cleanup, run `spx diagnose --format json` again and require the same `worktree-pool` health predicates. At that point the assigned feature worktree may be detached, while the designated main checkout must remain readable and attached to the resolved default branch.

## Merge command

Use a merge commit (the product's `main` history style), not the default rebase:

```bash
gh pr merge <pr-number> --merge --delete-branch=false
git push origin --delete <branch>
```

`--delete-branch=false` is explicit because `gh`'s default for the omitted flag is unknowable across environments and its local-cleanup step fails in this multi-worktree checkout; the separate `git push origin --delete` removes the remote branch deterministically.

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

The Claude marketplace is registered as a **Directory source** at the authoritative default-branch worktree — the checkout named like the remote (for example `~/Code/outcomeeng/plugins/plugins`), which stays on branch `main`. That worktree's `dist/` is what every Claude session and `claude plugin marketplace update` reads, so the marketplace serves current content only when **that worktree's `main` is current**.

After a merge lands on `origin/main`, fast-forward the **marketplace-source worktree's** `main`, then refresh installs:

```bash
src=$(just marketplace-source-root outcomeeng)
git -C "$src" fetch origin main
git -C "$src" merge --ff-only origin/main   # the source worktree is on main; fast-forward it to the merged tip
(cd "$src" && just sync-marketplace <previous-main-ref>)   # run FROM the source worktree
```

`just sync-marketplace` must run from the source worktree: its `validate_install` reads `current_versions` from its own working directory, so a feature worktree behind `origin/main` false-fails against stale versions. A PR that changes no plugin-distribution files leaves `dist/` unchanged, so the refresh is skipped, but the source `main` is still fast-forwarded so it never drifts. If `merge --ff-only` fails, the source worktree carries unexpected local commits — move them onto a feature branch (never `reset --hard`), then re-run.

After the canonical-checkout preflight proves that the assigned worktree is a distinct feature worktree, that feature worktree detaches onto the merged commit and never attaches `main` (which lives only in the source worktree):

```bash
git switch --detach origin/main
spx diagnose --format json
```

Inspect the post-cleanup `worktree-pool` record under the canonical checkout safety predicates above before completing `CLOSE`.
