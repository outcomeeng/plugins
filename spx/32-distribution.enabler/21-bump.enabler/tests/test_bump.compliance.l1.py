"""Level-1 compliance evidence for `spx/32-distribution.enabler/21-bump.enabler/`."""

from __future__ import annotations

from outcomeeng_testing.harnesses.bump import (
    already_bumped_plugin_is_skipped_not_rewritten,
    already_bumped_plugin_skipped_in_dry_run,
    already_bumped_plugin_skipped_while_other_changed_plugin_is_bumped,
    auto_detection_never_writes_a_major_bump_through_the_orchestrator,
    dry_run_and_check_are_mutually_exclusive_at_the_cli_boundary,
    dry_run_skips_already_bumped_plugin_and_reports_the_other,
    dual_manifest_plugin_writes_every_owned_manifest,
    missing_required_tool_fails_fast_with_diagnostic,
    mixed_dual_manifest_plugin_aligns_every_owned_manifest_to_current_max,
    mixed_dual_manifest_plugin_aligns_lagging_manifest_to_current_bump,
    mixed_dual_manifest_plugin_fails_check,
    non_version_content_is_preserved_character_for_character,
    read_only_modes_never_write_regardless_of_plugin_state,
    tool_availability_is_probed_before_any_other_probe_or_write,
    unchanged_plugins_never_have_manifests_written,
)


def test_missing_required_tool_fails_fast_with_diagnostic() -> None:
    assert missing_required_tool_fails_fast_with_diagnostic()


def test_tool_availability_is_probed_before_any_other_probe_or_write() -> None:
    assert tool_availability_is_probed_before_any_other_probe_or_write()


def test_already_bumped_plugin_is_skipped_not_rewritten() -> None:
    assert already_bumped_plugin_is_skipped_not_rewritten()


def test_already_bumped_plugin_skipped_while_other_changed_plugin_is_bumped() -> None:
    assert already_bumped_plugin_skipped_while_other_changed_plugin_is_bumped()


def test_mixed_dual_manifest_plugin_aligns_lagging_manifest_to_current_bump() -> None:
    assert mixed_dual_manifest_plugin_aligns_lagging_manifest_to_current_bump()


def test_mixed_dual_manifest_plugin_aligns_every_owned_manifest_to_current_max() -> (
    None
):
    assert mixed_dual_manifest_plugin_aligns_every_owned_manifest_to_current_max()


def test_mixed_dual_manifest_plugin_fails_check() -> None:
    assert mixed_dual_manifest_plugin_fails_check()


def test_already_bumped_plugin_skipped_in_dry_run() -> None:
    assert already_bumped_plugin_skipped_in_dry_run()


def test_dry_run_skips_already_bumped_plugin_and_reports_the_other() -> None:
    assert dry_run_skips_already_bumped_plugin_and_reports_the_other()


def test_unchanged_plugins_never_have_manifests_written() -> None:
    assert unchanged_plugins_never_have_manifests_written()


def test_dual_manifest_plugin_writes_every_owned_manifest() -> None:
    assert dual_manifest_plugin_writes_every_owned_manifest()


def test_non_version_content_is_preserved_character_for_character() -> None:
    assert non_version_content_is_preserved_character_for_character()


def test_read_only_modes_never_write_regardless_of_plugin_state() -> None:
    assert read_only_modes_never_write_regardless_of_plugin_state()


def test_dry_run_and_check_are_mutually_exclusive_at_the_cli_boundary() -> None:
    assert dry_run_and_check_are_mutually_exclusive_at_the_cli_boundary()


def test_auto_detection_never_writes_a_major_bump_through_the_orchestrator() -> None:
    assert auto_detection_never_writes_a_major_bump_through_the_orchestrator()
