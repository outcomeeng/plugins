"""Scenario evidence for the /merge changeset classifier."""

from __future__ import annotations

from outcomeeng_testing.harnesses.changeset_scope import (
    canonical_merge_comparison,
    spaced_note_comparison,
    unconfigured_base_comparison,
)


def test_changed_paths_use_the_canonical_changeset_scope() -> None:
    assert canonical_merge_comparison().actual == canonical_merge_comparison().expected


def test_spaced_coordination_note_path_is_preserved() -> None:
    assert spaced_note_comparison().actual == spaced_note_comparison().expected


def test_unconfigured_remote_base_is_reported_without_traceback() -> None:
    assert (
        unconfigured_base_comparison().actual == unconfigured_base_comparison().expected
    )
