# Marketplace Merge Rules

Loaded by `/merging-standards` `<repo_local_overlay>` when working in this repository, and by `/merge` for transport selection. Marketplace-specific overrides to the base merge flow.

## Transport selection

This repository uses the **GitHub-PR transport** by default — feature work, spec/decision/implementation/test/doc changes, and anything that needs review all ship as a pull request through `/manage-github-pr`.

A **coordination-note-only changeset** — every changed path is a `PLAN.md` or `ISSUES.md` — routes to the **direct-push transport** automatically, per `/merge`'s classification and the marketplace guidance that node-local coordination files may be committed directly so collaborators see the coordination state immediately. There is no explicit `transport:` override; the changeset heuristic governs.

The sections below split into the per-transport blocks `/merge` and the lifecycle skills consume: **Production-relevance recognition**, **Merge command**, **Deterministic verification**, and **Mention-reviewer trigger phrase** configure the GitHub-PR transport; **Direct-push transport** configures the direct-push path; **Pre-mutation confirmation** and **Post-merge** apply to both.

## Production-relevance recognition

This repository declares **no** production-relevance recognition mechanism: every change is treated as not production-relevant, so `PRODUCTION_READINESS` holds by default and `MERGE_READINESS` holding is sufficient authority to merge autonomously. The marketplace ships methodology and plugin sources; a merge to `main` publishes the next marketplace version, which the post-merge sync step picks up — no per-PR human merge approval is required.

