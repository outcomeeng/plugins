"""Level 1 mapping tests for the init-worktrees layout classifier.

Each case constructs a source-owned ``GitFacts`` shape and pins the layout
verdict the classifier must return. The expected verdicts are derived from
``spx/21-spec-tree.enabler/11-repository-layout.pdr.md`` — a single working tree
and a complete bare pool are compliant; every other shape is non-compliant — not
copied from the classifier's output.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.worktree_provisioning import (
    load_init_worktrees_module,
)

_module = load_init_worktrees_module()
GitFacts = _module.GitFacts
Layout = _module.Layout
classify = _module.classify


def _facts(
    *,
    common_dir_is_bare: bool = False,
    has_linked_worktrees: bool = False,
    main_worktree_present: bool = False,
    main_worktree_beside_common_dir: bool = False,
    main_tracks_origin_main: bool = False,
    spx_beside_common_dir: bool = False,
):
    return GitFacts(
        common_dir_is_bare=common_dir_is_bare,
        has_linked_worktrees=has_linked_worktrees,
        main_worktree_present=main_worktree_present,
        main_worktree_beside_common_dir=main_worktree_beside_common_dir,
        main_tracks_origin_main=main_tracks_origin_main,
        spx_beside_common_dir=spx_beside_common_dir,
    )


_COMPLETE_POOL = dict(
    common_dir_is_bare=True,
    main_worktree_present=True,
    main_worktree_beside_common_dir=True,
    main_tracks_origin_main=True,
    spx_beside_common_dir=True,
)

LAYOUT_CASES = [
    pytest.param(
        _facts(common_dir_is_bare=False, has_linked_worktrees=False),
        "SINGLE",
        id="lone-working-tree",
    ),
    pytest.param(
        _facts(common_dir_is_bare=False, has_linked_worktrees=True),
        "NON_COMPLIANT",
        id="linked-worktrees-on-non-bare-root",
    ),
    pytest.param(_facts(**_COMPLETE_POOL), "POOL", id="complete-bare-pool"),
    pytest.param(
        _facts(**{**_COMPLETE_POOL, "main_worktree_present": False}),
        "NON_COMPLIANT",
        id="pool-missing-main-worktree",
    ),
    pytest.param(
        _facts(**{**_COMPLETE_POOL, "main_worktree_beside_common_dir": False}),
        "NON_COMPLIANT",
        id="pool-main-not-beside-common-dir",
    ),
    pytest.param(
        _facts(**{**_COMPLETE_POOL, "main_tracks_origin_main": False}),
        "NON_COMPLIANT",
        id="pool-main-not-tracking-origin-main",
    ),
    pytest.param(
        _facts(**{**_COMPLETE_POOL, "spx_beside_common_dir": False}),
        "NON_COMPLIANT",
        id="pool-spx-not-beside-common-dir",
    ),
]


@pytest.mark.parametrize(("facts", "expected_name"), LAYOUT_CASES)
def test_layout_shape_maps_to_expected_verdict(facts, expected_name: str) -> None:
    assert classify(facts) is getattr(Layout, expected_name)
