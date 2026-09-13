"""Compliance evidence for deterministic native-profile probe planning."""

import json
from dataclasses import replace

from outcomeeng_testing.harnesses.discovery_auth_cases import NativeFault
from outcomeeng_testing.harnesses.native_profile_failures import native_profile_failure

from outcomeeng.distribution.native_thread_evidence import (
    THREAD_READ_FAILED,
    ChildIdentityField,
    NativeTurnStatus,
)
from outcomeeng_testing.generators.native_thread_evidence import NativeEvidenceCase
from outcomeeng_testing.harnesses.native_thread_evidence import (
    NativeEvidenceContext,
    RecordingThreadReader,
    exercise_native_evidence,
    read_absent_native_thread,
    read_absent_native_child,
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


def test_real_native_read_reports_absent_thread_without_launching_a_turn() -> None:
    result = read_absent_native_thread()
    assert result.exit_code != 0
    assert THREAD_READ_FAILED in result.stderr


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


def test_real_native_child_listing_retains_empty_pages_without_launching() -> None:
    result = read_absent_native_child()
    assert result.exit_code == 0
    assert json.loads(result.stdout)["childIds"] == []
    assert all("result" in page for page in json.loads(result.stdout)["pages"])
