"""Installation evidence grouped by its governing contract."""

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_CATALOG_PATH,
    CODEX_CATALOG_PATH,
)
from outcomeeng_testing.generators.installation import (
    catalog_plugin_names_from_document,
)
from outcomeeng_testing.harnesses.installation import (
    observe_isolated_subset_plan,
    repository_root,
)


def test_explicit_isolated_subsets_map_to_their_selection_in_catalog_order() -> None:
    observation = observe_isolated_subset_plan()

    catalogs = {
        Agent.CLAUDE: catalog_plugin_names_from_document(
            repository_root() / CLAUDE_CATALOG_PATH
        ),
        Agent.CODEX: catalog_plugin_names_from_document(
            repository_root() / CODEX_CATALOG_PATH
        ),
    }
    planned = {
        Agent.CLAUDE: observation.plan.claude_plugins,
        Agent.CODEX: observation.plan.codex_plugins,
    }
    for agent in Agent:
        assert set(planned[agent]) == set(observation.subsets[agent])
        positions = [catalogs[agent].index(plugin) for plugin in planned[agent]]
        assert positions == sorted(set(positions))
