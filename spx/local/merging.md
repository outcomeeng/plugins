# Marketplace Merge Rules

Loaded by `/merging-standards` `<repo_local_overlay>` and `/merge`. The product-specific values the merge skills read; the gates, transport selection, and protocols are injected by those skills.

## Production-relevance recognition

None. Every change is treated as not production-relevant, so `PRODUCTION_READINESS` holds and `MERGE_READINESS` alone authorizes the merge — never ask the operator whether to merge.

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
- Implementation, test, validation-config, or broad changes: the focused node/package/module tests plus the narrow validation lane that covers the changed files, widening to full `just check` for shared validation/test infrastructure, package-manager files, generated catalog output, or distribution build machinery.

## Governance surfaces (base-sync review reuse)

A prior local review is reusable across a clean rebase only when the branch patch is unchanged **and** no base-delta path is a governance surface: `AGENTS.md`, `CLAUDE.md`, `REVIEW.template.md`, any `spx/local/*.md`, or any standards reference under `src/plugins/*/skills/*-standards/` or `src/plugins/*/skills/**/SKILL.md`.

## Mention-reviewer trigger phrase

`@spec-tree` (configured in `.github/workflows/spec-tree-review.yml` `trigger_phrase`; repository-variable override `SPEC_TREE_REVIEW_TRIGGER_PHRASE`).

## Post-merge marketplace sync

The Claude marketplace is registered as a **Directory source** at the authoritative default-branch worktree — the checkout named like the remote (for example `~/Code/outcomeeng/plugins/plugins`), which stays on branch `main`. That worktree's `dist/` is what every Claude session and `claude plugin marketplace update` reads, so the marketplace serves current content only when **that worktree's `main` is current**.

After a merge lands on `origin/main`, fast-forward the **marketplace-source worktree's** `main`, then refresh installs. A checkout update alone is incomplete: `git pull`, `git switch`, `git fetch`, or `git merge --ff-only` in the source checkout is only the prerequisite for `just sync-marketplace <previous-main-ref>`.

```bash
src=$(claude plugin marketplace list --json | python3 -c 'import json,sys; print(next((e["path"] for e in json.load(sys.stdin) if e.get("name")=="outcomeeng" and e.get("source")=="directory"), ""))')
[ -n "$src" ] || { echo "outcomeeng is not registered as a directory source" >&2; exit 1; }
git -C "$src" fetch origin main
git -C "$src" merge --ff-only origin/main   # the source worktree is on main; fast-forward it to the merged tip
(cd "$src" && just sync-marketplace <previous-main-ref>)   # run FROM the source worktree
```

`just sync-marketplace` must run from the source worktree: its `validate_install` reads `current_versions` from its own working directory, so a feature worktree behind `origin/main` false-fails against stale versions. A PR that changes no plugin-distribution files leaves `dist/` unchanged, so the refresh is skipped, but the source `main` is still fast-forwarded so it never drifts. If `merge --ff-only` fails, the source worktree carries unexpected local commits — move them onto a feature branch (never `reset --hard`), then re-run.

The feature worktree where the change was prepared detaches onto the merged commit and never attaches `main` (which lives only in the source worktree):

```bash
git switch --detach origin/main
```
