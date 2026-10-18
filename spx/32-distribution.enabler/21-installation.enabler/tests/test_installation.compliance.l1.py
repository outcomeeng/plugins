"""State-boundary and failure evidence for repository installation."""

import json
import tempfile
import tomllib
from pathlib import Path
from typing import cast

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import (
    CLAUDE_CATALOG_PATH,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    CLAUDE_PROJECT_SCOPE,
    CLAUDE_REFRESH_SCOPES,
    CLAUDE_SCOPE_BEARING_OPERATIONS,
    CLAUDE_SCOPELESS_OPERATIONS,
    CLAUDE_SCOPE_FLAG,
    CLAUDE_INSTALLED_PLUGINS_FIELD,
    CLAUDE_PLUGIN_VERSION_FIELD,
    CODEX_CONFIG_PATH,
    CODEX_HOME_ENV,
    FETCH_PROJECT_PREFIX,
    FIRST_INSTALL_WARNING,
    InstallationMode,
    Operation,
    ReportField,
    SPEC_TREE_PLUGIN,
    STATE_ENV_NAMES,
    marketplace_plugin_identifier,
    marketplace_plugin_name,
)
from outcomeeng_testing.generators.installation import (
    ClosingDisposition,
    RecordDisposition,
    generated_boolean_states,
    UNCACHED_OTHER_CHECKOUT_STATE,
)
from outcomeeng_testing.harnesses.installation import (
    RegistryState,
    absent_from_every_agent,
    captured_non_pending_failure_wordings,
    committed_catalog_plugin_names,
    install_record_fixture_path,
    observe_codex_config_independence,
    observe_designated_failure,
    observe_empty_selection_execution,
    observe_racing_install_record_rewrite,
    observe_first_failure,
    observe_inspection_failure,
    observe_invalid_persistent_selections,
    observe_missing_codex_home,
    observe_persistent_execution,
    observe_persistent_plan,
    observe_record_refresh_plan,
    observe_repository_plan,
    observe_uncached_fetch,
    observe_unpublished_plugin,
    observe_unreadable_source,
)


def committed_marketplace_name() -> str:
    """The marketplace name read from the raw committed catalog."""
    catalog = json.loads(
        (Path(__file__).resolve().parents[4] / CLAUDE_CATALOG_PATH).read_text(
            encoding="utf-8"
        )
    )
    return cast("str", catalog["name"])


def test_every_command_uses_the_explicit_checkout_and_agent_homes() -> None:
    observation = observe_repository_plan()

    assert observation.plan.commands
    assert all(
        command.cwd == observation.plan.roots.checkout
        for command in observation.plan.commands
    )
    assert all(
        set(STATE_ENV_NAMES) <= set(dict(command.environment))
        for command in observation.plan.commands
    )
    assert all(
        value not in observation.ambient_state_values
        for command in observation.plan.commands
        for name, value in command.environment
        if name in STATE_ENV_NAMES
    )
    state_root = observation.plan.roots.state
    assert state_root is not None
    assert all(
        all(
            Path(value).is_relative_to(state_root)
            for name, value in command.environment
            if name in STATE_ENV_NAMES
        )
        for command in observation.plan.commands
    )


def test_persistent_installation_requires_selected_codex_home() -> None:
    error = observe_missing_codex_home()

    assert error is not None
    assert CODEX_HOME_ENV in error


