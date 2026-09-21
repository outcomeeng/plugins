"""Installation evidence grouped by its governing contract."""

from outcomeeng.distribution.installation import (
    Agent,
    SPEC_TREE_PLUGIN,
)
from outcomeeng_testing.harnesses.installation import (
    observe_isolated_subset_plans,
)


def test_explicit_isolated_subsets_map_to_their_selection_in_catalog_order() -> None:
    observations = observe_isolated_subset_plans()

    for agent in Agent:
        agent_observations = tuple(
            observation for observation in observations if observation.agent is agent
        )
        catalog = agent_observations[0].catalog
        assert len({row.selected for row in agent_observations}) == 2 ** (
            len(catalog) - 1
        )
        for observation in agent_observations:
            assert SPEC_TREE_PLUGIN in observation.selected
            assert observation.selected <= frozenset(catalog)
            assert observation.planned == tuple(
                plugin for plugin in catalog if plugin in observation.selected
            )
