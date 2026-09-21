"""Installation evidence grouped by its governing contract."""

from outcomeeng.distribution.installation import Operation
from outcomeeng_testing.harnesses.installation import (
    observe_interrupted_reconciliation,
    ScopeSplitClassification,
    installation_fixture,
    observe_agent_home_collision,
    observe_agent_home_reconciliation,
    observe_scope_split,
)


def test_persistent_installation_places_agents_in_the_selected_home() -> None:
    observation = observe_agent_home_reconciliation()

    assert set(observation.home_first) == (
        set(observation.home_initial) | set(observation.desired_first)
    )
    assert len(observation.home_first) == len(
        {name for name, _ in observation.home_first}
    )
    assert observation.ownership_record_present
    assert observation.foreign_first == observation.foreign_initial
    assert {path.name for path in observation.first_result.written} == {
        name for name, _ in observation.desired_first
    }


def test_catalog_reconciliation_prunes_only_stale_owned_agents() -> None:
    observation = observe_agent_home_reconciliation()
    retired_agents = set(observation.desired_first) - set(observation.desired_second)
    retired_plugins = set(observation.desired_second) - set(observation.desired_third)

    assert set(observation.home_second) == (
        set(observation.home_initial) | set(observation.desired_second)
    )
    assert {path.name for path in observation.second_result.pruned} == {
        name for name, _ in retired_agents
    }
    assert observation.foreign_second == observation.foreign_initial
    assert set(observation.home_third) == (
        set(observation.home_initial) | set(observation.desired_third)
    )
    assert {path.name for path in observation.third_result.pruned} == {
        name for name, _ in retired_plugins
    }
    assert observation.foreign_third == observation.foreign_initial


def test_an_interrupted_run_is_adopted_cleanly_on_rerun() -> None:
    observation = observe_interrupted_reconciliation()

    assert observation.first_result.collisions == ()
    assert observation.second_result.collisions == ()
    assert observation.second_result.written == ()
    assert observation.second_result.pruned == ()
    assert observation.home_second == observation.home_first
    assert observation.record_present_after


def test_foreign_agent_collision_stops_before_any_mutation() -> None:
    observation = observe_agent_home_collision()

    assert observation.collisions
    assert observation.attempted
    assert all(
        command.operation in {Operation.MARKETPLACE_INSPECT, Operation.PLUGIN_INSPECT}
        for command in observation.attempted
    )
    assert observation.home_after == observation.home_before


def test_scope_split_reports_exact_and_changed_copies_before_mutation() -> None:
    observation = observe_scope_split()

    assert {entry.classification for entry in observation.entries} == {
        ScopeSplitClassification.DIRECTED_REMOVAL,
        ScopeSplitClassification.SHADOWING_COLLISION,
    }
    assert {entry.path for entry in observation.entries} == {
        path.parent.resolve() / path.name for path in observation.checkout_paths
    }
    assert {
        entry.classification
        for entry in observation.entries
        if entry.path.name == installation_fixture("local_helper.toml").name
    } == {ScopeSplitClassification.SHADOWING_COLLISION}
    assert observation.attempted == ()
    assert observation.home_after == observation.home_before
