# Marketplace Merge Rules

Loaded by `/standardizing-merging` `<repo_local_overlay>` when working in this repository, and by `/merge` for transport selection. Marketplace-specific overrides to the base merge flow.

## Transport selection

This repository uses the **GitHub-PR transport** by default — feature work, spec/decision/implementation/test/doc changes, and anything that needs review all ship as a pull request through `/github-pr`.

A **coordination-note-only changeset** — every changed path is a `PLAN.md` or `ISSUES.md` — routes to the **direct-push transport** automatically, per `/merge`'s classification and the marketplace guidance that node-local coordination files may be committed directly so collaborators see the coordination state immediately. There is no explicit `transport:` override; the changeset heuristic governs.

The sections below split into the per-transport blocks `/merge` and the lifecycle skills consume: **Production-relevance recognition**, **Merge command**, **Deterministic verification**, and **Mention-reviewer trigger phrase** configure the GitHub-PR transport; **Direct-push transport** configures the direct-push path; **Post-merge** applies to both.

## Production-relevance recognition

This repository declares **no** production-relevance recognition mechanism: every change is treated as not production-relevant, so `PRODUCTION_READINESS` holds by default and `MERGE_READINESS` holding is sufficient authority to merge autonomously. The marketplace ships methodology and plugin sources; a merge to `main` publishes the next marketplace version, which the post-merge sync step picks up — no per-PR human merge approval is required.

The agent merges the moment `MERGE_READINESS` holds and **NEVER asks the operator whether to merge, for merge approval, or whether to hold for human review** — there is no merge-approval decision for the operator to make in this repository, so surfacing one (through the runtime's structured-question tool or in prose) violates this overlay. The only operator-facing pauses in the whole flow are the explicit `<action_tokens>` an unresolved condition emits — an unresolvable rebase conflict (`SYNC_BASE`) or a mention-review edge case (`MENTION_REVIEW_NEEDED`) — never a discretionary "should I merge?".

## Merge command

Use a merge commit (preserves PR history; matches existing main):

```bash
gh pr merge <pr-number> --merge --delete-branch=false
git push origin --delete <branch>
gh pr view <pr-number> --json state,mergedAt,mergeCommit
```

`--delete-branch=false` is passed explicitly rather than omitted: omitting the flag relies on `gh`'s default for it, which varies by `gh` version and config and is unknowable across environments, and a host whose default is on (or whose repository auto-deletes head branches) makes `gh` run its local-cleanup phase, which fails under multi-worktree checkouts when `main` is already checked out in another worktree (the merge succeeds on the remote, but the post-merge `git checkout main` step errors with `fatal: 'main' is already used by worktree at '<path>'`). `=false` guarantees `gh` never attempts that step. Delete the remote branch separately with `git push origin --delete <branch>` (tolerating a host that already auto-deleted it), then verify with `gh pr view`.

## Deterministic verification

The marketplace's full deterministic-verification command is `just check`. It is the `REVIEW_READINESS` deterministic-verification predicate of `/standardizing-merging` `<authority_gates>`: run it (green) before opening the PR, and re-run it before any follow-up push and before any `--force-with-lease` push that follows a base-sync rebase.

## Mention-reviewer trigger phrase

`@spec-tree` (the value `.github/workflows/spec-tree-review.yml` configures via `trigger_phrase`, with `SPEC_TREE_REVIEW_TRIGGER_PHRASE` as the repository-variable override). The managing flow posts `@spec-tree review` as a PR-level comment when the `spec-tree-review / spec-tree-review` workflow reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate), per `/standardizing-merging` `<authority_gates>` reviewer-skipped-by-design exception. Any other skip cause (path filter, branch filter, manual skip) emits `WAIT_FOR_REVIEW` and does not post the trigger phrase.

## Direct-push transport

