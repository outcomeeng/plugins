"""Conformance evidence: the committed Claude Code catalog declares the retired plugin ids the installer reads."""

from outcomeeng.distribution.installation import (
    CLAUDE_CATALOG_PATH,
    catalog_renames,
)
from outcomeeng_testing.harnesses.installation import (
    committed_catalog_plugin_names,
    observe_committed_renames,
    repository_root,
)


def test_every_retired_plugin_id_the_committed_catalog_declares_resolves_to_a_listed_plugin() -> (
    None
):
    renames = observe_committed_renames()
    listed = committed_catalog_plugin_names()

    assert renames
    assert set(renames.values()) <= listed
    assert not set(renames) & listed


def test_the_production_reader_returns_the_renames_the_committed_catalog_declares() -> (
    None
):
    declared = observe_committed_renames()

    read = catalog_renames(repository_root() / CLAUDE_CATALOG_PATH)

    assert read == declared
