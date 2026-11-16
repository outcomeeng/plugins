"""Compliance evidence for the native auditor-dispatch row lifecycle."""

import hashlib
import json
import tomllib
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

import pytest

from outcomeeng.distribution.agents import AGENT_TOOLS_FIELD, ALL_TOOLS_SENTINEL
from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import CODEX_HOME_CONFIG_PATH, CODEX_HOME_ENV
from outcomeeng.distribution.native_auditor_dispatch import (
    AUDITOR_FIXTURES,
    CLAUDE_ADD_DIRECTORY_OPTION,
    CLAUDE_ALLOWED_TOOLS_OPTION,
    CLAUDE_ALLOWED_TOOLS_SEPARATOR,
    CODEX_SANDBOX_WORKSPACE_WRITE_TABLE,
    CODEX_STRICT_CONFIG_OPTION,
    CODEX_WORKSPACE_WRITE_OPTIONS,
    CODEX_WRITABLE_ROOTS_KEY,
    CONFIGURATION_SHIPPED_SHA256_KEY,
    RESULT_BLOCKED_KEY,
    RESULT_PROJECTION_KEY,
    RESULT_RUN_FILE_KEY,
    RESULT_RUN_TOKEN_KEY,
    RESULT_TERMINAL_CONDITION_KEY,
    SCRATCH_ENVIRONMENT_VARIABLES,
    native_auditor_rows,
    record_native_auditor_failure,
)
from outcomeeng_testing.generators.native_auditor_dispatch import (
    UnboundedGrant,
    generated_preserved_codex_configs,
    generated_sandbox_table_configs,
    generated_unparseable_codex_configs,
)
from outcomeeng_testing.harnesses.agent_conversion import agent_document_oracle
from outcomeeng_testing.harnesses.discovery_auth import CREDENTIAL_ENVIRONMENTS
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NATIVE_FAILURE_EXIT_CODE,
    NativeFault,
)
from outcomeeng_testing.harnesses.installation import repository_root
from outcomeeng_testing.harnesses.native_auditor_launch import (
    PLANTED_PROJECTION,
    PLANTED_PROJECTION_QUOTING_BLOCKED,
    PLANTED_RUN_FILE,
    PLANTED_RUN_FILE_NAME,
    PLANTED_RUN_TOKEN,
    LaunchReturn,
    claude_definition_plant,
    codex_config_plant,
    native_auditor_failure,
    native_auditor_launch,
    native_auditor_without_codex_home,
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
CODEX_WORKSPACE_WRITE_PAIRS = tuple(
    zip(
        CODEX_WORKSPACE_WRITE_OPTIONS[::2],
        CODEX_WORKSPACE_WRITE_OPTIONS[1::2],
        strict=True,
    )
)
"""The Codex parent's sandbox and approval options, each paired with its value."""


def option_values(argv: Sequence[str], option: str) -> list[str]:
    """The value after every occurrence of `option` in a command."""
    return [argv[index + 1] for index, word in enumerate(argv[:-1]) if word == option]


def definition_tool_grants(definition: Path) -> tuple[str, ...]:
    """The `tools` grants a Markdown agent definition declares, read through PyYAML."""
    tools = agent_document_oracle(definition).frontmatter[AGENT_TOOLS_FIELD]
    assert isinstance(tools, str), definition
    return tuple(grant.strip() for grant in tools.split(","))


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
                assert result[RESULT_PROJECTION_KEY] == PLANTED_PROJECTION, (
                    row.identifier
                )
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


def test_dispatch_success_derives_from_the_rendered_projection_whatever_prose_surrounds_it() -> (
    None
):
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    with native_auditor_launch(
        {selected}, returned=LaunchReturn.PROJECTION_ONLY
    ) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            assert item.observation.terminal_condition is None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result[RESULT_RUN_TOKEN_KEY] == PLANTED_RUN_TOKEN, row.identifier
            assert result[RESULT_RUN_FILE_KEY] == PLANTED_RUN_FILE_NAME, row.identifier
            assert result[RESULT_BLOCKED_KEY] is False, row.identifier


def test_the_run_file_is_recovered_from_a_reply_that_names_no_label() -> None:
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    with native_auditor_launch(
        {selected}, returned=LaunchReturn.FREE_FORM
    ) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            assert item.observation.terminal_condition is None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result[RESULT_RUN_TOKEN_KEY] == PLANTED_RUN_TOKEN, row.identifier
            assert result[RESULT_RUN_FILE_KEY] == PLANTED_RUN_FILE, row.identifier
            assert result[RESULT_PROJECTION_KEY] == PLANTED_PROJECTION, row.identifier


def test_a_rendered_projection_that_quotes_the_blocked_word_is_not_a_blocked_result() -> (
    None
):
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    with native_auditor_launch(
        {selected}, returned=LaunchReturn.PROJECTION_QUOTING_BLOCKED
    ) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            assert item.observation.terminal_condition is None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result[RESULT_BLOCKED_KEY] is False, row.identifier
            assert result[RESULT_RUN_TOKEN_KEY] == PLANTED_RUN_TOKEN, row.identifier
            assert result[RESULT_RUN_FILE_KEY] == PLANTED_RUN_FILE_NAME, row.identifier
            assert result[RESULT_PROJECTION_KEY] == (
                PLANTED_PROJECTION_QUOTING_BLOCKED
            ), row.identifier


def test_a_reply_without_a_rendered_projection_or_blocked_diagnostic_records_a_terminal_condition() -> (
    None
):
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    with native_auditor_launch(
        {selected}, returned=LaunchReturn.UNSTRUCTURED
    ) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            assert item.observation.terminal_condition is not None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result[RESULT_RUN_TOKEN_KEY] is None, row.identifier
            assert result[RESULT_PROJECTION_KEY] is None, row.identifier


def test_a_failure_recorded_after_a_dispatch_retains_every_field_the_dispatch_captured() -> (
    None
):
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    condition = uuid4().hex
    with native_auditor_launch({selected}) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            captured = json.loads(row.result_path.read_text("utf-8"))
            failure = record_native_auditor_failure(
                row, condition, install_exit_code=NATIVE_FAILURE_EXIT_CODE
            )
            retained = json.loads(row.result_path.read_text("utf-8"))
            assert retained.keys() >= captured.keys(), row.identifier
            assert {
                key: retained[key]
                for key in captured
                if key != RESULT_TERMINAL_CONDITION_KEY
            } == {
                key: value
                for key, value in captured.items()
                if key != RESULT_TERMINAL_CONDITION_KEY
            }, row.identifier
            assert retained[RESULT_TERMINAL_CONDITION_KEY] == condition, row.identifier
            assert failure.terminal_condition == condition, row.identifier
            assert failure.install_exit_code == NATIVE_FAILURE_EXIT_CODE, row.identifier
            assert failure.launch_exit_code == item.observation.launch_exit_code, (
                row.identifier
            )


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


def test_each_auditor_parent_reaches_the_fixture_repository_and_scratch_directory_and_approves_exactly_the_definition_grants() -> (
    None
):
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    with native_auditor_launch({selected}) as observation:
        assert {item.observation.row.target for item in observation.rows} == set(Target)
        for item in observation.rows:
            row = item.observation.row
            launches = [
                call for call in item.calls if set(row.launch_command) <= set(call.argv)
            ]
            assert len(launches) == 1, row.identifier
            launch = launches[0]
            repository = row.fixture_path.parent
            scratch = launch.environment[SCRATCH_ENVIRONMENT_VARIABLES[0]]
            assert {
                launch.environment[name] for name in SCRATCH_ENVIRONMENT_VARIABLES
            } == {scratch}, row.identifier
            scratch_path = Path(scratch)
            assert scratch_path.relative_to(row.state_root) in launch.directories, (
                row.identifier
            )
            assert not scratch_path.is_relative_to(repository), row.identifier
            access_roots = [str(repository), scratch]
            if row.target is Target.CLAUDE:
                assert (
                    option_values(launch.argv, CLAUDE_ADD_DIRECTORY_OPTION)
                    == access_roots
                ), (row.identifier, launch.argv)
                allowed = option_values(launch.argv, CLAUDE_ALLOWED_TOOLS_OPTION)
                assert len(allowed) == 1, (row.identifier, launch.argv)
                assert tuple(
                    allowed[0].split(CLAUDE_ALLOWED_TOOLS_SEPARATOR)
                ) == definition_tool_grants(row.shipped_definition_path), row.identifier
            else:
                for option, value in CODEX_WORKSPACE_WRITE_PAIRS:
                    assert value in option_values(launch.argv, option), (
                        row.identifier,
                        launch.argv,
                    )
                assert CODEX_STRICT_CONFIG_OPTION in launch.argv, (
                    row.identifier,
                    launch.argv,
                )
                assert launch.codex_config is not None, row.identifier
                configuration = tomllib.loads(launch.codex_config.decode("utf-8"))
                assert set(access_roots) <= set(
                    configuration[CODEX_SANDBOX_WORKSPACE_WRITE_TABLE][
                        CODEX_WRITABLE_ROOTS_KEY
                    ]
                ), (row.identifier, configuration)


def test_each_claude_add_dir_takes_exactly_one_path_and_allowed_tools_follows_the_last_as_its_own_option() -> (
    None
):
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    with native_auditor_launch({selected}, target=Target.CLAUDE) as observation:
        assert {item.observation.row.target for item in observation.rows} == {
            Target.CLAUDE
        }
        for item in observation.rows:
            row = item.observation.row
            launches = [
                call for call in item.calls if set(row.launch_command) <= set(call.argv)
            ]
            assert len(launches) == 1, row.identifier
            argv = launches[0].argv
            scratch = launches[0].environment[SCRATCH_ENVIRONMENT_VARIABLES[0]]
            positions = [
                index
                for index, word in enumerate(argv)
                if word == CLAUDE_ADD_DIRECTORY_OPTION
            ]
            assert [argv[index + 1] for index in positions] == [
                str(row.fixture_path.parent),
                scratch,
            ], (row.identifier, argv)
            for index in positions:
                assert argv[index + 2 : index + 3] in {
                    (CLAUDE_ADD_DIRECTORY_OPTION,),
                    (CLAUDE_ALLOWED_TOOLS_OPTION,),
                }, (row.identifier, argv)
            assert argv.count(CLAUDE_ALLOWED_TOOLS_OPTION) == 1, (row.identifier, argv)
            assert argv.index(CLAUDE_ALLOWED_TOOLS_OPTION) == positions[-1] + 2, (
                row.identifier,
                argv,
            )


def test_a_codex_row_without_a_selected_codex_home_launches_no_parent_and_records_the_refusal() -> (
    None
):
    with native_auditor_without_codex_home() as observation:
        assert CODEX_HOME_ENV not in observation.environment
        assert {item.row.target for item in observation.rows} == {Target.CODEX}
        assert observation.launches == ()
        for item in observation.rows:
            row = item.row
            assert item.launch_exit_code is None, row.identifier
            assert item.terminal_condition is not None, row.identifier
            assert CODEX_HOME_ENV in item.terminal_condition, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result[RESULT_TERMINAL_CONDITION_KEY] == item.terminal_condition
            assert result.get(RESULT_RUN_TOKEN_KEY) is None, row.identifier
            assert result.get(RESULT_PROJECTION_KEY) is None, row.identifier


def test_a_codex_row_whose_config_does_not_parse_or_already_holds_the_sandbox_table_launches_no_parent_and_records_the_refusal() -> (
    None
):
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    unparseable = generated_unparseable_codex_configs()
    holding_table = generated_sandbox_table_configs()
    for text in unparseable:
        with pytest.raises(tomllib.TOMLDecodeError):
            tomllib.loads(text)
    for text in holding_table:
        assert CODEX_SANDBOX_WORKSPACE_WRITE_TABLE in tomllib.loads(text), text
    for text in (*unparseable, *holding_table):
        with native_auditor_launch(
            {selected}, target=Target.CODEX, plant=codex_config_plant(text)
        ) as observation:
            assert {item.observation.row.target for item in observation.rows} == {
                Target.CODEX
            }
            for item in observation.rows:
                row = item.observation.row
                assert not [
                    call
                    for call in item.calls
                    if set(row.launch_command) <= set(call.argv)
                ], (row.identifier, text)
                assert item.calls, row.identifier
                last = item.calls[-1]
                assert last.codex_config == text.encode("utf-8"), row.identifier
                assert item.observation.launch_exit_code is None, row.identifier
                condition = item.observation.terminal_condition
                assert condition is not None, (row.identifier, text)
                assert str(last.home / CODEX_HOME_CONFIG_PATH) in condition, condition
                result = json.loads(row.result_path.read_text("utf-8"))
                assert result[RESULT_TERMINAL_CONDITION_KEY] == condition
                assert result.get(RESULT_RUN_TOKEN_KEY) is None, row.identifier
                assert result.get(RESULT_PROJECTION_KEY) is None, row.identifier


def test_naming_the_writable_roots_keeps_every_entry_the_codex_config_held_before() -> (
    None
):
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    for text in generated_preserved_codex_configs():
        held = tomllib.loads(text)
        assert held, text
        assert CODEX_SANDBOX_WORKSPACE_WRITE_TABLE not in held, text
        with native_auditor_launch(
            {selected}, target=Target.CODEX, plant=codex_config_plant(text)
        ) as observation:
            assert {item.observation.row.target for item in observation.rows} == {
                Target.CODEX
            }
            for item in observation.rows:
                row = item.observation.row
                launches = [
                    call
                    for call in item.calls
                    if set(row.launch_command) <= set(call.argv)
                ]
                assert len(launches) == 1, row.identifier
                launch = launches[0]
                assert item.observation.terminal_condition is None, row.identifier
                assert launch.codex_config is not None, row.identifier
                scratch = launch.environment[SCRATCH_ENVIRONMENT_VARIABLES[0]]
                configuration = tomllib.loads(launch.codex_config.decode("utf-8"))
                assert {
                    key: value
                    for key, value in configuration.items()
                    if key != CODEX_SANDBOX_WORKSPACE_WRITE_TABLE
                } == held, (row.identifier, text)
                assert {str(row.fixture_path.parent), scratch} <= set(
                    configuration[CODEX_SANDBOX_WORKSPACE_WRITE_TABLE][
                        CODEX_WRITABLE_ROOTS_KEY
                    ]
                ), (row.identifier, configuration)


def test_a_claude_row_whose_definition_declares_no_tools_grant_or_grants_every_tool_launches_no_parent_and_records_that(
    tmp_path: Path,
) -> None:
    selected = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]
    for grant in UnboundedGrant:
        with native_auditor_launch(
            {selected}, target=Target.CLAUDE, plant=claude_definition_plant(grant)
        ) as observation:
            assert {item.observation.row.target for item in observation.rows} == {
                Target.CLAUDE
            }
            for item in observation.rows:
                row = item.observation.row
                assert item.calls, row.identifier
                planted = tmp_path / f"{grant.value}-{row.identifier}.md"
                planted.write_bytes(
                    item.calls[-1].state_files[
                        row.native_definition_path.relative_to(row.state_root)
                    ]
                )
                tools = agent_document_oracle(planted).frontmatter.get(
                    AGENT_TOOLS_FIELD
                )
                assert not tools or tools == ALL_TOOLS_SENTINEL, (grant, tools)
                assert not [
                    call
                    for call in item.calls
                    if set(row.launch_command) <= set(call.argv)
                ], (grant, row.identifier)
                assert item.observation.launch_exit_code is None, row.identifier
                condition = item.observation.terminal_condition
                assert condition is not None, (grant, row.identifier)
                assert str(row.native_definition_path) in condition, condition
                result = json.loads(row.result_path.read_text("utf-8"))
                assert result[RESULT_TERMINAL_CONDITION_KEY] == condition
                assert result.get(RESULT_RUN_TOKEN_KEY) is None, row.identifier
                assert result.get(RESULT_PROJECTION_KEY) is None, row.identifier
