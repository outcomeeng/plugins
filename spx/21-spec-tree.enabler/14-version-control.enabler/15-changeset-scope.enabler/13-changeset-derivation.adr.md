# Changeset Derivation Home and Remote-Ref Scoping

The git-derived changeset primitives — `branch_slug`, `detect_current_branch`, `detect_base_ref`, `commit_oid`, `branch_scope`, `expand_diff_range`, `remote_tracking_ref` — are defined once in `plugins/spec-tree/skills/scope-changeset/scripts/changeset_scope.py` and reached by the audit, review-changes, manage-thread-store, and sync-base skills through import or re-export, never re-definition. Every changeset diff range over a git-derived base is composed against the remote-tracking ref `origin/<base>` (three-dot, merge-base) through the single `remote_tracking_ref` helper, never a bare local branch ref — `branch_scope` composes it for the audit surface and `compute_diff` for the review surface. Journal run-state identity uses `commit_oid` to stamp concrete head/base commit IDs rather than symbolic refs.

## Rationale

The agentic-verification surfaces — audit, review-changes, and manage-thread-store — derive branch identity and diff scope from git, and base synchronization derives the base ref from the same primitives. Housing that derivation inside one verification consumer forces a re-export shim in manage-thread-store to carry the slug rule across skills and leaves review-changes reaching two skills away for `detect_base_ref`. A single shared home removes the cross-skill reach; the migration trigger for a helper co-located with one consumer is met when review-changes consumes the derivation.

Scoping against the remote-tracking ref rather than a bare local branch ref keeps the changeset independent of local-ref staleness. A bare local ref such as `main` lags `origin/<base>` in a multi-worktree checkout where the local branch is left unattached. The three-dot diff recomputes its merge base from whichever ref it is given; against a stale local ref the merge base falls at an older divergence point, so commits already merged into the base re-enter the diff and surface as findings against work outside the changeset. Composing against the fetched remote-tracking ref fixes the merge base at the true branch point.

Rejected: keeping the derivation in the audit skill with re-exports — it leaves a primitive shared by multiple skills owned by one of them and keeps the cross-skill `importlib` reach the consolidation removes.

## Verification

### Testing

- ALWAYS: every git-derived diff range is composed against the remote-tracking ref `origin/<base>` via `remote_tracking_ref` — `branch_scope` for the audit surface, `compute_diff` for the review surface — so a stale local branch ref does not widen the scope ([scenario])

### Audit

- ALWAYS: the changeset-derivation primitives are defined once in the changeset-scope skill's `scripts/changeset_scope.py`; the audit, review-changes, manage-thread-store, and sync-base skills reach them only by import or re-export ([audit])
- ALWAYS: the `branch_slug` re-export at `plugins/spec-tree/skills/manage-thread-store/scripts/branch_slug.py` resolves the symbol from the changeset-scope module and is identity-equal to the canonical definition ([audit])
- NEVER: a consumer skill re-implements a changeset-derivation primitive in its own `scripts/` ([audit])
