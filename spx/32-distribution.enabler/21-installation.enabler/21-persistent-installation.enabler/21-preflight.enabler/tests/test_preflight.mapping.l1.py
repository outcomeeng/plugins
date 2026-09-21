"""Native listing membership independent of persistent selection."""

from outcomeeng.distribution.installation import (
    Agent,
    CANONICAL_MARKETPLACE_SOURCE,
    CLAUDE_CATALOG_PATH,
    CODEX_CATALOG_PATH,
    CODEX_PLUGIN_ENTRIES_FIELD,
    installed_plugin_names,
)
from outcomeeng_testing.generators.installation import (
    catalog_plugin_names_from_document,
    generated_claude_listing_entries,
    generated_codex_listing_entries,
    marketplace_source_from_fixture,
)
from outcomeeng_testing.harnesses.installation import (
    observe_noncanonical_source,
    repository_root,
)
import json
import pytest

NONCANONICAL_MARKETPLACE_SOURCE = marketplace_source_from_fixture(
    "project-marketplace-noncanonical.json"
)


@pytest.mark.parametrize("agent", tuple(Agent), ids=str)
def test_every_noncanonical_agent_source_stops_before_any_plan(agent: Agent) -> None:
    error = observe_noncanonical_source(agent, NONCANONICAL_MARKETPLACE_SOURCE)

    assert error is not None
    assert NONCANONICAL_MARKETPLACE_SOURCE in error
    assert CANONICAL_MARKETPLACE_SOURCE in error


def test_claude_inventory_maps_only_the_invocation_checkout_refresh_scopes() -> None:
    checkout = repository_root()
    catalog = catalog_plugin_names_from_document(checkout / CLAUDE_CATALOG_PATH)
    entries, in_scope = generated_claude_listing_entries(catalog, checkout)

    observed = installed_plugin_names(
        Agent.CLAUDE,
        json.dumps(list(entries)),
        checkout=checkout,
    )

    assert observed == in_scope


def test_codex_inventory_maps_only_outcomeeng_marketplace_entries() -> None:
    checkout = repository_root()
    catalog = catalog_plugin_names_from_document(checkout / CODEX_CATALOG_PATH)
    entries, in_scope = generated_codex_listing_entries(catalog)

    observed = installed_plugin_names(
        Agent.CODEX,
        json.dumps({CODEX_PLUGIN_ENTRIES_FIELD: list(entries)}),
        checkout=checkout,
    )

    assert observed == in_scope
