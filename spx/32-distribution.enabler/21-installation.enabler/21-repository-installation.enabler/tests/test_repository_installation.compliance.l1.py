"""Ambient-state and repository-config evidence for installation."""

from outcomeeng.distribution.installation import (
    CODEX_CONFIG_PATH,
    Operation,
    SourceAction,
)
from outcomeeng_testing.harnesses.installation import (
    observe_codex_config_independence,
    observe_failed_run_restore,
    observe_noncanonical_reconciliation,
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
    assert observation.config_bytes
    assert all(
        str(CODEX_CONFIG_PATH) not in argument
        for plan in (observation.after, observation.persistent_after)
        for command in plan.commands
        for argument in command.argv
    )


def test_restoring_the_selection_keeps_the_reconciled_marketplace_source() -> None:
    observation = observe_noncanonical_reconciliation()

    assert observation.source_action is SourceAction.REPLACE
    assert observation.selection_after == observation.selection_before
    assert observation.marketplace_before != observation.canonical_marketplace
    assert observation.marketplace_after == observation.canonical_marketplace


def test_failed_persistent_run_restores_the_committed_selection() -> None:
    observation = observe_failed_run_restore(Operation.PLUGIN_ENABLE)

    assert observation.failure is not None
    assert observation.settings_after == observation.settings_before
    assert observation.attempted[-1].operation is observation.failed_operation
