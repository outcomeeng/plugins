"""Scenario evidence for the /merge changeset classifier."""

from __future__ import annotations

from outcomeeng_testing.harnesses.changeset_scope import (
    assert_merge_classifier_handles_spaced_coordination_note,
    assert_merge_classifier_reports_unconfigured_base,
    assert_merge_classifier_uses_canonical_changeset_scope,
)


def test_changed_paths_use_the_canonical_changeset_scope() -> None:
    assert_merge_classifier_uses_canonical_changeset_scope()


def test_spaced_coordination_note_path_is_preserved() -> None:
    assert_merge_classifier_handles_spaced_coordination_note()


def test_unconfigured_remote_base_is_reported_without_traceback() -> None:
    assert_merge_classifier_reports_unconfigured_base()
