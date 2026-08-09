"""Level-1 mapping evidence for bump segment classification."""

from __future__ import annotations

from outcomeeng.distribution.bump import (
    ChangedPath,
    FileStatus,
    Segment,
    auto_segment,
    plugins_from_change,
)
from outcomeeng_testing.generators.bump_mapping import (
    ATTRIBUTION_DESTINATION_PLUGIN,
    ATTRIBUTION_SOURCE_PLUGIN,
    AUTO_SEGMENT_MAPPING_CASES,
    change_attribution_inputs,
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


def test_each_file_status_attributes_its_change_to_the_expected_plugins() -> None:
    changes = change_attribution_inputs()

    assert {change.status for change in changes} == set(FileStatus)
    for change in changes:
        expected = {ATTRIBUTION_DESTINATION_PLUGIN}
        if change.status is FileStatus.RENAMED:
            expected.add(ATTRIBUTION_SOURCE_PLUGIN)

        assert plugins_from_change(change) == expected


def test_auto_segment_never_returns_major() -> None:
    for status, path, _ in AUTO_SEGMENT_MAPPING_CASES:
        assert (
            auto_segment([ChangedPath(status=status, path=path)]) is not Segment.MAJOR
        )