def test_persistent_commands_use_project_scope_and_selected_codex_home() -> None:
    refreshing = observe_persistent_execution()
    registering = observe_persistent_plan(claude_marketplace_listed=False)
    bootstrapping = observe_persistent_plan(
        installed={agent: frozenset() for agent in Target},
    )
    plans = (refreshing.report.plan, registering.plan, bootstrapping.plan)
    claude_commands = [
        command
        for plan in plans
        for command in (*plan.commands, *plan.closing)
        if command.agent is Target.CLAUDE
    ]
    codex_commands = [
        command
        for plan in plans
        for command in (*plan.commands, *plan.closing)
        if command.agent is Target.CODEX
    ]

    observed = {command.operation for command in claude_commands}

    assert all(plan.mode is InstallationMode.PERSISTENT for plan in plans)
    assert observed == CLAUDE_SCOPE_BEARING_OPERATIONS | CLAUDE_SCOPELESS_OPERATIONS
    assert all(
        command.argv[-2:] == (CLAUDE_SCOPE_FLAG, CLAUDE_PROJECT_SCOPE)
        and command.cwd == plan.roots.checkout
        for plan in plans
        for command in plan.commands
        if command.agent is Target.CLAUDE
        and command.operation in CLAUDE_SCOPE_BEARING_OPERATIONS
        and command.operation is not Operation.PLUGIN_UPDATE
    )
    assert all(
        command.argv[-2:] == (CLAUDE_SCOPE_FLAG, CLAUDE_PROJECT_SCOPE)
        and command.cwd == plan.roots.checkout
        for plan in plans
        for command in plan.commands
        if command.agent is Target.CLAUDE
        and command.operation is Operation.PLUGIN_UPDATE
    )
    spread = observe_record_refresh_plan()
    marketplace = committed_marketplace_name()
    expected_updates = {
        (
            marketplace_plugin_name(entry[CLAUDE_PLUGIN_ID_FIELD], marketplace),
            entry[CLAUDE_PLUGIN_SCOPE_FIELD],
            Path(entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]),
        )
        for entry, disposition in spread.cases
        if disposition is RecordDisposition.INVOCATION_NATIVE
    }
    expected_rewrites = {
        (
            marketplace_plugin_name(entry[CLAUDE_PLUGIN_ID_FIELD], marketplace),
            entry[CLAUDE_PLUGIN_SCOPE_FIELD],
            Path(entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]),
        )
        for entry, disposition in spread.cases
        if disposition
        in {RecordDisposition.FILE_REWRITE, RecordDisposition.MISSING_DIRECTORY}
    }
    observed_updates = [
        (command.plugin, command.argv[-1], command.cwd)
        for command in spread.plan.commands
        if command.agent is Target.CLAUDE
        and command.operation is Operation.PLUGIN_UPDATE
    ]
    assert {scope for _, scope, _ in expected_updates} == CLAUDE_REFRESH_SCOPES
    assert {path for _, _, path in expected_updates} == {spread.checkout}
    assert {path for _, _, path in expected_rewrites} > set()
    assert spread.checkout not in {path for _, _, path in expected_rewrites}
    assert set(observed_updates) == expected_updates
    assert len(observed_updates) == len(expected_updates)
    assert {
        (record.plugin, record.scope, record.project_path)
        for record in spread.plan.rewrite_records
    } == expected_rewrites
    assert all(command.cwd == spread.checkout for command in spread.attempted)
    assert all(
        command.argv[-2] == CLAUDE_SCOPE_FLAG
        for command in spread.plan.commands
        if command.agent is Target.CLAUDE
        and command.operation is Operation.PLUGIN_UPDATE
    )
    assert all(
        CLAUDE_SCOPE_FLAG not in command.argv
        for command in claude_commands
        if command.operation not in CLAUDE_SCOPE_BEARING_OPERATIONS
    )
    assert codex_commands
    assert all(
        dict(command.environment)[CODEX_HOME_ENV] == str(plan.roots.codex_home)
        for plan in plans
        for command in plan.commands
        if command.agent is Target.CODEX
    )
    assert refreshing.attempted[len(refreshing.preflight.inspections) :] == (
        *refreshing.report.plan.commands,
        *refreshing.report.plan.closing,
    )
    inspections = refreshing.preflight.inspections
    assert {command.operation for command in inspections} == {
        Operation.MARKETPLACE_INSPECT,
        Operation.PLUGIN_INSPECT,
    }
    assert {command.agent for command in inspections} == set(Target)
    assert all(
        command.cwd == refreshing.preflight.roots.checkout
        and CLAUDE_SCOPE_FLAG not in command.argv
        and dict(command.environment)[CODEX_HOME_ENV]
        == str(refreshing.preflight.roots.codex_home)
        for command in inspections
    )


