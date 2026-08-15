"""Level-1 compliance evidence for `spx/32-distribution.enabler/21-bump.enabler/`."""

from __future__ import annotations

from outcomeeng.distribution.bump import Mode, REQUIRED_TOOLS
from outcomeeng_testing.generators.bump import version_of
from outcomeeng_testing.harnesses.bump import (
    TOOL_EVENT_PREFIX,
    observe_all_minor_triggering_changes_run,
    observe_already_bumped_beside_unbumped_plugin,
    observe_already_bumped_plugin,
    observe_cli_dry_run_check_combination,
    observe_dual_manifest_plugin,
    observe_explicit_segment_override_run,
    observe_fixture_manifest_rewrite,
    observe_missing_required_tool_runs,
    observe_mixed_dual_manifest_plugin,
    observe_modification_only_changes_run,
    observe_probe_ordering,
    observe_shared_fragment_changes,
    observe_read_only_mode_runs,
    observe_unchanged_plugins_run,
)


def test_missing_required_tool_fails_fast_with_diagnostic() -> None:
    for run in observe_missing_required_tool_runs():
        assert run.outcome.exit_code != 0
        assert run.outcome.writes == ()
        assert run.outcome.change_queries == ()
        assert run.outcome.reader_queries == ()
        assert run.missing_tool in run.outcome.diagnostics


def test_tool_availability_is_probed_before_any_other_probe_or_write() -> None:
    exit_code, events = observe_probe_ordering()
    first_other = next(
        (
            index
            for index, event in enumerate(events)
            if not event.startswith(TOOL_EVENT_PREFIX)
        ),
        len(events),
    )
    probed_first = {
        event.removeprefix(TOOL_EVENT_PREFIX) for event in events[:first_other]
    }

    assert exit_code == 0
    assert probed_first >= set(REQUIRED_TOOLS)


def test_already_bumped_plugin_is_skipped_not_rewritten() -> None:
    observation = observe_already_bumped_plugin()

    assert observation.outcome.exit_code == 0
    assert observation.outcome.writes == ()
    assert observation.plugin in observation.outcome.stderr


def test_already_bumped_plugin_skipped_while_other_changed_plugin_is_bumped() -> None:
    observation = observe_already_bumped_beside_unbumped_plugin()
    written = observation.outcome.written

    assert observation.outcome.exit_code == 0
    assert observation.already_bumped_path not in written
    assert version_of(written[observation.unbumped_path]) == "0.4.2"
    assert observation.already_bumped_plugin in observation.outcome.stderr


def test_mixed_dual_manifest_plugin_aligns_lagging_manifest_to_current_bump() -> None:
    observation = observe_mixed_dual_manifest_plugin(claude_version="0.4.2")
    written = observation.outcome.written

    assert observation.outcome.exit_code == 0
    assert set(written) == {observation.claude_path, observation.codex_path}
    assert version_of(written[observation.claude_path]) == "0.4.2"
    assert version_of(written[observation.codex_path]) == "0.4.2"


def test_mixed_dual_manifest_aligns_owned_manifests_to_current_max() -> None:
    observation = observe_mixed_dual_manifest_plugin(claude_version="0.4.3")
    written = observation.outcome.written

    assert observation.outcome.exit_code == 0
    assert set(written) == {observation.claude_path, observation.codex_path}
    assert version_of(written[observation.claude_path]) == "0.4.3"
    assert version_of(written[observation.codex_path]) == "0.4.3"


def test_already_bumped_plugin_skipped_in_dry_run() -> None:
    observation = observe_already_bumped_plugin(Mode.DRY_RUN)

    assert observation.outcome.exit_code == 0
    assert observation.outcome.writes == ()
    assert observation.plugin in observation.outcome.stderr


def test_dry_run_skips_already_bumped_plugin_and_reports_the_other() -> None:
    observation = observe_already_bumped_beside_unbumped_plugin(mode=Mode.DRY_RUN)

    assert observation.outcome.exit_code == 0
    assert observation.outcome.writes == ()
    assert observation.unbumped_plugin in observation.outcome.stdout
    assert "0.4.1 -> 0.4.2" in observation.outcome.stdout
    assert observation.already_bumped_plugin in observation.outcome.stderr


def test_unchanged_plugins_never_have_manifests_written() -> None:
    changed_path, outcome = observe_unchanged_plugins_run()

    assert outcome.exit_code == 0
    assert [path for path, _ in outcome.writes] == [changed_path]
    assert outcome.reader_queries == ("foo",)


def test_dual_manifest_plugin_writes_every_owned_manifest() -> None:
    observation = observe_dual_manifest_plugin()
    written = observation.outcome.written

    assert observation.outcome.exit_code == 0
    assert set(written) == {observation.claude_path, observation.codex_path}
    assert {version_of(content) for content in written.values()} == {"0.4.2"}


def test_non_version_content_is_preserved_character_for_character() -> None:
    path, original, outcome = observe_fixture_manifest_rewrite()
    rewritten = outcome.written[path]

    assert outcome.exit_code == 0
    assert rewritten == original.replace(
        f'"version": "{version_of(original)}"',
        f'"version": "{version_of(rewritten)}"',
        1,
    )


def test_read_only_modes_never_write_regardless_of_plugin_state() -> None:
    for outcome in observe_read_only_mode_runs():
        assert outcome.writes == ()


def test_dry_run_and_check_are_mutually_exclusive_at_the_cli_boundary() -> None:
    exit_code, stderr = observe_cli_dry_run_check_combination()

    assert exit_code != 0
    assert "not allowed with" in stderr


def test_auto_detection_never_writes_a_major_bump_through_the_orchestrator() -> None:
    path, outcome = observe_all_minor_triggering_changes_run()

    assert outcome.exit_code == 0
    assert version_of(outcome.written[path]) == "0.5.0"


def test_auto_detected_segment_is_patch_for_modification_only_changes() -> None:
    path, outcome = observe_modification_only_changes_run()

    assert outcome.exit_code == 0
    assert version_of(outcome.written[path]) == "0.4.2"


def test_explicit_segment_patch_overrides_detected_minor_with_warning() -> None:
    plugin, path, outcome = observe_explicit_segment_override_run()

    assert outcome.exit_code == 0
    assert version_of(outcome.written[path]) == "0.4.2"
    assert plugin in outcome.stderr
    assert "minor" in outcome.stderr


def test_shared_fragment_change_reaches_its_including_plugin() -> None:
    handle, changed = observe_shared_fragment_changes()

    assert handle.including_plugin in changed
    assert handle.unrelated_plugin not in changed
    assert handle.fragment_path in {
        change.path for change in changed[handle.including_plugin]
    }
