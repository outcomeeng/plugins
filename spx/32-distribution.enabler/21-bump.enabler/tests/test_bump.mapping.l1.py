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
    change_attribution_inputs,
    lifecycle_surface_changes,
    mixed_minor_triggering_changes,
    non_lifecycle_surface_changes,
    patch_only_changes,
)


def test_a_lifecycle_change_to_a_declared_surface_is_minor() -> None:
    for change in lifecycle_surface_changes():
        assert auto_segment([change]) is Segment.MINOR, change


def test_a_modifying_or_undeclared_surface_change_is_patch() -> None:
    for change in non_lifecycle_surface_changes():
        assert auto_segment([change]) is Segment.PATCH, change


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
    for change in lifecycle_surface_changes() + non_lifecycle_surface_changes():
        assert auto_segment([change]) is not Segment.MAJOR, change
