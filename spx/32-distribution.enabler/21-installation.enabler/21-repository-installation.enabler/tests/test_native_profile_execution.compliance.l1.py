"""Compliance evidence for deterministic native-profile probe planning."""

from collections.abc import Mapping
from dataclasses import replace

from outcomeeng_testing.harnesses.discovery_auth import CREDENTIAL_ENVIRONMENTS
from outcomeeng_testing.harnesses.discovery_auth_cases import NativeFault
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
    NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES,
)
from outcomeeng_testing.harnesses.native_profile_failures import native_profile_failure
from outcomeeng_testing.harnesses.native_profile_launch import native_profile_launch

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.native_profile_execution import native_profile_rows

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


def test_no_native_process_inherits_an_ambient_override_or_an_unselected_credential() -> (
    None
):
    stripped = (
        NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES
        | CLAUDE_CREDENTIAL_VARIABLES
        | CREDENTIAL_ENVIRONMENTS
    )
    with native_profile_failure(NativeFault.INSTALL_FAILURE) as observation:
        assert stripped <= observation.environment.keys()
        assert len(observation.calls) == len(observation.rows)
        for call in observation.calls:
            assert not stripped & call.environment.keys(), call.argv


def test_every_row_launches_its_child_once_passing_only_the_selected_credential() -> (
    None
):
    strippable = (
        NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES
        | CLAUDE_CREDENTIAL_VARIABLES
        | CREDENTIAL_ENVIRONMENTS
    )
    for selected in sorted(CLAUDE_CREDENTIAL_VARIABLES):
        with native_profile_launch({selected}) as observation:
            assert strippable - CLAUDE_CREDENTIAL_VARIABLES | {selected} <= (
                observation.environment.keys()
            )
            assert len(observation.rows) == len(native_profile_rows())
            for item in observation.rows:
                row = item.observation.row
                launches = [
                    call
                    for call in item.calls
                    if set(row.launch_commands[0]) <= set(call.argv)
                ]
                assert len(launches) == 1, (row.identifier, launches)
                launch = launches[0]
                assert item.observation.launch_exit_code == 0, row.identifier
                assert row.definition_path.is_file()
                assert row.loading_path.is_file()
                assert row.result_path.is_file()
                assert not row.state_root.exists()
                if row.target is Target.CLAUDE:
                    assert launch.environment.keys() & strippable == {selected}
                    assert (
                        launch.environment[selected]
                        == observation.environment[selected]
                    )
                else:
                    assert not launch.environment.keys() & strippable, row.identifier
                for call in item.calls:
                    if call is not launch:
                        assert not call.environment.keys() & strippable, call.argv


def test_an_ambiguous_claude_credential_fails_its_row_without_a_launch() -> None:
    with native_profile_launch(CLAUDE_CREDENTIAL_VARIABLES) as observation:
        assert CLAUDE_CREDENTIAL_VARIABLES <= observation.environment.keys()
        assert {item.observation.row.target for item in observation.rows} == set(Target)
        for item in observation.rows:
            row = item.observation.row
            launches = [
                call
                for call in item.calls
                if set(row.launch_commands[0]) <= set(call.argv)
            ]
            if row.target is Target.CLAUDE:
                assert item.observation.terminal_condition is not None
                assert item.observation.launch_exit_code is None
                assert not launches, row.identifier
                assert row.result_path.is_file()
            else:
                assert len(launches) == 1, row.identifier


def test_native_child_read_retains_correlated_configuration_and_completion() -> None:
    def assert_case(case: NativeEvidenceCase, context: NativeEvidenceContext) -> None:
        reader = RecordingThreadReader.from_thread(case.thread)
        result = context.collect(case, reader)
        thread: Mapping[str, object] = case.thread
        assert result.terminal_condition is None
        assert result.thread == case.thread
        assert len(reader.calls) == 1
        assert reader.calls[0][0] == thread[ChildIdentityField.PARENT]
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
