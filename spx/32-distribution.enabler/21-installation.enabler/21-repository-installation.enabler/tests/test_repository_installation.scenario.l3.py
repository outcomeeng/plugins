"""Network-backed real-agent scenarios for repository installation."""

import json

import pytest

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_LOCAL_SCOPE,
    CLAUDE_PROJECT_SCOPE,
    ClaudeInstallRecord,
    FIRST_INSTALL_WARNING,
    ReportField,
    SPEC_TREE_PLUGIN,
)
from outcomeeng_testing.harnesses.installation import (
    MARKETPLACE,
    observe_codex_subagent_discovery,
    observe_real_first_install,
    observe_real_installation,
    observe_real_record_refresh,
)


def _first_install_warning(agent: Agent) -> str:
    """The bootstrap warning for one agent, named for this checkout's marketplace."""
    return FIRST_INSTALL_WARNING.format(
        marketplace=MARKETPLACE, agent=agent.value, plugin=SPEC_TREE_PLUGIN
    )


def test_real_agent_clis_bootstrap_empty_persistent_state() -> None:
    observation = observe_real_first_install()

    assert observation.initial_state == ()
    assert observation.initial_project_settings is not None
    assert observation.exit_code == 0, observation.stderr
    document = json.loads(observation.stdout)
    assert document[ReportField.CLAUDE_PLUGINS] == [SPEC_TREE_PLUGIN]
    assert document[ReportField.CODEX_PLUGINS] == [SPEC_TREE_PLUGIN]
    assert document[ReportField.WARNINGS] == [
        {
            ReportField.AGENT: agent.value,
            ReportField.MESSAGE: _first_install_warning(agent),
        }
        for agent in Agent
    ]
    assert observation.stderr.splitlines() == [
        f"warning: {_first_install_warning(agent)}" for agent in Agent
    ]
    assert observation.claude_listing_exit_code == 0, observation.claude_listing_stderr
    assert observation.codex_listing_exit_code == 0, observation.codex_listing_stderr
    assert observation.claude_plugins is not None
    assert observation.codex_plugins is not None
    assert observation.claude_plugins.installed == {SPEC_TREE_PLUGIN}
    assert observation.claude_plugins.enabled == {SPEC_TREE_PLUGIN}
    assert observation.codex_plugins.installed == {SPEC_TREE_PLUGIN}
    assert observation.codex_plugins.enabled == {SPEC_TREE_PLUGIN}


def test_real_agent_clis_place_home_agents_and_repeat_full_installation() -> None:
    observation = observe_real_installation()
    assert observation.first_exit_code == 0, observation.first_stderr
    assert observation.second_exit_code == 0, observation.second_stderr
    assert observation.claude_plugins_second == observation.claude_plugins_first
    assert observation.codex_plugins_second == observation.codex_plugins_first
    assert set(observation.placed_first) == (
        set(observation.placed_initial) | set(observation.shipped_agents)
    )
    assert observation.placed_first == observation.placed_second
    assert observation.unowned_first == observation.unowned_initial
    assert observation.unowned_second == observation.unowned_initial


def test_real_persistent_run_moves_a_second_checkout_record_without_entering_it() -> (
    None
):
    observation = observe_real_record_refresh()

    expected = {
        (SPEC_TREE_PLUGIN, CLAUDE_PROJECT_SCOPE, observation.invocation_checkout),
        (SPEC_TREE_PLUGIN, CLAUDE_LOCAL_SCOPE, observation.other_checkout),
    }
    recorded_before = {
        (record.plugin, record.scope, record.project_path)
        for record in observation.records_before
        if isinstance(record, ClaudeInstallRecord)
    }
    assert expected <= recorded_before
    assert observation.exit_code == 0, observation.stderr
    document = json.loads(observation.stdout)
    refreshed = {
        (
            record[ReportField.PLUGIN],
            record[ReportField.SCOPE],
            record[ReportField.PROJECT_PATH],
        )
        for record in document[ReportField.CLAUDE_RECORDS]
    }
    assert {(plugin, scope, str(path)) for plugin, scope, path in expected} <= refreshed
    assert {command[ReportField.CWD] for command in document[ReportField.COMMANDS]} == {
        str(observation.invocation_checkout)
    }
    target = document[ReportField.TARGET][ReportField.VERSIONS][SPEC_TREE_PLUGIN]
    after = {
        (record.plugin, record.scope, record.project_path): record.version
        for record in observation.records_after
        if isinstance(record, ClaudeInstallRecord)
    }
    assert after[
        (SPEC_TREE_PLUGIN, CLAUDE_LOCAL_SCOPE, observation.other_checkout)
    ] == (target)
    assert set(after) == {
        (record.plugin, record.scope, record.project_path)
        for record in observation.records_before
        if isinstance(record, ClaudeInstallRecord)
    }
    assert (
        observation.invocation_activation_after
        == observation.invocation_activation_before
    )
    assert observation.other_activation_after == observation.other_activation_before


