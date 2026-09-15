"""Installation evidence grouped by its governing contract."""

from outcomeeng.distribution.installation import Operation, SPEC_TREE_PLUGIN
from outcomeeng_testing.harnesses.installation import (
    absent_from_every_agent,
    committed_catalog_plugin_names,
    observe_invalid_isolated_selection,
    observe_unpublished_plugin,
)


def test_invalid_isolated_subset_is_rejected_before_mutation() -> None:
    observation = observe_invalid_isolated_selection()

    assert observation.error is not None
    assert SPEC_TREE_PLUGIN in observation.error
    assert observation.attempted == ()


def test_isolated_installation_treats_an_absent_plugin_as_terminal() -> None:
    absent = sorted(committed_catalog_plugin_names())[0]

    observation = observe_unpublished_plugin(
        isolated=True, unpublished=absent_from_every_agent(frozenset({absent}))
    )

    assert observation.report is None
    assert observation.failure is not None
    assert observation.failure.command.plugin == absent
    assert observation.failure.command.operation is Operation.PLUGIN_INSTALL
