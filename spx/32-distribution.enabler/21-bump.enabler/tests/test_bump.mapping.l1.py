"""Level-1 mapping evidence for bump segment classification."""

from __future__ import annotations

from outcomeeng_testing.harnesses.bump_mapping import (
    auto_segment_classifies_each_status_and_path_pattern,
    auto_segment_never_returns_major,
    auto_segment_returns_minor_when_any_change_is_minor_triggering,
    auto_segment_returns_patch_when_no_change_triggers_minor,
    segment_increment_matches_mapping,
)


def test_segment_increment_matches_mapping() -> None:
    assert segment_increment_matches_mapping()


def test_auto_segment_classifies_each_status_and_path_pattern() -> None:
    assert auto_segment_classifies_each_status_and_path_pattern()


def test_auto_segment_returns_minor_when_any_change_is_minor_triggering() -> None:
    assert auto_segment_returns_minor_when_any_change_is_minor_triggering()


def test_auto_segment_returns_patch_when_no_change_triggers_minor() -> None:
    assert auto_segment_returns_patch_when_no_change_triggers_minor()


def test_auto_segment_never_returns_major() -> None:
    assert auto_segment_never_returns_major()
