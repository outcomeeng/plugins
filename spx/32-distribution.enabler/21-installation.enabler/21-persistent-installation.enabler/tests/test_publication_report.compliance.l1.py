"""Installation evidence grouped by its governing contract."""

from outcomeeng.distribution.installation import (
    Agent,
    Operation,
    ReportField,
    report_document,
)
from outcomeeng_testing.harnesses.installation import (
    absent_from_every_agent,
    committed_catalog_plugin_names,
    observe_unpublished_plugin,
)
from typing import cast


def test_persistent_installation_reports_an_unpublished_plugin_and_completes() -> None:
    absent = sorted(committed_catalog_plugin_names())[0]

    observation = observe_unpublished_plugin(
        isolated=False, unpublished=absent_from_every_agent(frozenset({absent}))
    )

    assert observation.failure is None
    assert observation.report is not None
    assert {entry.plugin for entry in observation.report.pending_publication} == {
        absent
    }
    installed = {
        call.plugin
        for call in observation.calls
        if call.operation is Operation.PLUGIN_INSTALL
    }
    # Every catalog plugin, not merely more than one: "every other plugin still
    # installs" fails the moment the run stops early, and a count threshold
    # passes a run that stopped after the second plugin.
    assert installed == committed_catalog_plugin_names()


def test_the_json_report_never_lists_a_pending_plugin_as_installed() -> None:
    absent = sorted(committed_catalog_plugin_names())[0]

    observation = observe_unpublished_plugin(
        isolated=False, unpublished={Agent.CLAUDE: frozenset({absent})}
    )

    assert observation.report is not None
    document = report_document(observation.report)
    pending = {
        cast(str, entry[ReportField.PLUGIN])
        for entry in cast(
            list[dict[str, str]], document[ReportField.PENDING_PUBLICATION]
        )
    }

    # The text summary and this document answer from the same accessor. Reading
    # the plan directly here reported a plugin as installed in one field while
    # the next field reported it unpublished, and the two disagreed inside one
    # document.
    assert pending == {absent}
    assert not pending & set(cast(list[str], document[ReportField.CLAUDE_PLUGINS]))
    assert absent in cast(list[str], document[ReportField.CODEX_PLUGINS])


def test_a_plugin_absent_from_one_agent_stays_installed_for_the_other() -> None:
    absent = sorted(committed_catalog_plugin_names())[0]

    observation = observe_unpublished_plugin(
        isolated=False, unpublished={Agent.CLAUDE: frozenset({absent})}
    )

    assert observation.failure is None
    assert observation.report is not None
    # The two marketplaces refresh separately, so one agent reporting a plugin
    # unpublished says nothing about the other. A pending record carrying only
    # the plugin name cannot express that, and drops the plugin from both
    # agents' installed counts on either one's failure.
    assert observation.report.pending_for(Agent.CLAUDE) == frozenset({absent})
    assert observation.report.pending_for(Agent.CODEX) == frozenset()
