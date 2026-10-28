"""Compliance evidence for the native auditor-dispatch row lifecycle."""

import hashlib
import json

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.native_auditor_dispatch import (
    AUDITOR_FIXTURES,
    CONFIGURATION_SHIPPED_SHA256_KEY,
    RESULT_BLOCKED_KEY,
    RESULT_RUN_FILE_KEY,
    RESULT_RUN_TOKEN_KEY,
    RESULT_TERMINAL_CONDITION_KEY,
    native_auditor_rows,
)
from outcomeeng_testing.harnesses.discovery_auth import CREDENTIAL_ENVIRONMENTS
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NATIVE_FAILURE_EXIT_CODE,
    NativeFault,
)
from outcomeeng_testing.harnesses.installation import repository_root
from outcomeeng_testing.harnesses.native_auditor_launch import (
    PLANTED_RUN_FILE,
    PLANTED_RUN_TOKEN,
    LaunchReturn,
    native_auditor_failure,
    native_auditor_launch,
)
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
    NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES,
)

STRIPPABLE = (
    NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES
    | CLAUDE_CREDENTIAL_VARIABLES
    | CREDENTIAL_ENVIRONMENTS
)


def test_every_row_launches_once_from_the_shipped_definition_passing_only_the_selected_credential() -> (
    None
):
    for selected in sorted(CLAUDE_CREDENTIAL_VARIABLES):
        with native_auditor_launch({selected}) as observation:
            assert STRIPPABLE - CLAUDE_CREDENTIAL_VARIABLES | {selected} <= (
                observation.environment.keys()
            )
            assert len(observation.rows) == len(native_auditor_rows(repository_root()))
            for item in observation.rows:
                row = item.observation.row
                launches = [
                    call
                    for call in item.calls
                    if set(row.launch_command) <= set(call.argv)
                ]
                assert len(launches) == 1, (row.identifier, launches)
                launch = launches[0]
                assert item.observation.launch_exit_code == 0, row.identifier
                assert item.calls[-1] is launch
                assert row.native_name in " ".join(launch.argv)
                assert str(row.fixture_path) in " ".join(launch.argv)
                assert launch.state_files[
                    row.native_definition_path.relative_to(row.state_root)
                ] == (row.shipped_definition_path.read_bytes())
                assert (
                    launch.state_files[
                        row.fixture_path.relative_to(row.state_root)
                    ].decode("utf-8")
                    == (AUDITOR_FIXTURES[row.auditor][1])
                )
                configuration = json.loads(row.configuration_path.read_text("utf-8"))
                assert configuration[CONFIGURATION_SHIPPED_SHA256_KEY] == (
                    hashlib.sha256(row.shipped_definition_path.read_bytes()).hexdigest()
                )
                assert row.loading_path.is_file()
                assert row.result_path.is_file()
                assert item.observation.terminal_condition is None, row.identifier
                result = json.loads(row.result_path.read_text("utf-8"))
                assert result[RESULT_TERMINAL_CONDITION_KEY] is None, row.identifier
                assert result[RESULT_RUN_TOKEN_KEY] == PLANTED_RUN_TOKEN, row.identifier
                assert result[RESULT_RUN_FILE_KEY] == PLANTED_RUN_FILE, row.identifier
                assert result[RESULT_BLOCKED_KEY] is False, row.identifier
                assert not row.state_root.exists()
                if row.target is Target.CLAUDE:
                    assert launch.environment.keys() & STRIPPABLE == {selected}
                    assert (
                        launch.environment[selected]
                        == observation.environment[selected]
                    )
                else:
                    assert not launch.environment.keys() & STRIPPABLE, row.identifier
                    assert launch.saved_login == observation.saved_login, row.identifier
                for call in item.calls:
                    if call is not launch:
                        assert not call.environment.keys() & STRIPPABLE, call.argv


def test_a_blocked_dispatch_diagnostic_is_a_returned_result_without_a_terminal_condition() -> (
    None
):
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    with native_auditor_launch(
        {selected}, returned=LaunchReturn.BLOCKED
    ) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            assert item.observation.launch_exit_code == 0, row.identifier
            assert item.observation.terminal_condition is None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result[RESULT_BLOCKED_KEY] is True, row.identifier
            assert result[RESULT_RUN_TOKEN_KEY] is None, row.identifier
            assert result[RESULT_RUN_FILE_KEY] is None, row.identifier
            assert result[RESULT_TERMINAL_CONDITION_KEY] is None, row.identifier


def test_a_failed_launch_records_its_terminal_condition_without_a_retry() -> None:
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    with native_auditor_launch({selected}, NATIVE_FAILURE_EXIT_CODE) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            launches = [
                call for call in item.calls if set(row.launch_command) <= set(call.argv)
            ]
            assert len(launches) == 1, row.identifier
            assert item.calls[-1] is launches[0]
            assert item.observation.launch_exit_code == NATIVE_FAILURE_EXIT_CODE
            assert item.observation.terminal_condition is not None
            result = json.loads(row.result_path.read_text("utf-8"))
            assert (
                result[RESULT_TERMINAL_CONDITION_KEY]
                == item.observation.terminal_condition
            )
            assert (
                launches[0].state_files[
                    row.native_definition_path.relative_to(row.state_root)
                ]
                == row.shipped_definition_path.read_bytes()
            )
            assert not row.state_root.exists()


def test_a_missing_or_ambiguous_claude_credential_fails_its_row_without_a_launch() -> (
    None
):
    for planted in (frozenset(), CLAUDE_CREDENTIAL_VARIABLES):
        with native_auditor_launch(planted) as observation:
            assert {item.observation.row.target for item in observation.rows} == set(
                Target
            )
            for item in observation.rows:
                row = item.observation.row
                launches = [
                    call
                    for call in item.calls
                    if set(row.launch_command) <= set(call.argv)
                ]
                if row.target is Target.CLAUDE:
                    assert item.observation.terminal_condition is not None
                    assert item.observation.launch_exit_code is None
                    assert not launches, row.identifier
                    assert row.result_path.is_file()
                else:
                    assert len(launches) == 1, row.identifier


def test_a_failed_or_timed_out_installation_retains_evidence_and_does_not_launch() -> (
    None
):
    for fault in (NativeFault.INSTALL_FAILURE, NativeFault.TIMEOUT):
        with native_auditor_failure(fault) as observation:
            assert len(observation.calls) == len(observation.rows)
            for item in observation.rows:
                assert item.terminal_condition is not None
                assert item.launch_exit_code is None
                assert item.row.configuration_path.is_file()
                assert item.row.loading_path.is_file()
                assert item.row.result_path.is_file()
                assert not item.row.state_root.exists()
            for call in observation.calls:
                assert not any(
                    set(item.row.launch_command) <= set(call.argv)
                    for item in observation.rows
                ), call.argv
