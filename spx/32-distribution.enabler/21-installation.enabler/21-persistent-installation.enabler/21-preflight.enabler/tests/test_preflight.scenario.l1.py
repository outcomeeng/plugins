"""Installation evidence grouped by its governing contract."""

import json
import os
from outcomeeng.distribution.installation import (
    Agent,
    CANONICAL_MARKETPLACE_SOURCE,
    Operation,
    ReportField,
    SPEC_TREE_PLUGIN,
    USER_SCOPE_COLLISION_DIAGNOSTIC,
    PATHLESS_LISTING_ENTRY_DIAGNOSTIC,
    CLAUDE_PROJECT_SCOPE,
    REGISTRY_SOURCE_DIAGNOSTIC,
    UNREADABLE_SETTINGS_DIAGNOSTIC,
)
from outcomeeng_testing.harnesses.installation import (
    observe_claude_user_collision,
    observe_inspection_failure,
    observe_invalid_persistent_selection,
    observe_persistent_plan,
    observe_noncanonical_registry_plan,
    observe_pathless_record_listing,
    observe_unreadable_source,
)
from outcomeeng_testing.generators.installation import marketplace_source_from_fixture

NONCANONICAL_MARKETPLACE_SOURCE = marketplace_source_from_fixture(
    "project-marketplace-noncanonical.json"
)


def test_invalid_persistent_subset_is_rejected_before_mutation() -> None:
    observation = observe_invalid_persistent_selection()

    assert observation.error is not None
    assert SPEC_TREE_PLUGIN in observation.error
    assert observation.attempted
    assert all(
        command.operation in {Operation.MARKETPLACE_INSPECT, Operation.PLUGIN_INSPECT}
        for command in observation.attempted
    )


def test_marketplace_inspection_failure_stops_before_any_plan_operation() -> None:
    observation = observe_inspection_failure()
    document = json.loads(observation.stderr)

    assert observation.exit_code != os.EX_OK
    assert observation.stdout == ""
    assert document[ReportField.OPERATION] == Operation.MARKETPLACE_INSPECT.value
    assert document[ReportField.AGENT] == observation.attempted[-1].agent.value
    assert document[ReportField.COMPLETED_OPERATIONS] == len(observation.attempted[:-1])
    assert (
        observation.attempted
        == observation.command_sequence[: len(observation.attempted)]
    )
    assert not any(
        command in observation.attempted for command in observation.plan.commands
    )


def test_claude_user_scope_collision_stops_before_mutation() -> None:
    observation = observe_claude_user_collision()

    assert observation.error is not None
    assert str(observation.settings_path) in observation.error
    assert USER_SCOPE_COLLISION_DIAGNOSTIC in observation.error
    assert observation.attempted == ()


def test_fresh_home_plan_adds_the_declared_marketplace() -> None:
    observation = observe_persistent_plan(claude_marketplace_listed=False)

    source_operations = [
        command.operation
        for command in observation.plan.commands
        if command.agent is Agent.CLAUDE
        and command.operation
        in {
            Operation.MARKETPLACE_ADD,
            Operation.MARKETPLACE_REFRESH,
        }
    ]
    assert source_operations == [Operation.MARKETPLACE_ADD]


def test_a_pathless_refresh_scope_entry_stops_before_any_plan() -> None:
    error = observe_pathless_record_listing()

    assert error == PATHLESS_LISTING_ENTRY_DIAGNOSTIC.format(
        index=0, scope=CLAUDE_PROJECT_SCOPE
    )


def test_unreadable_invocation_settings_stop_before_any_plan() -> None:
    observation = observe_unreadable_source()

    assert observation.error is not None
    assert observation.error.startswith(UNREADABLE_SETTINGS_DIAGNOSTIC)
    assert str(observation.settings_path) in observation.error


def test_a_noncanonical_registry_source_stops_before_any_plan() -> None:
    error = observe_noncanonical_registry_plan(NONCANONICAL_MARKETPLACE_SOURCE)

    assert error is not None
    assert error.startswith(REGISTRY_SOURCE_DIAGNOSTIC)
    assert NONCANONICAL_MARKETPLACE_SOURCE in error
    assert CANONICAL_MARKETPLACE_SOURCE in error
