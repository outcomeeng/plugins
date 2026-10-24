"""Root authorization follows catalog changes independently of plugin roles."""

from outcomeeng_testing.harnesses.plugin_authorization import (
    PluginAuthorizationObservation,
    for_all_plugin_authorization_changes,
)


def test_plugin_catalog_changes_drive_root_authorization() -> None:
    def follows_catalog(observation: PluginAuthorizationObservation) -> None:
        assert observation.initial_plugins == observation.catalog
        assert observation.role_added_document == observation.initial_document
        assert observation.updated_plugins == (
            *observation.catalog,
            observation.additional_plugin,
        )
        assert observation.plugin_added_document != observation.initial_document

    for_all_plugin_authorization_changes(follows_catalog)
