"""Level-1 scenario evidence for `spx/32-distribution.enabler/21-bump.enabler/`."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.bump import (
    auto_detected_segment_is_minor_for_new_skill_addition,
    auto_detected_segment_is_patch_for_modification_only_changes,
    check_compares_added_manifest_to_base_source_path,
    check_compares_copied_manifest_to_base_source_path,
    check_fails_when_any_changed_plugin_is_not_yet_bumped,
    check_fails_when_changed_plugin_is_not_yet_bumped,
    check_fails_when_working_tree_version_is_below_base,
    check_passes_when_every_changed_plugin_is_already_bumped,
    dry_run_reports_would_be_new_version_without_writing,
    dual_manifest_plugin_writes_both_with_same_new_version,
    explicit_segment_patch_overrides_detected_minor_with_warning,
    mixed_dual_manifest_minor_change_uses_current_segment,
    no_changed_plugins_exits_zero_without_writing,
    only_changed_plugin_manifests_are_written,
    real_change_probe_detects_untracked_new_skill_as_added,
    segment_selection_produces_expected_versions,
    write_bumps_from_base_when_working_tree_version_is_below_base,
)


def test_only_changed_plugin_manifests_are_written() -> None:
    assert only_changed_plugin_manifests_are_written()


def test_dual_manifest_plugin_writes_both_with_same_new_version() -> None:
    assert dual_manifest_plugin_writes_both_with_same_new_version()


def test_mixed_dual_manifest_minor_change_uses_current_segment() -> None:
    assert mixed_dual_manifest_minor_change_uses_current_segment()


def test_segment_selection_produces_expected_versions() -> None:
    assert segment_selection_produces_expected_versions()


def test_no_changed_plugins_exits_zero_without_writing() -> None:
    assert no_changed_plugins_exits_zero_without_writing()


def test_dry_run_reports_would_be_new_version_without_writing() -> None:
    assert dry_run_reports_would_be_new_version_without_writing()


def test_check_passes_when_every_changed_plugin_is_already_bumped() -> None:
    assert check_passes_when_every_changed_plugin_is_already_bumped()


def test_write_bumps_from_base_when_working_tree_version_is_below_base() -> None:
    assert write_bumps_from_base_when_working_tree_version_is_below_base()


def test_check_fails_when_working_tree_version_is_below_base() -> None:
    assert check_fails_when_working_tree_version_is_below_base()


def test_check_compares_added_manifest_to_base_source_path() -> None:
    assert check_compares_added_manifest_to_base_source_path()


def test_check_compares_copied_manifest_to_base_source_path() -> None:
    assert check_compares_copied_manifest_to_base_source_path()


def test_check_fails_when_changed_plugin_is_not_yet_bumped() -> None:
    assert check_fails_when_changed_plugin_is_not_yet_bumped()


def test_check_fails_when_any_changed_plugin_is_not_yet_bumped() -> None:
    assert check_fails_when_any_changed_plugin_is_not_yet_bumped()


def test_auto_detected_segment_is_minor_for_new_skill_addition() -> None:
    assert auto_detected_segment_is_minor_for_new_skill_addition()


def test_auto_detected_segment_is_patch_for_modification_only_changes() -> None:
    assert auto_detected_segment_is_patch_for_modification_only_changes()


def test_explicit_segment_patch_overrides_detected_minor_with_warning() -> None:
    assert explicit_segment_patch_overrides_detected_minor_with_warning()


def test_real_change_probe_detects_untracked_new_skill_as_added(
    tmp_path: pathlib.Path,
) -> None:
    assert real_change_probe_detects_untracked_new_skill_as_added(tmp_path / "repo")
