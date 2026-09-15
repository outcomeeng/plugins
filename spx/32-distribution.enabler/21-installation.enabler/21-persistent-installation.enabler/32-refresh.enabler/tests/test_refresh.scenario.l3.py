"""Installation evidence grouped by its governing contract."""


import json
from outcomeeng.distribution.installation import CLAUDE_LOCAL_SCOPE, CLAUDE_PROJECT_SCOPE, ClaudeInstallRecord, ReportField, SPEC_TREE_PLUGIN
from outcomeeng_testing.harnesses.installation import observe_real_record_refresh

def test_real_persistent_run_refreshes_a_second_checkout_at_local_scope() -> None:
    observation = observe_real_record_refresh()

    expected = {
        (SPEC_TREE_PLUGIN, CLAUDE_PROJECT_SCOPE, observation.invocation_checkout),
        (SPEC_TREE_PLUGIN, CLAUDE_LOCAL_SCOPE, observation.other_checkout),
    }
    recorded_before = {
        (record.plugin, record.scope, record.project_path)
        for record in observation.records_before
        if isinstance(record, ClaudeInstallRecord)
    }
    assert expected <= recorded_before
    assert observation.exit_code == 0, observation.stderr
    document = json.loads(observation.stdout)
    refreshed = {
        (
            record[ReportField.PLUGIN],
            record[ReportField.SCOPE],
            record[ReportField.PROJECT_PATH],
        )
        for record in document[ReportField.CLAUDE_RECORDS]
    }
    assert {(plugin, scope, str(path)) for plugin, scope, path in expected} <= refreshed
    assert observation.records_after == observation.records_before
    assert (
        observation.invocation_activation_after
        == observation.invocation_activation_before
    )
    assert observation.other_activation_after == observation.other_activation_before
