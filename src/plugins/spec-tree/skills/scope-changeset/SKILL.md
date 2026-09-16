---
name: scope-changeset
user-invocable: false
description: >-
  Committed changeset endpoint identities and changed paths, resolved through
  the canonical Git scope capability.
argument-hint: "[HEAD|branch|base...head]"
allowed-tools: Read, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/changeset_scope.py":*)
---

<objective>
A committed changeset's full endpoint identities and changed paths, with a canonical Python API for Git derivation.
</objective>

<invocation>

When `$ARGUMENTS` is empty, load the API reference below without executing a command or emitting a scope marker. Script consumers import the provider.

When a selector is supplied, resolve it through this skill's own command:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/changeset_scope.py" "<selector>"
```

Pass the supplied selector as one literal argument. For a git-derived or `origin/` base the command fetches the base's remote-tracking ref, reads the current checkout, and emits one JSON object with `base`, `head`, and `changed_paths`; an explicit range whose base names a local ref or a commit is compared as given, with no fetch and no refusal. Exit status 3 (`EXIT_STALE_BASE`) is the stale-base refusal: the head does not descend from the fetched `origin/<base>` tip, stdout carries no scope, and stderr carries one JSON diagnostic with `status` `stale-base`, `tip`, `merge_base`, and `behind`. Report it as a `stale-base` block and emit no marker; a scope computed against an older base is never a substitute. Any other nonzero exit or malformed result is `blocked`: preserve its diagnostic and emit no marker. Never fabricate a base, endpoint identity, or path set.

After a successful command, emit `<COMMITTED_CHANGESET_SCOPE>` with the supplied selector, absolute checkout root, and all three returned fields verbatim. The invoking workflow consumes this marker without re-executing the derivation. The marker applies only to that checkout and selector at the recorded full head; discard it when the subject changes. The command fetches the base's remote-tracking ref and never rebases, commits, or modifies the working tree.

</invocation>

<api_surface>

The derivation lives in `${CLAUDE_SKILL_DIR}/scripts/changeset_scope.py`, imported by sibling skills' scripts through the marketplace skill-co-located importlib convention (no path is hardcoded in agent prose).

| Symbol                                              | Purpose                                                                                                                                                                                     |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `branch_slug(name, state_dir)`                      | Path-safe, length-bounded, deterministic on-disk slug for a branch name                                                                                                                     |
| `detect_current_branch(repo)`                       | Current branch name; raises `DetachedHeadError` on detached HEAD                                                                                                                            |
| `detect_base_ref(repo)`                             | Bare base-branch name from `origin/HEAD`; raises `BaseRefNotConfiguredError` when absent                                                                                                    |
| `commit_oid(ref, *, repo)`                          | Full commit object ID for a ref, rejecting non-commit objects                                                                                                                               |
| `remote_tracking_ref(base)`                         | The remote-tracking ref `origin/{base}` — the single source of the `origin/` composition                                                                                                    |
| `branch_scope(base, *, repo)`                       | Files changed on this branch relative to `origin/{base}` (three-dot, merge-base)                                                                                                            |
| `expand_diff_range(spec, repo)`                     | Files changed in an arbitrary git diff range                                                                                                                                                |
| `require_current_base(base_ref, head_ref, *, repo)` | Fetches a remote-tracking base and raises `StaleBaseError` when the head does not descend from its tip                                                                                      |
| `resolve_committed_scope(selector, *, repo)`        | Full endpoint identities and merge-base changed paths for `HEAD`, a branch, or an explicit three-dot range, refused through `require_current_base` when the head is behind the fetched base |

</api_surface>

<selector_resolution>

`resolve_committed_scope` returns `base`, `head`, and `changed_paths`. A single
ref uses the configured remote base; an explicit range preserves both supplied
endpoints. `base` identifies the selected base endpoint, while `changed_paths`
uses Git's three-dot merge-base semantics. Do not treat that endpoint as the
merge-base commit when constructing a two-dot diff. Every composed Git call
receives the supplied `Runner`; missing base configuration, malformed ranges,
and Git execution failures raise `ScopeResolutionError` without changing the
checkout. Invalid repository paths retain the path and operating-system error
in that diagnostic. `ScopeField` owns the returned JSON field names.

For a git-derived or `origin/` base the base identity is the fetched
`origin/<base>` tip, never the merge base. `require_current_base` fetches that
ref, then refuses a head whose merge base with the tip is not the tip itself
by raising `StaleBaseError`; a local-ref or commit base in an explicit range
is the caller's exact endpoint, compared as given with no fetch and no
refusal, so exit status 3 arises only for a git-derived or `origin/` base. The CLI maps
it to `EXIT_STALE_BASE` (exit status 3) and prints
`StaleBaseError.diagnostic()` — the `StaleBaseField` names `status`
(`STALE_BASE_STATUS`), `tip`, `merge_base`, and `behind` — on stderr in place
of a scope. `detect_base_ref`, `remote_tracking_ref`, and `branch_scope` carry
no refusal, so an importer that partitions or synchronizes rather than
verifies composes them directly.

The focused scope suites exercise stale local bases, explicit ranges, a branch
other than the checked-out branch, concrete endpoint identities, malformed
ranges, absent remote-base configuration, a nonexistent `--repo` path, a head
behind the fetched base, a lagging local remote-tracking ref the fetch
corrects, a symbolic `origin/HEAD` range base, an explicit local-ref range
base both lagging the remote and ahead of the head, and a current head
through the shipped resolver CLI.

</selector_resolution>

<scoping_invariant>

Every changeset diff range over a git-derived base is composed against the remote-tracking ref `origin/{base}` through `remote_tracking_ref`. Shared branch-scope consumers call `branch_scope`; consumers with their own diff operation import `remote_tracking_ref` before composing that range. A bare local branch ref can lag `origin/{base}` in a multi-worktree checkout; scoping against the remote-tracking ref keeps the merge base at the true branch point so already-merged commits do not re-enter the scope.

</scoping_invariant>

<success_criteria>

- A `<COMMITTED_CHANGESET_SCOPE>` marker exists exactly when the command exited 0, and its `base`, `head`, and `changed_paths` are byte-equal to the command's JSON.
- Exit status 3 leaves no marker and a `stale-base` diagnostic on stderr whose `tip` is the fetched `origin/<base>` commit; any other nonzero exit leaves no marker and its diagnostic preserved.
- The base ref, branch slug, branch identity, concrete commit OID, and diff scope come from `changeset_scope.py`.
- Git-derived diff ranges are composed against `origin/{base}` via `remote_tracking_ref`, never a bare local branch ref.
- The module imports only the Python standard library.

</success_criteria>