def test_the_uncached_target_fetch_install_runs_at_project_scope_in_a_run_owned_project() -> (
    None
):
    observation = observe_uncached_fetch(UNCACHED_OTHER_CHECKOUT_STATE)
    fetches = observation.fetches
    others = [command for command in observation.attempted if command not in fetches]

    roots = observation.plan.roots
    persistent_directories = (
        observation.checkout,
        observation.other_checkout,
        roots.home,
        roots.claude_config,
        roots.codex_home,
    )

    assert fetches
    assert all(
        command.argv[-2:] == (CLAUDE_SCOPE_FLAG, CLAUDE_PROJECT_SCOPE)
        for command in fetches
    )
    assert all(
        not command.cwd.is_relative_to(directory) and command.cwd != directory
        for command in fetches
        for directory in persistent_directories
    )
    assert len({command.cwd for command in fetches}) == 1
    assert all(
        command.cwd.parent == Path(tempfile.gettempdir()).resolve()
        and command.cwd.name.startswith(FETCH_PROJECT_PREFIX)
        for command in fetches
    )
    assert len(observation.install_project_present) == len(fetches)
    assert all(observation.install_project_present)
    assert not any(observation.fetch_projects_present_after)
    assert others
    assert all(command.cwd == observation.checkout for command in others)


def test_an_enable_failure_stops_the_run_rather_than_reading_as_idempotent() -> None:
    observation = observe_first_failure(Operation.PLUGIN_ENABLE)
    document = json.loads(observation.stderr)

    assert observation.exit_code != 0
    assert document[ReportField.AGENT] == Target.CLAUDE.value
    assert document[ReportField.OPERATION] == Operation.PLUGIN_ENABLE.value
    assert document[ReportField.PLUGIN] == observation.attempted[-1].plugin
    assert (
        observation.attempted
        == observation.command_sequence[: len(observation.attempted)]
    )


def test_a_failed_inspection_stops_before_any_planned_operation() -> None:
    observation = observe_inspection_failure()
    document = json.loads(observation.stderr)

    assert observation.exit_code != 0
    assert document[ReportField.OPERATION] == Operation.MARKETPLACE_INSPECT.value
    assert document[ReportField.AGENT] == observation.attempted[-1].agent.value
    assert (
        observation.attempted
        == observation.command_sequence[: len(observation.attempted)]
    )
    assert not any(
        command in observation.attempted for command in observation.plan.commands
    )


def test_invalid_installed_selection_never_reaches_a_state_changing_operation() -> None:
    for observation in observe_invalid_persistent_selections():
        assert observation.error is not None
        assert SPEC_TREE_PLUGIN in observation.error
        assert observation.attempted
        assert all(
            command.operation
            in {Operation.MARKETPLACE_INSPECT, Operation.PLUGIN_INSPECT}
            for command in observation.attempted
        )


def test_a_codex_operation_failure_reports_the_codex_agent_and_stops() -> None:
    observation = observe_first_failure(Operation.PLUGIN_INSTALL, agent=Target.CODEX)
    document = json.loads(observation.stderr)

    assert observation.exit_code != 0
    assert document[ReportField.AGENT] == Target.CODEX.value
    assert document[ReportField.OPERATION] == Operation.PLUGIN_INSTALL.value
    assert document[ReportField.PLUGIN] == observation.attempted[-1].plugin
    assert document[ReportField.COMPLETED_OPERATIONS] == len(observation.attempted) - 1
    assert (
        observation.attempted
        == observation.command_sequence[: len(observation.attempted)]
    )


def test_first_agent_cli_failure_reports_the_operation_and_stops() -> None:
    observation = observe_first_failure(Operation.PLUGIN_INSTALL)
    document = json.loads(observation.stderr)

    assert observation.exit_code != 0
    assert document[ReportField.AGENT] == Target.CLAUDE.value
    assert document[ReportField.OPERATION] == Operation.PLUGIN_INSTALL.value
    assert document[ReportField.PLUGIN] == observation.attempted[-1].plugin
    assert document[ReportField.STDERR] == Operation.PLUGIN_INSTALL.value
    assert document[ReportField.COMPLETED_OPERATIONS] == len(observation.attempted) - 1
    assert (
        observation.attempted
        == observation.command_sequence[: len(observation.attempted)]
    )
    assert len(observation.attempted) < len(observation.command_sequence)


