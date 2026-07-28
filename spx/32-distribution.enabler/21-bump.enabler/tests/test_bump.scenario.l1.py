"""Level-1 scenario evidence for `spx/32-distribution.enabler/21-bump.enabler/`."""

from __future__ import annotations

from outcomeeng.distribution.bump import FileStatus, Mode, Segment, auto_segment
from outcomeeng_testing.generators.bump import version_of
from outcomeeng_testing.harnesses.bump import (
    base_ref,
    observe_base_source_path_comparison,
    observe_below_base_plugin,
    observe_check_all_plugins_bumped,
    observe_check_one_plugin_unbumped,
    observe_check_unbumped_plugin,
    observe_cross_plugin_rename_changes,
    observe_dry_run_report,
    observe_malformed_manifest_runs,
    observe_mixed_dual_manifest_plugin,
    observe_new_plugin_without_base_manifest,
    observe_new_skill_addition_run,
    observe_no_changed_plugins_run,
    observe_renamed_structural_path_changes,
    observe_segment_selection_runs,
    observe_single_changed_plugin_run,
    observe_untracked_new_skill_changes,
)

EXPECTED_VERSION_BY_SEGMENT = {
    Segment.PATCH: "0.4.2",
    Segment.MINOR: "0.5.0",
    Segment.MAJOR: "1.0.0",
}


def test_only_changed_plugin_manifests_are_written() -> None:
    changed_path, unchanged_plugin, outcome = observe_single_changed_plugin_run()

    assert outcome.exit_code == 0
    assert list(outcome.written) == [changed_path]
    assert version_of(outcome.written[changed_path]) == "0.4.2"
    assert unchanged_plugin not in outcome.reader_queries


def test_mixed_dual_manifest_minor_change_uses_current_segment() -> None:
    observation = observe_mixed_dual_manifest_plugin(
        claude_version="0.4.2", segment=Segment.MINOR
    )
    written = observation.outcome.written

    assert observation.outcome.exit_code == 0
    assert set(written) == {observation.claude_path, observation.codex_path}
    assert version_of(written[observation.claude_path]) == "0.5.0"
    assert version_of(written[observation.codex_path]) == "0.5.0"


def test_segment_selection_produces_expected_versions() -> None:
    for segment, observation in observe_segment_selection_runs():
        assert observation.outcome.exit_code == 0
        assert (
            version_of(observation.outcome.written[observation.path])
            == EXPECTED_VERSION_BY_SEGMENT[segment]
        )


def test_no_changed_plugins_exits_zero_without_writing() -> None:
    outcome = observe_no_changed_plugins_run()

    assert outcome.exit_code == 0
    assert outcome.writes == ()
    assert outcome.reader_queries == ()


def test_dry_run_reports_would_be_new_version_without_writing() -> None:
    observation = observe_dry_run_report()

    assert observation.outcome.exit_code == 0
    assert observation.outcome.writes == ()
    assert "0.4.2" in observation.outcome.stdout
    assert observation.plugin in observation.outcome.stdout


def test_check_passes_when_every_changed_plugin_is_already_bumped() -> None:
    outcome = observe_check_all_plugins_bumped()

    assert outcome.exit_code == 0
    assert outcome.writes == ()
    assert outcome.stderr == ""


def test_new_plugin_without_base_manifest_passes_check() -> None:
    outcome = observe_new_plugin_without_base_manifest()

    assert outcome.exit_code == 0
    assert outcome.writes == ()
    assert outcome.stderr == ""


def test_check_fails_when_changed_plugin_is_not_yet_bumped() -> None:
    observation = observe_check_unbumped_plugin()

    assert observation.outcome.exit_code != 0
    assert observation.outcome.writes == ()
    assert observation.plugin in observation.outcome.stderr


def test_check_fails_when_any_changed_plugin_is_not_yet_bumped() -> None:
    observation = observe_check_one_plugin_unbumped()

    assert observation.outcome.exit_code != 0
    assert observation.outcome.writes == ()
    assert observation.unbumped_plugin in observation.outcome.stderr
    assert observation.already_bumped_plugin not in observation.outcome.stderr