Merge the moment `MERGE_READINESS` holds and **NEVER ask the operator whether to merge, for merge approval, or whether to hold for human review** — there is no merge-approval decision for the operator to make in this repository, so surfacing one (through the runtime's structured-question tool or in prose) violates this overlay. The only operator-facing pauses in the whole flow are the explicit `<action_tokens>` an unresolved condition emits — an unresolvable rebase conflict (`SYNC_BASE`) or a mention-review edge case (`MENTION_REVIEW_NEEDED`) — never a discretionary "should I merge?".

## Pre-mutation confirmation

This repository declares **no** pre-mutation confirmation: drive a determined changeset from intent to merge autonomously, stating the plan in prose with no up-front structured-question pause before branching, committing, pushing, opening a PR, or direct-pushing. This matches the standing autonomy in [`AGENTS.md`](../../AGENTS.md) Git workflow → Autonomy — the operator has pre-authorized the whole lifecycle, so an up-front proposal-and-confirm pause would re-ask a decision the operator has already made.

Establishing *what* to ship when nothing is determined (the `/manage-github-pr` Empty-mode `/interview` pass) is requirements work, not a pre-mutation confirmation, and proceeds regardless. The only operator-facing pauses in the whole flow are the explicit `<action_tokens>` an unresolved condition emits — an unresolvable rebase conflict (`SYNC_BASE`) or a mention-review edge case (`MENTION_REVIEW_NEEDED`) — never a discretionary "should I proceed?".

## Merge command

Use a merge commit (preserves PR history; matches existing main):

```bash
gh pr merge <pr-number> --merge --delete-branch=false
git push origin --delete <branch>
gh pr view <pr-number> --json state,mergedAt,mergeCommit
```

`--delete-branch=false` is passed explicitly rather than omitted: omitting the flag relies on `gh`'s default for it, which varies by `gh` version and config and is unknowable across environments, and a host whose default is on (or whose repository auto-deletes head branches) makes `gh` run its local-cleanup phase, which fails under multi-worktree checkouts when `main` is already checked out in another worktree (the merge succeeds on the remote, but the post-merge `git checkout main` step errors with `fatal: 'main' is already used by worktree at '<path>'`). `=false` guarantees `gh` never attempts that step. Delete the remote branch separately with `git push origin --delete <branch>` (tolerating a host that already auto-deleted it), then verify with `gh pr view`.

## Deterministic verification

The marketplace's local deterministic-verification predicate is changeset-scoped. Run the narrow validation and testing lane that covers the files touched by the diff, and reserve local full-repository `just check` for changes that alter shared validation/test infrastructure, package manager files, generated catalog output, distribution build machinery, or broad implementation surfaces whose touched-scope commands cannot cover the contract.

For Markdown-only skill/spec/doc changes, use the documented narrow lane: `just check-skills` and `just docs-check` for skill content, or `spx validation markdown` and `spx spec status --format json` for spec-only changes. For changed implementation or test files, run the focused node/package/module tests plus the narrow validation commands that cover those files.

CI owns the full-repository deterministic regression pass. A passing local touched-scope run is the `REVIEW_READINESS` deterministic predicate; the PR checks then run the full repository gate on the hosted surface. Capture verbose command output to `$TMPDIR` and inspect only the exit status, summary, and failing sections unless a failure requires the retained log.

## Base-sync readiness preservation

After a clean rebase, `/sync-base` returns a readiness-preservation proof (`preservation` in its JSON: full before/after OIDs, `base_delta_paths`, `branch_paths_after`, `path_overlap`, `branch_patch_changed`, `branch_diff_unchanged`). This overlay maps those git facts to the marketplace's verification lanes and governance surfaces; `/merging-standards` `<base_sync>` and `/manage-pr` consume the mapping. The proof scopes pre-push local verification only — current-head PR checks and the current-head CI review remain required for `MERGE_READINESS`.

**Governance surfaces.** A prior local review is reusable across a rebase only when `branch_diff_unchanged` is true **and** no `base_delta_paths` entry is a governance surface — a file the `changes-reviewer` judges against: `AGENTS.md`, `CLAUDE.md`, `REVIEW.template.md`, any `spx/local/*.md`, or any standards reference under `src/plugins/*/skills/*-standards/` and `src/plugins/*/skills/**/SKILL.md`. When the base delta touches any of these, re-run the local review even if the branch patch is unchanged.

**Validation lane.** Choose the narrowest lane that covers every `base_delta_paths` entry:

- All entries under `spx/` or matching `*.md` (specs, decisions, coordination notes, docs), and `path_overlap` empty → the spec/markdown lane: `spx validation markdown` and `spx spec status --format json`.
- Any entry under `src/plugins/` or `dist/` that is only skill Markdown/reference content, and `path_overlap` empty → the skill/doc lane: `just check-skills` and `just docs-check`.
- Any entry under `src/`, `outcomeeng*/`, `.github/`, a package or lockfile, `justfile`/`Justfile`, or validation config; any entry this overlay does not classify; `path_overlap` non-empty; or `branch_patch_changed` true → widen to the focused node/package/module test lane plus the narrow validation lane that covers the changed files, reserving full `just check` for the escalation cases above.

When in doubt, widen the local lane only as far as the changed contract requires — the narrower lane is an optimization, never a relaxation of `REVIEW_READINESS`.

## Mention-reviewer trigger phrase

`@spec-tree` (the value `.github/workflows/spec-tree-review.yml` configures via `trigger_phrase`, with `SPEC_TREE_REVIEW_TRIGGER_PHRASE` as the repository-variable override). The managing flow posts `@spec-tree review` as a PR-level comment when the `spec-tree-review / spec-tree-review` workflow reports `conclusion: skipped` because the PR modifies the reviewer's own workflow file (GitHub Actions' identical-workflow-content gate), per `/merging-standards` `<authority_gates>` reviewer-skipped-by-design exception. Any other skip cause (path filter, branch filter, manual skip) emits `WAIT_FOR_REVIEW` and does not post the trigger phrase.

## Direct-push transport

A coordination-note-only changeset publishes straight to `main` with no pull request, per `/merge`'s transport classification and `spx/21-spec-tree.enabler/76-merging.enabler/32-direct-push.enabler/direct-push.md`. The three gates are unchanged; only the predicate bindings differ.

**Deterministic verification.** A coordination-note-only changeset touches only Markdown coordination notes, so the spec lane is sufficient: `spx validation markdown` and `spx spec status --format json` (per the [AGENTS.md spec-only validation rule](../../AGENTS.md)). The full `just check` is not required when no implementation, test, validation config, or generated catalog file changed.

