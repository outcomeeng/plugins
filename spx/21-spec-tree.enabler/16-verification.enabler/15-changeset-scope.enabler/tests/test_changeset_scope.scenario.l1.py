"""Scenario tests for the changeset-scope git-derivation primitives.

Covers the Scenario assertions in ``../changeset-scope.md``:

- ``detect_base_ref`` returns the bare base-branch name from ``origin/HEAD``;
  strict raises ``BaseRefNotConfiguredError`` and non-strict returns
  ``DEFAULT_BASE_REF`` when ``origin/HEAD`` is unset.
- ``remote_tracking_ref`` composes the remote-tracking ref ``origin/<base>``.
- ``branch_scope`` diffs the three-dot range ``origin/<base>...HEAD``.
- A local branch ref that lags its remote-tracking ref does not widen the
  scope: scoping against ``origin/<base>`` excludes commits already merged into
  the base, while scoping against the stale local ref re-includes them.

These are ``l1`` — direct in-process calls into ``changeset_scope`` against a
synthetic git repository seeded under ``tmp_path``; git and temp dirs are
expected on a working machine.
"""

from __future__ import annotations

import pathlib

import pytest
from outcomeeng_testing.harnesses.changeset_scope import (
    build_repo_without_origin,
    build_stale_local_base_repo,
    load_changeset_scope_module,
)


def _repo(tmp_path: pathlib.Path) -> pathlib.Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


def test_detect_base_ref_returns_bare_base_from_origin_head(
    tmp_path: pathlib.Path,
) -> None:
    module = load_changeset_scope_module()
    stale = build_stale_local_base_repo(_repo(tmp_path))
    assert module.detect_base_ref(stale.repo) == stale.base_ref


def test_detect_base_ref_non_strict_falls_back_to_default_without_origin(
    tmp_path: pathlib.Path,
) -> None:
    module = load_changeset_scope_module()
    repo = _repo(tmp_path)
    build_repo_without_origin(repo)
    assert module.detect_base_ref(repo, strict=False) == module.DEFAULT_BASE_REF


def test_detect_base_ref_strict_raises_without_origin(tmp_path: pathlib.Path) -> None:
    module = load_changeset_scope_module()
    repo = _repo(tmp_path)
    build_repo_without_origin(repo)
    with pytest.raises(module.BaseRefNotConfiguredError):
        module.detect_base_ref(repo, strict=True)


def test_remote_tracking_ref_composes_origin_prefix(tmp_path: pathlib.Path) -> None:
    module = load_changeset_scope_module()
    stale = build_stale_local_base_repo(_repo(tmp_path))
    assert (
        module.remote_tracking_ref(stale.base_ref)
        == f"{module.ORIGIN_REF_PREFIX}{stale.base_ref}"
    )


def test_branch_scope_returns_feature_change_against_remote_tracking_base(
    tmp_path: pathlib.Path,
) -> None:
    module = load_changeset_scope_module()
    stale = build_stale_local_base_repo(_repo(tmp_path))
    files = module.branch_scope(stale.base_ref, repo=stale.repo)
    assert stale.feature_file in files


def test_stale_local_base_ref_does_not_widen_scope(tmp_path: pathlib.Path) -> None:
    # The crux: the feature branch contains a commit already merged into
    # origin/<base>, while the local base ref lags behind it. Scoping against
    # the remote-tracking ref (what branch_scope composes via remote_tracking_ref)
    # excludes the merged commit; scoping against the stale local ref re-includes
    # it. Asserting both directions makes the test falsifying — it fails if
    # branch_scope ever scopes against the bare local ref.
    module = load_changeset_scope_module()
    stale = build_stale_local_base_repo(_repo(tmp_path))

    remote_tracking_scope = module.branch_scope(stale.base_ref, repo=stale.repo)
    assert stale.merged_file not in remote_tracking_scope
    assert stale.feature_file in remote_tracking_scope

    # Control: diffing against the stale local base ref widens the scope to
    # re-include the already-merged commit — the defect remote-tracking scoping
    # avoids.
    local_ref_scope = module.expand_diff_range(
        f"{stale.base_ref}...HEAD", repo=stale.repo
    )
    assert stale.merged_file in local_ref_scope