def test_a_persistent_run_plans_from_one_listing_and_reads_it_once_more_after_execution() -> (
    None
):
    observation = observe_persistent_execution()
    claude = [
        command for command in observation.attempted if command.agent is Target.CLAUDE
    ]
    operations = [command.operation for command in claude]

    assert operations.count(Operation.PLUGIN_INSPECT) == 1
    assert operations.count(Operation.PLUGIN_LIST) == 1
    assert operations.index(Operation.PLUGIN_INSPECT) < min(
        index
        for index, operation in enumerate(operations)
        if operation is Operation.PLUGIN_UPDATE
    )
    assert operations[-1] is Operation.PLUGIN_LIST


def test_a_record_the_closing_listing_leaves_off_the_target_fails_the_run() -> None:
    observation = observe_record_refresh_plan(supplied_closing_listing=True)
    stale = [
        entry
        for entry, disposition in observation.closing_cases
        if disposition is ClosingDisposition.STALE
    ]

    assert len(stale) == 1
    (entry,) = stale
    plugin = marketplace_plugin_name(
        entry[CLAUDE_PLUGIN_ID_FIELD], committed_marketplace_name()
    )
    off_target = cast(
        "list[dict[str, str]]", observation.document[ReportField.OFF_TARGET_RECORDS]
    )
    assert {
        ReportField.PLUGIN: plugin,
        ReportField.SCOPE: entry[CLAUDE_PLUGIN_SCOPE_FIELD],
        ReportField.PROJECT_PATH: entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD],
        ReportField.VERSION: entry[CLAUDE_PLUGIN_VERSION_FIELD],
    } in off_target
    assert observation.exit_code != 0


def test_no_agent_announces_a_first_install_its_plan_does_not_carry() -> None:
    observation = observe_unreadable_source(generated_boolean_states(RegistryState))
    marketplace = committed_marketplace_name()

    for case in observation.cases:
        reported = cast("list[dict[str, str]]", case.document[ReportField.WARNINGS])
        for agent in Target:
            announced = {
                ReportField.AGENT: agent.value,
                ReportField.MESSAGE: FIRST_INSTALL_WARNING.format(
                    marketplace=marketplace,
                    agent=agent.value,
                    plugin=SPEC_TREE_PLUGIN,
                ),
            } in reported
            installs = [
                command
                for command in case.attempted
                if command.agent is agent
                and command.operation is Operation.PLUGIN_INSTALL
            ]
            if announced:
                assert installs, (case.state, agent)
            pending = {
                entry[ReportField.PLUGIN]
                for entry in cast(
                    "list[dict[str, str]]",
                    case.document[ReportField.PENDING_PUBLICATION],
                )
                if entry[ReportField.AGENT] == agent.value
            }
            reached = {
                command.plugin
                for command in case.attempted
                if command.agent is agent
                and command.operation
                in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_UPDATE}
            } - pending
            named = cast(
                "list[str]",
                case.document[ReportField(f"{agent.value}_plugins")],
            )
            assert set(named) == reached, (case.state, agent)


def test_an_empty_selection_supplies_only_spec_tree_with_a_warning_and_disabled_codex_activation() -> (
    None
):
    observation = observe_persistent_plan(
        installed={agent: frozenset() for agent in Target},
    )
    marketplace = committed_marketplace_name()
    plan = observation.plan
    installs = [
        command
        for command in plan.commands
        if command.operation is Operation.PLUGIN_INSTALL
    ]

    assert plan.claude_plugins == (SPEC_TREE_PLUGIN,)
    assert plan.codex_plugins == (SPEC_TREE_PLUGIN,)
    assert {command.agent for command in installs} == set(Target)
    assert {command.plugin for command in installs} == {SPEC_TREE_PLUGIN}
    assert {(warning.agent, warning.message) for warning in plan.warnings} == {
        (
            agent,
            FIRST_INSTALL_WARNING.format(
                marketplace=marketplace,
                agent=agent.value,
                plugin=SPEC_TREE_PLUGIN,
            ),
        )
        for agent in Target
    }
    assert plan.codex_disabled == (SPEC_TREE_PLUGIN,)


