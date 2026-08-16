# Changeset Derivation Home and Remote-Ref Scoping

The git-derived changeset primitives — `branch_slug`, `detect_current_branch`, `detect_base_ref`, `commit_oid`, `branch_scope`, `expand_diff_range`, `remote_tracking_ref` — are defined once in `src/plugins/spec-tree/skills/changeset-scope-standards/scripts/changeset_scope.py` and reached by implementation-audit orchestration, review-changes, and sync-base through import, never re-definition. Every changeset diff range over a git-derived base is composed against the remote-tracking ref `origin/<base>` (three-dot, merge-base) through the single `remote_tracking_ref` helper, never a bare local branch ref — `branch_scope` composes it for the audit surface and `compute_diff` for the review surface. Journal run-state identity uses `commit_oid` to stamp concrete head/base commit IDs rather than symbolic refs.

## Rationale

The agentic-verification surfaces — implementation audit and review-changes — derive branch identity and diff scope from git, and base synchronization derives the base ref from the same primitives. A single shared home prevents either verification consumer from owning or duplicating the common derivation.

Scoping against the remote-tracking ref rather than a bare local branch ref keeps the changeset independent of local-ref staleness. A bare local ref such as `main` lags `origin/<base>` in a multi-worktree checkout where the local branch is left unattached. The three-dot diff recomputes its merge base from whichever ref it is given; against a stale local ref the merge base falls at an older divergence point, so commits already merged into the base re-enter the diff and surface as findings against work outside the changeset. Composing against the fetched remote-tracking ref fixes the merge base at the true branch point.

Rejected: keeping the derivation in the audit skill with re-exports — it leaves a primitive shared by multiple skills owned by one of them and keeps the cross-skill `importlib` reach the consolidation removes.

## Verification

### Audit

- ALWAYS: every git-derived diff range is composed against the remote-tracking ref `origin/<base>` via `remote_tracking_ref` — `branch_scope` for the audit surface, `compute_diff` for the review surface — so a stale local branch ref does not widen the scope ([audit])
- ALWAYS: the changeset-derivation primitives are defined once in the changeset-scope skill's `scripts/changeset_scope.py`; implementation-audit orchestration, review-changes, and sync-base reach them only by import ([audit])
- ALWAYS: each changeset-derivation primitive that invokes git accepts a dependency-injected runner typed by a source-owned protocol, and composed primitives forward that runner through the complete call path ([audit])
- NEVER: a consumer skill re-implements a changeset-derivation primitive in its own `scripts/` ([audit])
- NEVER: tests replace git behavior through framework mocking; runner doubles cross the declared protocol boundary ([audit])
