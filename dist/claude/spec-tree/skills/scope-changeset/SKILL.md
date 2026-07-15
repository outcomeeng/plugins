---
name: scope-changeset
user-invocable: false
description: >-
  Canonical git-derived changeset primitives loaded by verification and lifecycle
  skills instead of re-implementing branch, base-ref, commit-identity, slug, or
  diff-scope derivation.
allowed-tools: Read
---

<objective>
The canonical deterministic git-derived changeset primitives — branch identity, on-disk addressing slug, base-ref resolution, concrete commit-OID resolution, remote-tracking ref form, and merge-base diff scope.
</objective>

<api_surface>

The derivation lives in `${CLAUDE_SKILL_DIR}/scripts/changeset_scope.py`, imported by sibling skills' scripts through the marketplace skill-co-located importlib convention (no path is hardcoded in agent prose).

| Symbol                          | Purpose                                                                                  |
| ------------------------------- | ---------------------------------------------------------------------------------------- |
| `branch_slug(name, state_dir)`  | Path-safe, length-bounded, deterministic on-disk slug for a branch name                  |
| `detect_current_branch(repo)`   | Current branch name; raises `DetachedHeadError` on detached HEAD                         |
| `detect_base_ref(repo)`         | Bare base-branch name from `origin/HEAD`; raises `BaseRefNotConfiguredError` when absent |
| `commit_oid(ref, *, repo)`      | Full commit object ID for a ref, rejecting non-commit objects                            |
| `remote_tracking_ref(base)`     | The remote-tracking ref `origin/<base>` — the single source of the `origin/` composition |
| `branch_scope(base, *, repo)`   | Files changed on this branch relative to `origin/<base>` (three-dot, merge-base)         |
| `expand_diff_range(spec, repo)` | Files changed in an arbitrary git diff range                                             |

</api_surface>

<scoping_invariant>

Every changeset diff range over a git-derived base is composed against the remote-tracking ref `origin/<base>` through `remote_tracking_ref`. Shared branch-scope consumers call `branch_scope`; consumers with their own diff operation import `remote_tracking_ref` before composing that range. A bare local branch ref can lag `origin/<base>` in a multi-worktree checkout; scoping against the remote-tracking ref keeps the merge base at the true branch point so already-merged commits do not re-enter the scope.

</scoping_invariant>

<success_criteria>

- The base ref, branch slug, branch identity, concrete commit OID, and diff scope come from `changeset_scope.py` — no consumer re-implements them.
- Git-derived diff ranges are composed against `origin/<base>` via `remote_tracking_ref`, never a bare local branch ref.
- The module imports only the Python standard library.

</success_criteria>
