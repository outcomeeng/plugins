# Changeset Derivation Home and Remote-Ref Scoping

The git-derived changeset primitives — `branch_slug`, `detect_current_branch`, `detect_base_ref`, `commit_oid`, `branch_scope`, `expand_diff_range`, `remote_tracking_ref` — are defined once in `plugins/spec-tree/skills/scope-changeset/scripts/changeset_scope.py` and reached by implementation-audit orchestration, review-changes, and sync-base through import, never re-definition. Every changeset diff range over a git-derived base is composed against the remote-tracking ref `origin/<base>` (three-dot, merge-base) through the single `remote_tracking_ref` helper, never a bare local branch ref — `branch_scope` composes it for the audit surface and `compute_diff` for the review surface. Journal run-state identity uses `commit_oid` to stamp concrete head/base commit IDs rather than symbolic refs — the base identity is the fetched `origin/<base>` tip, never the merge-base commit. A committed selector whose base is git-derived or a remote-tracking ref resolves only against that fetched tip: the resolver fetches the base's remote-tracking ref and refuses a head whose merge base with the tip is not the tip itself, reporting the tip, the merge base, and the base commits the head lacks through a dedicated exit code and a diagnostic in place of a scope. An explicit range whose base names a local ref or a commit is the caller's exact endpoint pair and is compared as given, with no fetch and no refusal. That refusal is every verifier's first step for a git-derived or remote-tracking base: a verification skill that resolves a committed scope returns it as a `stale-base` block before it opens a run or reads a subject. Base synchronization is the remedy and resolves through the primitives without the refusal; the merge transport's classification partitions paths rather than verifying them and resolves the same way.

## Rationale

The agentic-verification surfaces — implementation audit and review-changes — derive branch identity and diff scope from git, and base synchronization derives the base ref from the same primitives. A single shared home prevents either verification consumer from owning or duplicating the common derivation.

Scoping against the remote-tracking ref rather than a bare local branch ref keeps the changeset independent of local-ref staleness. A bare local ref such as `main` lags `origin/<base>` in a multi-worktree checkout where the local branch is left unattached. The three-dot diff recomputes its merge base from whichever ref it is given; against a stale local ref the merge base falls at an older divergence point, so commits already merged into the base re-enter the diff and surface as findings against work outside the changeset. Composing against the fetched remote-tracking ref fixes the merge base at the true branch point.

A verification result is a claim about one tree, and the tree that ships is the branch on the current default-branch tip, because integration requires a fast-forward descendant of that tip. A head that has fallen behind verifies a tree that cannot merge, and the only party that knows the tip advanced is the remote: the agent driving verification has no view of it, and a rule that says "sync before verifying" is followed by that same agent. Stamping the tip as the base identity makes a stale run visible as drift; placing the refusal in the one resolver every verifier imports makes the check mechanical and first, so a stale run is refused before it starts rather than sealed and discovered later. The merge base is the wrong identity because it stays fixed while the tip advances, which hides exactly the condition the refusal exists to surface.

Rejected: keeping the derivation in the audit skill with re-exports — it leaves a primitive shared by multiple skills owned by one of them and keeps the cross-skill `importlib` reach the consolidation removes.

## Verification

### Testing

- ALWAYS: resolving a committed selector whose base is git-derived or remote-tracking fetches that remote-tracking ref before comparing, so the refusal reads the remote's tip rather than a stale local remote-tracking ref ([compliance])
- ALWAYS: a head whose merge base with the fetched base tip is not that tip is refused with a dedicated exit code and a diagnostic naming the tip, the merge base, and the count of base commits the head lacks, and no scope is emitted ([compliance])
- ALWAYS: base synchronization and merge-transport classification resolve through the primitives without the refusal — one is the remedy, the other partitions paths rather than verifying them ([compliance])

### Audit

- ALWAYS: every verification skill that resolves a committed scope makes that resolution its first step and returns a refusal as a `stale-base` block before it opens a run or reads a subject ([audit])
- NEVER: a verification consumer resolves a git-derived or remote-tracking base through a path that bypasses the currency refusal ([audit])

- ALWAYS: every git-derived diff range is composed against the remote-tracking ref `origin/<base>` via `remote_tracking_ref` — `branch_scope` for the audit surface, `compute_diff` for the review surface — so a stale local branch ref does not widen the scope ([audit])
- ALWAYS: the changeset-derivation primitives are defined once in the changeset-scope skill's `scripts/changeset_scope.py`; implementation-audit orchestration, review-changes, and sync-base reach them only by import ([audit])
- ALWAYS: each changeset-derivation primitive that invokes git accepts a dependency-injected runner typed by a source-owned protocol, and composed primitives forward that runner through the complete call path ([audit])
- NEVER: a consumer skill re-implements a changeset-derivation primitive in its own `scripts/` ([audit])
- NEVER: tests replace git behavior through framework mocking; runner doubles cross the declared protocol boundary ([audit])
