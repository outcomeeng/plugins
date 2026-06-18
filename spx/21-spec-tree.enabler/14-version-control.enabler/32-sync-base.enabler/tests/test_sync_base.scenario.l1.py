"""Scenario tests for the sync-base base-synchronization module.

Covers the Scenario assertions in ``../sync-base.md``:

- A branch behind its fetched base has its own commits replayed onto
  ``origin/<base>`` with the base's changes present.
- A branch already current with its fetched base performs no rebase.
- A rebase conflict stops with the ``SYNC_BASE`` action token, leaving the
  branch and working tree intact.
- A detached HEAD with no branch to rebase reports a hard git failure.

These are ``l1`` — direct in-process calls into ``sync_base`` against real git
repositories (a bare origin and working clones) seeded under ``tmp_path``; git
and temp dirs are expected on a working machine.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.sync_base import (
    build_alternate_base_repo,
    build_behind_base_repo,
    build_conflicting_repo,
    build_current_repo,
    detach_head,
    load_sync_base_module,
)


def _root(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "pool"
    root.mkdir()
    return root


def test_behind_base_branch_is_rebased_onto_remote_tracking_base(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.REBASED
    assert result.remote_ref == handle.remote_ref
    assert result.branch == handle.feature_branch
    # The feature commit's effect survives the rebase (it was replayed)...
    assert (handle.repo / handle.feature_file).exists()
    # ...and the base advance the branch was behind is now present.
    assert (handle.repo / handle.base_file).exists()


def test_branch_already_current_performs_no_rebase(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_current_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.ALREADY_CURRENT
    assert result.branch == handle.feature_branch
    assert result.action_token is None


def test_rebase_conflict_stops_with_sync_base_token_intact(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_conflicting_repo(_root(tmp_path))

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.CONFLICT
    assert result.action_token == module.SYNC_BASE_TOKEN
    # The aborted rebase leaves no rebase in progress...
    assert not (handle.repo / ".git" / "rebase-merge").exists()
    assert not (handle.repo / ".git" / "rebase-apply").exists()
    # ...and the feature's own edit is intact, not a conflicted blend.
    assert (handle.repo / handle.conflict_file).read_text(
        encoding="utf-8"
    ) == "feature edit\n"


def test_detached_head_reports_hard_git_failure(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_behind_base_repo(_root(tmp_path))
    detach_head(handle.repo)

    result = module.sync_base(handle.repo)

    assert result.status is module.SyncStatus.GIT_FAILURE
    assert result.branch is None
    assert result.action_token is None


def test_explicit_base_ref_overrides_origin_head(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_current_repo(_root(tmp_path))

    # An explicit base name is used instead of the origin/HEAD default: the run
    # targets origin/<given> and fails to resolve a base that does not exist,
    # rather than syncing against the detected default.
    result = module.sync_base(handle.repo, base_ref="not-a-branch", fetch=False)

    assert result.status is module.SyncStatus.GIT_FAILURE
    assert result.base_ref == "not-a-branch"
    assert result.remote_ref == module.remote_tracking_ref("not-a-branch")


def test_explicit_valid_base_rebases_onto_that_base_not_origin_head(
    tmp_path: pathlib.Path,
) -> None:
    module = load_sync_base_module()
    handle = build_alternate_base_repo(_root(tmp_path))

    # The feature is current with the origin/HEAD default, so syncing onto the
    # default does nothing...
    default_result = module.sync_base(handle.repo, base_ref=handle.default_ref)
    assert default_result.status is module.SyncStatus.ALREADY_CURRENT

    # ...but it is behind the caller-supplied alternate base, so syncing onto
    # that base rebases the feature onto origin/<alternate> and brings the
    # alternate's advance into the working tree.
    result = module.sync_base(handle.repo, base_ref=handle.alternate_ref)
    assert result.status is module.SyncStatus.REBASED
    assert result.remote_ref == handle.alternate_remote_ref
    assert (handle.repo / handle.alternate_file).exists()
    assert (handle.repo / handle.feature_file).exists()
