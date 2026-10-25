"""Conformance evidence: the committed Claude Code catalog declares the installer's migration."""

from outcomeeng.distribution.installation import (
    CLAUDE_CATALOG_PATH,
    PRODUCT_TREE_PLUGIN,
    RETIRED_PLUGIN,
    catalog_renames,
)
from outcomeeng_testing.harnesses.installation import (
    observe_committed_renames,
    repository_root,
)


def test_the_committed_catalog_renames_the_plugin_the_installer_migrates_to_its_successor() -> (
    None
):
    renames = observe_committed_renames()

    assert renames.get(RETIRED_PLUGIN) == PRODUCT_TREE_PLUGIN


def test_the_production_reader_accepts_every_rename_the_committed_catalog_declares() -> (
    None
):
    declared = observe_committed_renames()

    read = catalog_renames(repository_root() / CLAUDE_CATALOG_PATH)

    assert read == declared