@pytest.mark.live_subagent_discovery
def test_fresh_codex_session_discovers_every_placed_canonical_subagent() -> None:
    observation = observe_codex_subagent_discovery()

    assert observation.install_exit_code == 0, observation.install_stderr
    assert observation.login_exit_code == 0, observation.login_stderr
    assert observation.session_exit_code == 0, observation.session_stderr
    assert observation.placed_subagent_names
    assert observation.discovered_subagent_names is not None, (
        observation.session_last_message
    )
    assert observation.placed_subagent_names <= observation.discovered_subagent_names


def test_real_persistent_run_moves_records_at_differing_versions_to_one_version() -> (
    None
):
    observation = observe_real_record_refresh()
    before = {
        record: record.version
        for record in observation.records_before
        if isinstance(record, ClaudeInstallRecord) and record.plugin == SPEC_TREE_PLUGIN
    }
    after = {
        record: record.version
        for record in observation.records_after
        if isinstance(record, ClaudeInstallRecord) and record.plugin == SPEC_TREE_PLUGIN
    }
    assert before[observation.seeded_record] == observation.seeded_record.version
    assert len(set(before.values())) > 1
    assert observation.exit_code == 0, observation.stderr
    document = json.loads(observation.stdout)
    target = document[ReportField.TARGET][ReportField.VERSIONS][SPEC_TREE_PLUGIN]
    assert set(after.values()) == {target}
    assert after[observation.seeded_record] != observation.seeded_record.version
    assert document[ReportField.OFF_TARGET_RECORDS] == []

    reported = {
        (
            record[ReportField.PLUGIN],
            record[ReportField.SCOPE],
            record[ReportField.PROJECT_PATH],
        ): (record[ReportField.VERSION_BEFORE], record[ReportField.VERSION_AFTER])
        for record in document[ReportField.CLAUDE_RECORDS]
    }
    for record, version_after in after.items():
        key = (record.plugin, record.scope, str(record.project_path))
        assert reported[key] == (before[record], version_after), key


def test_real_run_moves_a_record_whose_directory_is_gone_and_exits_zero() -> None:
    observation = observe_real_record_refresh()

    assert not observation.gone_checkout.exists()
    assert observation.exit_code == 0, observation.stderr
    document = json.loads(observation.stdout)
    target = document[ReportField.TARGET][ReportField.VERSIONS][SPEC_TREE_PLUGIN]
    gone = {
        record: record.version
        for record in observation.records_after
        if isinstance(record, ClaudeInstallRecord)
        and record.project_path == observation.gone_checkout
    }
    assert len(gone) == 1
    assert set(gone.values()) == {target}
    assert observation.seeded_record in {
        record
        for record in observation.records_after
        if isinstance(record, ClaudeInstallRecord)
    }
    assert not any(
        str(observation.gone_checkout) == command[ReportField.CWD]
        for command in document[ReportField.COMMANDS]
    )


def test_real_second_run_reports_records_refreshed_at_unchanged_versions() -> None:
    observation = observe_real_record_refresh()
    assert observation.second_exit_code == 0, observation.second_stderr
    document = json.loads(observation.second_stdout)
    records = document[ReportField.CLAUDE_RECORDS]
    assert len(records) >= 1
    assert all(
        record[ReportField.VERSION_AFTER] == record[ReportField.VERSION_BEFORE]
        for record in records
    )
    assert set(observation.records_after_second) == set(observation.records_after)
    assert {
        record.version
        for record in observation.records_after_second
        if isinstance(record, ClaudeInstallRecord)
    } == {
        record.version
        for record in observation.records_after
        if isinstance(record, ClaudeInstallRecord)
    }
