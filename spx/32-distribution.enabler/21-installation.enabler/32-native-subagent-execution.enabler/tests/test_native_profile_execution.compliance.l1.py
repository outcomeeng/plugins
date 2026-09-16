"""Compliance evidence for deterministic native-profile probe planning."""

from dataclasses import replace
from pathlib import Path

import pytest

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import CODEX_HOME_ENV
from outcomeeng.distribution.native_profile_execution import (
    NATIVE_PROFILE_OVERRIDE_ENVIRONMENT_VARIABLES,
    native_profile_rows,
)
from outcomeeng.validation.ci_gate import CODEX_API_KEY_ENVIRONMENT
from outcomeeng_testing.harnesses.discovery_auth import (
    API_LOGIN_FLAG,
    CREDENTIAL_ENVIRONMENTS,
    FILE_STORE_ARGS,
    WORKSPACE_LOGIN_FLAG,
    WORKSPACE_TOKEN_ENV,
    AuthenticationMode,
    NativeCommand,
)
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
)
from outcomeeng_testing.harnesses.native_profile_interactions import (
    native_profile_interactions,
)

from outcomeeng_testing.harnesses.discovery_auth_cases import NativeFault
from outcomeeng_testing.harnesses.native_profile_failures import native_profile_failure

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


@pytest.mark.parametrize("mode", list(AuthenticationMode), ids=str)
@pytest.mark.parametrize("claude_credential", CLAUDE_CREDENTIAL_VARIABLES)
def test_successful_rows_retain_artifacts_and_launch_once_without_overrides(
    mode: AuthenticationMode,
    claude_credential: str,
) -> None:
    with native_profile_interactions(mode, claude_credential) as observed:
        assert {item.row.identifier for item in observed.rows} == {
            row.identifier for row in native_profile_rows()
        }
        assert observed.environment == observed.original_environment
        for item in observed.rows:
            row = item.row
            assert item.terminal_condition is None
            parents = [
                call
                for call in observed.processes
                if Path(call.environment[CODEX_HOME_ENV]).parent
                == row.state_root.resolve()
                and call.argv[0] == row.launch_commands[0][0]
                and row.launch_commands[0][1] in call.argv
            ]
            assert len(parents) == 1
            parent = parents[0]
            assert not NATIVE_PROFILE_OVERRIDE_ENVIRONMENT_VARIABLES.intersection(
                parent.environment
            )
            assert parent.input_text is None
            assert parent.native_definition == row.definition_path.read_bytes()
            assert row.loading_path.is_file()
            assert row.result_path.is_file()
            assert not row.state_root.exists()
            children = [
                call
                for call in observed.children
                if Path(call.environment[CODEX_HOME_ENV]).parent
                == row.state_root.resolve()
            ]
            assert len(children) == (1 if row.target is Target.CODEX else 0)
            for child in children:
                assert child.cwd == parent.cwd
                assert child.environment == parent.environment
                assert all(argument in child.command for argument in FILE_STORE_ARGS)


@pytest.mark.parametrize("mode", list(AuthenticationMode), ids=str)
@pytest.mark.parametrize("claude_credential", CLAUDE_CREDENTIAL_VARIABLES)
def test_successful_rows_propagate_only_the_selected_credential_channel(
    mode: AuthenticationMode,
    claude_credential: str,
) -> None:
    with native_profile_interactions(mode, claude_credential) as observed:
        for item in observed.rows:
            assert item.terminal_condition is None
            row = item.row
            calls = [
                call
                for call in observed.processes
                if Path(call.environment[CODEX_HOME_ENV]).parent
                == row.state_root.resolve()
            ]
            parents = [
                call
                for call in calls
                if call.argv[0] == row.launch_commands[0][0]
                and row.launch_commands[0][1] in call.argv
            ]
            assert len(parents) == 1
            parent = parents[0]
            assert not CREDENTIAL_ENVIRONMENTS.intersection(parent.environment)
            selected = set(CLAUDE_CREDENTIAL_VARIABLES).intersection(parent.environment)
            if row.target is Target.CLAUDE:
                assert selected == {claude_credential}
                assert (
                    parent.environment[claude_credential]
                    == observed.original_environment[claude_credential]
                )
            else:
                assert selected == set()
                assert all(argument in parent.argv for argument in FILE_STORE_ARGS)
                logins = [call for call in calls if NativeCommand.LOGIN in call.argv]
                if mode is AuthenticationMode.SUBSCRIPTION:
                    assert logins == []
                else:
                    assert len(logins) == 1
                    flag, variable = (
                        (API_LOGIN_FLAG, CODEX_API_KEY_ENVIRONMENT)
                        if mode is AuthenticationMode.API
                        else (WORKSPACE_LOGIN_FLAG, WORKSPACE_TOKEN_ENV)
                    )
                    assert flag in logins[0].argv
                    assert (
                        logins[0].input_text == observed.original_environment[variable]
                    )
            for variable in (CODEX_API_KEY_ENVIRONMENT, WORKSPACE_TOKEN_ENV):
                credential = observed.original_environment[variable]
                assert all(
                    credential not in argument
                    for call in calls
                    for argument in call.argv
                )
                assert credential not in row.result_path.read_text(encoding="utf-8")


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
        assert reader.calls[0][0] == case.thread[ChildIdentityField.PARENT.value]
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