A coordination-note-only changeset publishes straight to `main` with no pull request, per `/merge`'s transport classification and `spx/21-spec-tree.enabler/76-merging.enabler/32-direct-push.enabler/direct-push.md`. The three gates are unchanged; only the predicate bindings differ.

**Deterministic verification.** A coordination-note-only changeset touches only Markdown coordination notes, so the spec lane is sufficient: `spx validation markdown` and `spx spec status --format json` (per the [AGENTS.md spec-only validation rule](../../AGENTS.md)). The full `just check` is not required when no implementation, test, validation config, or generated catalog file changed.

**Review predicate.** No CI review exists on this path. The local `changes-reviewer` review (converged at `REVIEW_READINESS`) is the `MERGE_READINESS` review predicate. `PRODUCTION_READINESS` holds — this repository declares no production-relevance mechanism (above).

**Push command.** Once `REVIEW_READINESS` holds (spec-lane verification green and the local review converged), publish to trunk with the explicit destination ref:

```bash
git push origin HEAD:refs/heads/main
```

The agent never opens a PR and never waits on CI for this transport. Post-merge follows the section below; a coordination-note-only change touches no plugin distribution files, so `just sync-marketplace` exits without refreshing.

## Post-merge

The Claude marketplace is registered as a **Directory source** at the authoritative default-branch worktree — the checkout named like the remote (for example `~/Code/outcomeeng/plugins/plugins`), which stays on branch `main`. `claude plugin marketplace list --json` reports it as `{"name": "outcomeeng", "source": "directory", "path": "<worktree>"}`. That worktree's `dist/` is what every Claude session and `claude plugin marketplace update` reads, so the marketplace serves current plugin content only when **that worktree's `main` is current** — not when some other worktree's HEAD is.

After a merge lands on `origin/main`, fast-forward the **marketplace-source worktree's** `main`, then refresh installs:

```bash
src=$(claude plugin marketplace list --json | python3 -c 'import json,sys; print(next((e["path"] for e in json.load(sys.stdin) if e.get("name")=="outcomeeng" and e.get("source")=="directory"), ""))')
[ -n "$src" ] || { echo "outcomeeng is not registered as a directory source" >&2; exit 1; }
git -C "$src" fetch origin main
git -C "$src" merge --ff-only origin/main   # the source worktree is on main; fast-forward it to the merged tip
just sync-marketplace <previous-main-ref>    # re-indexes the now-current source and re-validates installs
```

Advancing the source worktree's `main` is the step that makes the merged `dist/` visible to the marketplace. Running `just sync-marketplace` against a source still behind `origin/main` re-indexes stale content — the failure mode this procedure exists to prevent. A PR that changes no plugin-distribution files leaves `dist/` unchanged, so `sync-marketplace` skips the install refresh, but the source worktree's `main` is still fast-forwarded so it never drifts behind.

If `git -C "$src" merge --ff-only origin/main` exits non-zero, the source worktree has diverged from `origin/main` — it should carry no local commits or uncommitted changes, since feature work belongs in other worktrees. Inspect with `git -C "$src" status` and `git -C "$src" log --oneline origin/main..HEAD`, move any unexpected local commits onto a feature branch (never discard them with `reset --hard`), then re-run the fast-forward before `just sync-marketplace`.

The **current (feature) worktree** — where the `/pr` flow ran — is a different checkout. Detach it onto the merged commit so it is not left on the deleted branch, and never attach `main`:

```bash
git switch --detach origin/main
```

`main` is checked out in exactly one place: the marketplace-source worktree, kept current by the fast-forward above. Every other worktree detaches and never attaches `main`, so `git switch main` in a feature worktree — which fails with `fatal: 'main' is already used by worktree at <path>` — never happens, and the source worktree never contends with feature work. Keep feature work out of the source worktree so its `main` stays fast-forwardable. This overlay is the authoritative source for the multi-worktree post-merge rationale; the [AGENTS.md sync step](../../AGENTS.md) mirrors it.