**Review predicate.** No CI review exists on this path. The local `changes-reviewer` review (converged at `REVIEW_READINESS`) is the `MERGE_READINESS` review predicate. `PRODUCTION_READINESS` holds — this repository declares no production-relevance mechanism (above).

**Push command.** Once `REVIEW_READINESS` holds (spec-lane verification green and the local review converged), publish to the default branch on origin (`main` in this repository) with the explicit destination ref:

```bash
git push origin HEAD:refs/heads/main
```

For this transport, never open a PR and never wait on CI. Post-merge follows the section below; a coordination-note-only change touches no plugin distribution files, so `just sync-marketplace` exits without refreshing.

## Post-merge

The Claude marketplace is registered as a **Directory source** at the authoritative default-branch worktree — the checkout named like the remote (for example `~/Code/outcomeeng/plugins/plugins`), which stays on branch `main`. `claude plugin marketplace list --json` reports it as `{"name": "outcomeeng", "source": "directory", "path": "<worktree>"}`. That worktree's `dist/` is what every Claude session and `claude plugin marketplace update` reads, so the marketplace serves current plugin content only when **that worktree's `main` is current** — not when some other worktree's HEAD is.

After a merge lands on `origin/main`, fast-forward the **marketplace-source worktree's** `main`, then refresh installs:

```bash
src=$(claude plugin marketplace list --json | python3 -c 'import json,sys; print(next((e["path"] for e in json.load(sys.stdin) if e.get("name")=="outcomeeng" and e.get("source")=="directory"), ""))')
[ -n "$src" ] || { echo "outcomeeng is not registered as a directory source" >&2; exit 1; }
git -C "$src" fetch origin main
git -C "$src" merge --ff-only origin/main   # the source worktree is on main; fast-forward it to the merged tip
(cd "$src" && just sync-marketplace <previous-main-ref>)   # run FROM the source worktree; see below
```

Advancing the source worktree's `main` is the step that makes the merged `dist/` visible to the marketplace. Running `just sync-marketplace` against a source still behind `origin/main` re-indexes stale content — the failure mode this procedure exists to prevent. A PR that changes no plugin-distribution files leaves `dist/` unchanged, so `sync-marketplace` skips the install refresh, but the source worktree's `main` is still fast-forwarded so it never drifts behind.

Run `just sync-marketplace` from the source worktree (`cd "$src"` first), not from the feature worktree the change was prepared in. The sync step reconciles Claude and Codex `outcomeeng` registrations to the default-branch local marketplace source, refreshes every generated Codex plugin exposed under `dist/codex` with `codex plugin add <plugin>@outcomeeng`, repairs compatibility symlinks, installs generated agents, and then validates the install state. Its `validate_install` reads `current_versions` from its own working directory: invoked from a feature worktree that is behind `origin/main`, it checks the cache against that worktree's stale manifest versions and reports false `MISSING` errors for plugins the cache already holds at the newer published version. Invoked from the fast-forwarded source worktree, it validates against the current versions the cache actually carries.

If `git -C "$src" merge --ff-only origin/main` exits non-zero, the source worktree has diverged from `origin/main` — it should carry no local commits or uncommitted changes, since feature work belongs in other worktrees. Inspect with `git -C "$src" status` and `git -C "$src" log --oneline origin/main..HEAD`, move any unexpected local commits onto a feature branch (never discard them with `reset --hard`), then re-run the fast-forward before `(cd "$src" && just sync-marketplace <previous-main-ref>)`.

The **current (feature) worktree** — where the change was prepared — is a different checkout. Detach it onto the merged commit so it is not left on the deleted branch, and never attach `main`:

```bash
git switch --detach origin/main
```

`main` is checked out in exactly one place: the marketplace-source worktree, kept current by the fast-forward above. Every other worktree detaches and never attaches `main`, so `git switch main` in a feature worktree — which fails with `fatal: 'main' is already used by worktree at <path>` — never happens, and the source worktree never contends with feature work. Keep feature work out of the source worktree so its `main` stays fast-forwardable. This overlay is the authoritative source for the multi-worktree post-merge rationale; the [AGENTS.md sync step](../../AGENTS.md) mirrors it.
