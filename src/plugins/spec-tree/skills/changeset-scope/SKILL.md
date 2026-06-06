---
name: changeset-scope
description: ALWAYS invoke this skill when deriving a changeset's base ref, branch slug, branch identity, or merge-base diff scope from git. NEVER re-implement branch-slug or base-ref derivation inside another skill's scripts.
allowed-tools: Bash, Read
---

<objective>
Provide the single canonical home for the deterministic git-derived changeset primitives shared across the agentic verification surfaces — auditing, reviewing-changes, and thread-store. Branch identity, the on-disk addressing slug, base-ref resolution, the remote-tracking ref form, and merge-base diff scope are derived here once; consumers import them rather than re-deriving or re-exporting them.
</objective>

<api_surface>

The derivation lives in `${CLAUDE_SKILL_DIR}/scripts/changeset_scope.py`, imported by sibling skills' scripts through the marketplace skill-co-located importlib convention (no path is hardcoded in agent prose).

| Symbol                          | Purpose                                                                                  |
| ------------------------------- | ---------------------------------------------------------------------------------------- |
| `branch_slug(name, state_dir)`  | Path-safe, length-bounded, deterministic on-disk slug for a branch name                  |
| `detect_current_branch(repo)`   | Current branch name; raises `DetachedHeadError` on detached HEAD                         |
| `detect_base_ref(repo, strict)` | Bare base-branch name from `origin/HEAD`; strict raises `BaseRefNotConfiguredError`      |
| `remote_tracking_ref(base)`     | The remote-tracking ref `origin/<base>` — the single source of the `origin/` composition |
| `branch_scope(base, repo)`      | Files changed on this branch relative to `origin/<base>` (three-dot, merge-base)         |
| `expand_diff_range(spec, repo)` | Files changed in an arbitrary git diff range                                             |

</api_surface>

<scoping_invariant>

Every changeset diff range over a git-derived base is composed against the remote-tracking ref `origin/<base>` through `remote_tracking_ref` — `branch_scope` for the auditing surface and `compute_diff` for the reviewing surface. A bare local branch ref can lag `origin/<base>` in a multi-worktree checkout; scoping against the remote-tracking ref keeps the merge base at the true branch point so already-merged commits do not re-enter the scope.

</scoping_invariant>

<success_criteria>

- The base ref, branch slug, branch identity, and diff scope come from `changeset_scope.py` — no consumer re-implements them.
- Git-derived diff ranges are composed against `origin/<base>` via `remote_tracking_ref`, never a bare local branch ref.
- The module imports only the Python standard library.

</success_criteria>
