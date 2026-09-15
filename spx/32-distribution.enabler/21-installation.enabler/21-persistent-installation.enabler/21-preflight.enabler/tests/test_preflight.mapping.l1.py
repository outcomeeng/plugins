"""Native listing membership independent of persistent selection."""

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_CATALOG_PATH,
    CODEX_CATALOG_PATH,
    CODEX_PLUGIN_ENTRIES_FIELD,
    installed_plugin_names,
)
from outcomeeng_testing.generators.installation import (
    catalog_plugin_names_from_document,
    generated_claude_listing_entries,
    generated_codex_listing_entries,
)
from outcomeeng_testing.harnesses.installation import repository_root
import json


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
