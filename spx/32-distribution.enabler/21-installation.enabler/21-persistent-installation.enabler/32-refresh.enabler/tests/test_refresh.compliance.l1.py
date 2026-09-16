"""Installation evidence grouped by its governing contract."""

from outcomeeng.distribution.installation import (
    CODEX_CONFIG_PATH,
    Agent,
    CLAUDE_LOCAL_SCOPE,
    FIRST_INSTALL_WARNING,
    SPEC_TREE_PLUGIN,
    Operation,
)
from outcomeeng_testing.harnesses.installation import (
    observe_codex_config_independence,
    observe_designated_failure,
    observe_local_record_bootstrap_plan,
    observe_persistent_execution,
    observe_persistent_plan,
)


def test_repository_codex_config_has_no_installation_semantics() -> None:
    observation = observe_codex_config_independence()

    assert observation.before.commands == observation.after.commands
    assert observation.before.claude_plugins == observation.after.claude_plugins
    assert observation.before.codex_plugins == observation.after.codex_plugins
    assert (
        observation.persistent_before.commands == observation.persistent_after.commands
    )
    assert (
        observation.persistent_before.codex_plugins
        == observation.persistent_after.codex_plugins
    )
    assert observation.config_observed == observation.config_written
    assert all(
        str(CODEX_CONFIG_PATH) not in argument
        for plan in (observation.after, observation.persistent_after)
        for command in plan.commands
        for argument in command.argv
    )


def test_a_recorded_plugin_is_refreshed_by_the_native_update_never_a_reinstall() -> (
    None
):
    execution = observe_persistent_execution()
    claude_commands = [
        command
        for command in execution.report.plan.commands
        if command.agent is Agent.CLAUDE
    ]
    updated = [
        command.plugin
        for command in claude_commands
        if command.operation is Operation.PLUGIN_UPDATE
    ]
    failure = observe_designated_failure(
        isolated=False,
        operation=Operation.PLUGIN_UPDATE,
        stderr="update failed for a reason the marketplace did not name",
    )

    assert execution.report.plan.claude_plugins
    assert not any(
        command.operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}
        for command in claude_commands
    )
    assert tuple(updated) == execution.report.plan.claude_plugins
    assert all(
        command.cwd == execution.report.plan.roots.checkout
        for command in claude_commands
        if command.operation is Operation.PLUGIN_UPDATE
    )
    registering = observe_persistent_plan(claude_repository=None)
    registering_claude = [
        command
        for command in registering.plan.commands
        if command.agent is Agent.CLAUDE
    ]
    registering_operations = [command.operation for command in registering_claude]
    assert registering.plan.claude_plugins
    assert not any(
        operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}
        for operation in registering_operations
    )
    assert (
        tuple(
            command.plugin
            for command in registering_claude
            if command.operation is Operation.PLUGIN_UPDATE
        )
        == registering.plan.claude_plugins
    )
    assert registering_operations.index(Operation.MARKETPLACE_ADD) < (
        registering_operations.index(Operation.PLUGIN_UPDATE)
    )
    assert failure.report is None
    assert failure.failure is not None
    assert failure.failure.command.operation is Operation.PLUGIN_UPDATE
    assert not any(
        command.operation is Operation.PLUGIN_LIST and command.agent is Agent.CLAUDE
        for command in failure.calls
    )


def test_a_local_scope_record_for_the_checkout_suppresses_the_bootstrap_install() -> (
    None
):
    observation = observe_local_record_bootstrap_plan()
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

    assert not any(
        command.operation in {Operation.PLUGIN_INSTALL, Operation.PLUGIN_ENABLE}
        for command in claude_commands
    )
    assert [(command.plugin, command.argv[-1], command.cwd) for command in updates] == [
        (SPEC_TREE_PLUGIN, CLAUDE_LOCAL_SCOPE, observation.plan.roots.checkout)
    ]
    assert FIRST_INSTALL_WARNING.format(agent=Agent.CLAUDE.value) not in [
        warning.message for warning in observation.plan.warnings
    ]