def test_an_empty_selection_writes_disabled_activation_into_the_selected_codex_home() -> (
    None
):
    observation = observe_empty_selection_execution()
    marketplace = committed_marketplace_name()

    assert observation.codex_config is not None
    written = tomllib.loads(observation.codex_config.decode("utf-8"))
    assert (
        written["plugins"][
            marketplace_plugin_identifier(SPEC_TREE_PLUGIN, marketplace)
        ]["enabled"]
        is False
    )


def test_an_established_pending_publication_absence_is_reported_in_persistent_mode_and_terminal_in_isolated_mode() -> (
    None
):
    for absent in committed_catalog_plugin_names():
        persistent = observe_unpublished_plugin(
            isolated=False, unpublished=absent_from_every_agent(frozenset({absent}))
        )
        isolated = observe_unpublished_plugin(
            isolated=True, unpublished=absent_from_every_agent(frozenset({absent}))
        )

        assert persistent.failure is None, absent
        assert persistent.report is not None, absent
        assert {entry.plugin for entry in persistent.report.pending_publication} == {
            absent
        }
        assert isolated.report is None, absent
        assert isolated.failure is not None, absent
        assert isolated.failure.command.plugin == absent


def test_a_persistent_update_failure_outside_the_pending_wording_stops_every_later_operation() -> (
    None
):
    marketplace = committed_marketplace_name()
    failures = [
        observe_designated_failure(
            isolated=False,
            operation=Operation.PLUGIN_UPDATE,
            stderr=wording,
        )
        for wording in captured_non_pending_failure_wordings(
            sorted(committed_catalog_plugin_names()), marketplace
        )
    ]

    assert failures
    for observation in failures:
        assert observation.report is None
        assert observation.failure is not None
        assert observation.failure.command.operation is Operation.PLUGIN_UPDATE
        assert observation.calls[-1] == observation.failure.command


def test_trusted_product_codex_configuration_changes_no_installation_command() -> None:
    observation = observe_codex_config_independence()

    assert observation.before.commands == observation.after.commands
    assert observation.before.codex_plugins == observation.after.codex_plugins
    assert observation.before.agent_home == observation.after.agent_home
    assert observation.before.codex_disabled == observation.after.codex_disabled
    assert (
        observation.persistent_before.commands == observation.persistent_after.commands
    )
    assert (
        observation.persistent_before.codex_plugins
        == observation.persistent_after.codex_plugins
    )
    assert (
        observation.persistent_before.agent_home
        == observation.persistent_after.agent_home
    )
    assert (
        observation.persistent_before.codex_disabled
        == observation.persistent_after.codex_disabled
    )
    assert observation.config_observed == observation.config_written
    assert all(
        str(CODEX_CONFIG_PATH) not in argument
        for plan in (observation.after, observation.persistent_after)
        for command in plan.commands
        for argument in command.argv
    )


def test_a_record_written_after_the_listing_read_survives_the_install_record_write(
    tmp_path: Path,
) -> None:
    observation = observe_racing_install_record_rewrite(
        install_record_fixture_path(), tmp_path
    )
    plugins = cast(
        "dict[str, list[dict[str, str]]]",
        observation.document_after[CLAUDE_INSTALLED_PLUGINS_FIELD],
    )
    concurrent_path = observation.concurrent_entry[CLAUDE_PLUGIN_PROJECT_PATH_FIELD]
    surviving = [
        entry
        for entry in plugins[observation.concurrent_identifier]
        if entry.get(CLAUDE_PLUGIN_PROJECT_PATH_FIELD) == concurrent_path
    ]

    assert surviving == [observation.concurrent_entry]
    assert observation.reads > 1
    assert observation.rewrites
