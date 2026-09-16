"""Installation evidence grouped by its governing contract."""

from typing import cast
from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    CLAUDE_SCOPE_FLAG,
    Operation,
    ReportField,
    marketplace_plugin_name,
)
from pathlib import Path
from outcomeeng_testing.generators.installation import RecordDisposition
from outcomeeng_testing.harnesses.installation import observe_record_refresh_plan


def test_persistent_run_updates_every_recorded_checkout_and_reinstalls_nothing() -> (
    None
):
    observation = observe_record_refresh_plan()
    claude_commands = [
        command
        for command in observation.plan.commands
        if command.agent is Agent.CLAUDE
    ]
    updates = [
        command
        for command in claude_commands
        if command.operation is Operation.PLUGIN_UPDATE
    ]
    expected = {
        (
            marketplace_plugin_name(entry[CLAUDE_PLUGIN_ID_FIELD]),
            entry[CLAUDE_PLUGIN_SCOPE_FIELD],
            Path(entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]),
        )
        for entry, disposition in observation.cases
        if disposition is RecordDisposition.UPDATE
    }

    assert not any(
        command.operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}
        for command in claude_commands
    )
    assert {(command.plugin, command.argv[-1], command.cwd) for command in updates} == (
        expected
    )
    assert len(updates) == len(expected)
    assert all(command.argv[-2] == CLAUDE_SCOPE_FLAG for command in updates)
    assert observation.attempted[-len(observation.plan.commands) :] == (
        observation.plan.commands
    )
    assert {
        (
            record[ReportField.PLUGIN],
            record[ReportField.SCOPE],
            Path(cast(str, record[ReportField.PROJECT_PATH])),
        )
        for record in cast(
            list[dict[str, str]], observation.document[ReportField.CLAUDE_RECORDS]
        )
    } == expected
