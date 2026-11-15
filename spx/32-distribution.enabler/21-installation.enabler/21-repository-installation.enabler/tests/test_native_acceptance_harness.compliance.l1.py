"""Compliance evidence for the native acceptance harness's names, fixtures, and unusable rows."""

import json
import string
import tomllib
from collections.abc import Sequence
from pathlib import Path

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.native_auditor_dispatch import (
    AUDITOR_PLUGIN,
    RESULT_BLOCKED_KEY,
    RESULT_RUN_TOKEN_KEY,
    RESULT_TERMINAL_CONDITION_KEY,
)
from outcomeeng_testing.harnesses.native_auditor_launch import (
    PLANTED_RUN_TOKEN,
    DispatchCall,
    LaunchReturn,
    native_auditor_launch,
)
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
)
from outcomeeng_testing.harnesses.native_profile_launch import (
    FORWARDED_TOOL_USE_ID,
    ParentStream,
    native_profile_launch,
)

CODEX_NAME_ALPHABET = frozenset(string.ascii_lowercase + string.digits + "_")
"""The characters Codex admits in an agent name: lowercase letters, digits, and underscores."""
SELECTED = sorted(CLAUDE_CREDENTIAL_VARIABLES)[0]


def launched_once[Call: DispatchCall](
    calls: Sequence[Call], launch_command: Sequence[str]
) -> Call:
    """The one recorded command that carries the row's whole launch command."""
    launches = [call for call in calls if set(launch_command) <= set(call.argv)]
    assert len(launches) == 1, launches
    return launches[0]


def front_matter_name(definition: Path) -> str:
    """The `name` a Markdown agent definition's front matter declares."""
    front_matter = definition.read_text("utf-8").split("---")[1]
    for line in front_matter.splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "name":
            return value.strip().strip('"')
    raise AssertionError(f"{definition} declares no name")


def test_every_codex_probe_definition_is_named_in_the_codex_alphabet_and_launched_by_that_name() -> (
    None
):
    with native_profile_launch({SELECTED}) as observation:
        codex_rows = [
            item
            for item in observation.rows
            if item.observation.row.target is Target.CODEX
        ]
        assert codex_rows
        for item in codex_rows:
            row = item.observation.row
            name = tomllib.loads(row.definition_path.read_text("utf-8"))["name"]
            assert name, row.identifier
            assert set(name) <= CODEX_NAME_ALPHABET, (row.identifier, name)
            launch = [
                call
                for call in item.calls
                if set(row.launch_commands[0]) <= set(call.argv)
            ]
            assert len(launch) == 1, row.identifier
            assert f"`{name}`" in launch[0].argv[-1], (row.identifier, launch[0].argv)


def test_every_auditor_row_launches_its_shipped_auditor_by_the_name_the_shipped_definition_registers() -> (
    None
):
    with native_auditor_launch({SELECTED}) as observation:
        assert {item.observation.row.target for item in observation.rows} == set(Target)
        for item in observation.rows:
            row = item.observation.row
            launch = launched_once(item.calls, row.launch_command)
            if row.target is Target.CODEX:
                selector = tomllib.loads(
                    row.shipped_definition_path.read_text("utf-8")
                )["name"]
            else:
                selector = (
                    f"{AUDITOR_PLUGIN}:{front_matter_name(row.shipped_definition_path)}"
                )
            assert f"`{selector}`" in " ".join(launch.argv), (
                row.identifier,
                launch.argv,
            )


def test_every_auditor_row_launches_with_its_fixture_committed_as_the_one_change_of_a_git_repository() -> (
    None
):
    with native_auditor_launch({SELECTED}) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            launch = launched_once(item.calls, row.launch_command)
            repository = launch.fixture_repository
            assert repository is not None, row.identifier
            assert repository.toplevel.exit_code == 0, (row.identifier, repository)
            assert Path(repository.toplevel.output).resolve() == (
                row.fixture_path.parent.resolve()
            ), row.identifier
            assert repository.base.exit_code == 0, (row.identifier, repository)
            assert repository.head.exit_code == 0, (row.identifier, repository)
            assert repository.base.output != repository.head.output, row.identifier
            assert repository.status.exit_code == 0, (row.identifier, repository)
            assert repository.status.output == "", (row.identifier, repository)
            assert repository.changed.exit_code == 0, (row.identifier, repository)
            assert repository.changed.output == f"A\t{row.fixture_path.name}", (
                row.identifier,
                repository,
            )


def test_a_profile_row_whose_parent_stream_shows_no_child_execution_is_failed() -> None:
    with native_profile_launch({SELECTED}, ParentStream.SILENT) as observation:
        assert {item.observation.row.target for item in observation.rows} == set(Target)
        for item in observation.rows:
            row = item.observation.row
            assert item.observation.launch_exit_code == 0, row.identifier
            assert item.observation.terminal_condition is not None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert (
                result["terminal_condition"] == item.observation.terminal_condition
            ), row.identifier


def test_a_claude_profile_row_whose_parent_forwards_one_child_execution_is_not_failed() -> (
    None
):
    with native_profile_launch({SELECTED}, ParentStream.FORWARDED_CHILD) as observation:
        claude_rows = [
            item
            for item in observation.rows
            if item.observation.row.target is Target.CLAUDE
        ]
        assert claude_rows
        for item in claude_rows:
            row = item.observation.row
            launch = [
                call
                for call in item.calls
                if set(row.launch_commands[0]) <= set(call.argv)
            ]
            assert len(launch) == 1, row.identifier
            requests = [
                json.loads(line) for line in (launch[0].input_text or "").splitlines()
            ]
            assert requests[0]["request"] == {
                "subtype": "initialize",
                "forwardSubagentText": True,
            }, row.identifier
            assert item.observation.terminal_condition is None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result["child_observation"] == {
                "forwarded_parent_tool_use_ids": [FORWARDED_TOOL_USE_ID]
            }, row.identifier


def test_an_auditor_row_whose_dispatch_returns_a_blocked_diagnostic_is_failed() -> None:
    with native_auditor_launch(
        {SELECTED}, returned=LaunchReturn.BLOCKED
    ) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            assert item.observation.launch_exit_code == 0, row.identifier
            assert item.observation.terminal_condition is not None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result[RESULT_BLOCKED_KEY] is True, row.identifier
            assert (
                result[RESULT_TERMINAL_CONDITION_KEY]
                == item.observation.terminal_condition
            ), row.identifier


def test_an_auditor_row_whose_dispatch_returns_no_run_token_is_failed() -> None:
    with native_auditor_launch(
        {SELECTED}, returned=LaunchReturn.UNSTRUCTURED
    ) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            assert item.observation.terminal_condition is not None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result[RESULT_RUN_TOKEN_KEY] is None, row.identifier
            assert result[RESULT_BLOCKED_KEY] is False, row.identifier


def test_an_auditor_row_whose_dispatch_returns_a_run_token_is_not_failed() -> None:
    with native_auditor_launch(
        {SELECTED}, returned=LaunchReturn.RUN_TOKEN
    ) as observation:
        assert observation.rows
        for item in observation.rows:
            row = item.observation.row
            assert item.observation.terminal_condition is None, row.identifier
            result = json.loads(row.result_path.read_text("utf-8"))
            assert result[RESULT_RUN_TOKEN_KEY] == PLANTED_RUN_TOKEN, row.identifier
