"""Level-1 mapping evidence for bump segment classification."""

from __future__ import annotations

from outcomeeng.distribution.bump import ChangedPath, Segment, auto_segment
from outcomeeng_testing.generators.bump_mapping import (
    AUTO_SEGMENT_MAPPING_CASES,
    mixed_minor_triggering_changes,
    patch_only_changes,
)


def test_auto_segment_classifies_each_status_and_path_pattern() -> None:
    for status, path, expected in AUTO_SEGMENT_MAPPING_CASES:
        assert auto_segment([ChangedPath(status=status, path=path)]) == expected


def test_auto_segment_returns_minor_when_any_change_is_minor_triggering() -> None:
    assert auto_segment(mixed_minor_triggering_changes()) is Segment.MINOR


def test_auto_segment_returns_patch_when_no_change_triggers_minor() -> None:
    assert auto_segment(patch_only_changes()) is Segment.PATCH


def test_auto_segment_never_returns_major() -> None:
    for status, path, _ in AUTO_SEGMENT_MAPPING_CASES:
        assert (
            auto_segment([ChangedPath(status=status, path=path)]) is not Segment.MAJOR
        )
