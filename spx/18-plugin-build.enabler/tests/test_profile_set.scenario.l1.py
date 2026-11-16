"""Scenario evidence that the central profile set holds no `executor` and holds change-applier's selection."""

from __future__ import annotations

from outcomeeng.distribution.profiles import AgentProfile
from outcomeeng_testing.harnesses.agent_conversion import product_tree_wrapper_agents

RETIRED_PROFILE_NAME = "executor"
CHANGE_APPLIER_PROFILE_NAME = "thorough"
CHANGE_APPLIER_DEFINITION_NAME = "change-applier"


def test_profile_set_is_free_of_executor_and_holds_change_applier_selection() -> None:
    member_names = {member.name.lower() for member in AgentProfile}
    member_values = {member.value for member in AgentProfile}
    selections = {
        source.name: source.profile for source in product_tree_wrapper_agents()
    }

    assert RETIRED_PROFILE_NAME not in member_names
    assert RETIRED_PROFILE_NAME not in member_values
    assert selections[CHANGE_APPLIER_DEFINITION_NAME] == CHANGE_APPLIER_PROFILE_NAME
    assert CHANGE_APPLIER_PROFILE_NAME in member_values
    assert CHANGE_APPLIER_PROFILE_NAME in member_names
