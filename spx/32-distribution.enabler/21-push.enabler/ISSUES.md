# Issues: Push

The **push wrapper** refreshes every local marketplace plugin after a no-upstream direct push because it supplies no pre-push base reference to change detection.

## Preserve the published range without an upstream

**Evidence.** `just push-marketplace origin HEAD:refs/heads/main` published a changeset containing only `spx/21-spec-tree.enabler/65-apply.enabler/ISSUES.md`, then printed `Running marketplace refresh: no base_ref supplied` and refreshed all nine installed plugins. [`spx/32-distribution.enabler/21-push.enabler/push.md`](push.md) declares that a branch without an upstream invokes sync without `base_ref`; [`outcomeeng/distribution/push.py`](../../../outcomeeng/distribution/push.py) implements that publish-and-sync boundary.

**Impact.** Coordination-note-only direct pushes perform unnecessary user-scope marketplace mutations, extend the publication path, and rewrite compatibility links even when the published range changes no plugin distribution file.

**Deferral reason.** The fix is a separate larger concern because it changes the push wrapper's range-capture contract, its no-upstream scenario evidence, and the sync handoff for every explicit destination ref. The selected creator-skill slice consumes the publication workflow but does not own distribution orchestration.

**Required handling.** Preserve the remote destination's pre-push commit for explicit refspecs, or add an equivalent source-owned range input, and pass that commit to sync after a successful push. Add scenario evidence proving that a no-upstream push to an explicit destination skips marketplace refresh when the published range changes no plugin distribution path.

**Revisit condition.** Resolve this entry before the next direct-push lifecycle, or in the next change to `outcomeeng/distribution/push.py`, its scenario tests, or the push-and-sync contract, whichever occurs first.
