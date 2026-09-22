"""Compliance evidence for deterministic native-profile probe planning."""

from dataclasses import replace

import pytest

from outcomeeng_testing.harnesses.discovery_auth_cases import NativeFault
from outcomeeng_testing.harnesses import (
    native_profile_execution as profile_execution_harness,
)
from outcomeeng_testing.harnesses.installation import (
    native_profile_execution_recipe,
)
from outcomeeng_testing.harnesses.native_profile_failures import native_profile_failure

from pathlib import Path

from outcomeeng.distribution.native_profile_execution import native_profile_rows
from outcomeeng.distribution.profiles import AGENT_PROFILES
from outcomeeng.validation.agent_disable import AGENT_SWITCHES
from outcomeeng.validation.agent_switch_enforcement import (
    DECLARING_MODULE_NAME,
    NotAPythonSource,
    modules_naming_a_switch,
    modules_reading_the_switch_predicate,
)
from outcomeeng.distribution.native_thread_evidence import (
    ChildIdentityField,
    NativeTurnStatus,
)
from outcomeeng_testing.generators.native_thread_evidence import NativeEvidenceCase
from outcomeeng_testing.harnesses.native_thread_evidence import (
    NativeEvidenceContext,
    RecordingThreadReader,
    exercise_native_evidence,
)


def test_failed_installation_retains_evidence_and_removes_state_without_retry() -> None:
    with native_profile_failure(NativeFault.INSTALL_FAILURE) as observation:
        assert len(observation.calls) == len(observation.rows)
        for item in observation.rows:
            assert item.terminal_condition is not None
            assert item.launch_exit_code is None
            assert item.row.definition_path.is_file()
            assert item.row.loading_path.is_file()
            assert item.row.result_path.is_file()
            assert not item.row.state_root.exists()


def test_timed_out_installation_retains_evidence_and_removes_state_without_retry() -> (
    None
):
    with native_profile_failure(NativeFault.TIMEOUT) as observation:
        assert len(observation.calls) == len(observation.rows)
        for item in observation.rows:
            assert item.terminal_condition is not None
            assert item.launch_exit_code is None
            assert item.row.result_path.is_file()
            assert not item.row.state_root.exists()


def test_native_child_read_retains_correlated_configuration_and_completion() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        reader = RecordingThreadReader.from_thread(case.thread)
        result = context.collect(case, reader)
        assert result.terminal_condition is None
        assert result.thread == case.thread
        assert len(reader.calls) == 1
        assert reader.calls[0][0] == case.thread["parentThreadId"]
        assert reader.calls[0][1] == context.cwd
        assert reader.calls[0][2] == context.environment

    exercise_native_evidence(assert_case)


def test_missing_native_identity_is_unusable() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        for identity in ChildIdentityField:
            reader = RecordingThreadReader.without_identity(case.thread, identity)
            assert context.collect(case, reader).terminal_condition is not None
            assert len(reader.calls) == 1

    exercise_native_evidence(assert_case)


def test_mismatched_native_identity_is_unusable() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        for identity in ChildIdentityField:
            reader = RecordingThreadReader.mismatched_identity(case.thread, identity)
            assert context.collect(case, reader).terminal_condition is not None
            assert len(reader.calls) == 1

    exercise_native_evidence(assert_case)


def test_failed_native_read_is_terminal_without_retry() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        reader = RecordingThreadReader.failed_read()
        result = context.collect(case, reader)
        assert result.terminal_condition is not None
        assert result.thread_read == reader.response
        assert len(reader.calls) == 1

    exercise_native_evidence(assert_case)


def test_multiple_parents_cannot_supply_single_child_evidence() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        reader = RecordingThreadReader.from_thread(case.thread)
        result = context.collect(
            replace(case, events=case.events + case.events), reader
        )
        assert result.terminal_condition is not None
        assert not reader.calls

    exercise_native_evidence(assert_case)


def test_incomplete_native_turn_cannot_supply_completion_evidence() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        for status in NativeTurnStatus:
            if status is NativeTurnStatus.COMPLETED:
                continue
            reader = RecordingThreadReader.with_turn_status(case.thread, status)
            assert context.collect(case, reader).terminal_condition is not None

    exercise_native_evidence(assert_case)


def test_absent_native_thread_is_unusable() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        reader = RecordingThreadReader.without_thread()
        assert context.collect(case, reader).terminal_condition is not None
        assert len(reader.calls) == 1

    exercise_native_evidence(assert_case)


def test_absent_turns_are_unusable() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        reader = RecordingThreadReader.without_turns(case.thread)
        assert context.collect(case, reader).terminal_condition is not None

    exercise_native_evidence(assert_case)


def test_absent_completion_message_is_unusable() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        reader = RecordingThreadReader.without_completion_message(case.thread)
        assert context.collect(case, reader).terminal_condition is not None

    exercise_native_evidence(assert_case)


def test_multiple_listed_children_cannot_supply_single_child_evidence() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        reader = RecordingThreadReader.with_extra_child(case.thread)
        assert context.collect(case, reader).terminal_condition is not None
        assert len(reader.calls) == 1

    exercise_native_evidence(assert_case)


def test_unlisted_thread_cannot_supply_child_evidence() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        reader = RecordingThreadReader.without_listed_child(case.thread)
        assert context.collect(case, reader).terminal_condition is not None
        assert len(reader.calls) == 1

    exercise_native_evidence(assert_case)


def test_the_profile_execution_recipe_reads_no_disable_switch() -> None:
    entrypoint = Path(profile_execution_harness.__file__)

    assert modules_naming_a_switch((entrypoint,)) == ()
    assert modules_reading_the_switch_predicate((entrypoint,)) == ()
    assert not any(
        switch in native_profile_execution_recipe() for switch in AGENT_SWITCHES
    ), native_profile_execution_recipe()


def test_a_module_importing_the_predicate_is_reported(tmp_path: Path) -> None:
    reader = tmp_path / "reader.py"
    reader.write_text(
        f"from {DECLARING_MODULE_NAME} import codex_disabled_reason\n",
        encoding="utf-8",
    )

    assert modules_reading_the_switch_predicate((reader,)) == (reader,)


def test_a_module_reading_no_predicate_is_not_reported(tmp_path: Path) -> None:
    quiet = tmp_path / "quiet.py"
    quiet.write_text("VALUE = 1\n", encoding="utf-8")

    assert modules_reading_the_switch_predicate((quiet,)) == ()


def test_profile_execution_rows_cover_every_central_profile() -> None:
    selected = {(row.target, row.profile) for row in native_profile_rows()}

    assert selected == {
        (target, profile)
        for target, profiles in AGENT_PROFILES.items()
        for profile in profiles
    }


def test_a_non_python_path_is_refused_rather_than_scanned_as_empty(
    tmp_path: Path,
) -> None:
    not_source = tmp_path / "notes.txt"
    not_source.write_text("text\n", encoding="utf-8")

    with pytest.raises(NotAPythonSource):
        modules_naming_a_switch((not_source,))

    with pytest.raises(NotAPythonSource):
        modules_reading_the_switch_predicate((not_source,))


def test_a_single_offending_file_is_reported(tmp_path: Path) -> None:
    offender = tmp_path / "second_spelling.py"
    offender.write_text(f'VALUE = "{AGENT_SWITCHES[0]}"\n', encoding="utf-8")

    assert modules_naming_a_switch((offender,)) == (offender,)