def test_mixed_dual_manifest_plugin_fails_check() -> None:
    observation = observe_mixed_dual_manifest_plugin(
        claude_version="0.4.2", mode=Mode.CHECK
    )

    assert observation.outcome.exit_code == 1
    assert observation.outcome.writes == ()
    assert observation.plugin in observation.outcome.stderr
    assert "out of lockstep" in observation.outcome.stderr


def test_unparseable_manifest_returns_diagnostic_without_writes() -> None:
    for path, expected_diagnostic, outcome in observe_malformed_manifest_runs():
        assert outcome.exit_code == 1
        assert outcome.writes == ()
        assert path in outcome.stderr
        assert expected_diagnostic in outcome.stderr


def test_write_bumps_from_base_when_working_tree_version_is_below_base() -> None:
    observation = observe_below_base_plugin()

    assert observation.outcome.exit_code == 0
    assert version_of(observation.outcome.written[observation.path]) == "0.73.1"


def test_check_fails_when_working_tree_version_is_below_base() -> None:
    observation = observe_below_base_plugin(mode=Mode.CHECK)

    assert observation.outcome.exit_code == 1
    assert observation.outcome.writes == ()
    assert observation.plugin in observation.outcome.stderr


def test_check_compares_added_manifest_to_base_source_path() -> None:
    src_path, base_path, outcome = observe_base_source_path_comparison(FileStatus.ADDED)

    assert outcome.exit_code == 0
    assert outcome.writes == ()
    assert outcome.stderr == ""
    assert list(outcome.content_queries) == [
        (base_ref(), src_path),
        (base_ref(), base_path),
    ]


def test_check_compares_copied_manifest_to_base_source_path() -> None:
    src_path, base_path, outcome = observe_base_source_path_comparison(
        FileStatus.COPIED
    )

    assert outcome.exit_code == 0
    assert outcome.writes == ()
    assert outcome.stderr == ""
    assert list(outcome.content_queries) == [
        (base_ref(), src_path),
        (base_ref(), base_path),
    ]


def test_auto_detected_segment_is_minor_for_new_skill_addition() -> None:
    path, outcome = observe_new_skill_addition_run()

    assert outcome.exit_code == 0
    assert version_of(outcome.written[path]) == "0.5.0"


def test_real_change_probe_detects_untracked_new_skill_as_added() -> None:
    handle, changes = observe_untracked_new_skill_changes()
    by_path = {change.path: change for change in changes.get(handle.plugin, ())}

    assert by_path[handle.tracked_modified_path].status is FileStatus.MODIFIED
    assert by_path[handle.untracked_added_path].status is FileStatus.ADDED
    assert by_path[handle.untracked_codex_added_path].status is FileStatus.ADDED


def test_real_change_probe_detects_rename_away_from_structural_path() -> None:
    handle, changes = observe_renamed_structural_path_changes()
    by_path = {change.path: change for change in changes.get(handle.plugin, ())}
    renamed = by_path[handle.renamed_path]

    assert renamed.status is FileStatus.RENAMED
    assert renamed.old_path == handle.structural_path
    assert auto_segment(changes[handle.plugin]) is Segment.MINOR


def test_real_change_probe_detects_cross_plugin_structural_rename() -> None:
    handle, changes = observe_cross_plugin_rename_changes()
    source_changes = {change.path: change for change in changes[handle.source_plugin]}
    target_changes = {change.path: change for change in changes[handle.target_plugin]}

    assert source_changes.keys() == {handle.target_path}
    assert target_changes.keys() == {handle.target_path}
    assert source_changes[handle.target_path].old_path == handle.source_path
    assert target_changes[handle.target_path].old_path == handle.source_path
    assert auto_segment(changes[handle.source_plugin]) is Segment.MINOR
    assert auto_segment(changes[handle.target_plugin]) is Segment.MINOR
