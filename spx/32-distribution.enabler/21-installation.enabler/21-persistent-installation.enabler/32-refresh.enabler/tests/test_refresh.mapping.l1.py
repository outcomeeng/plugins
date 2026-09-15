"""Installation evidence grouped by its governing contract."""


from outcomeeng.distribution.installation import NO_DIRECTORY_PATH_WARNING, Agent, CLAUDE_PLUGIN_ID_FIELD, CLAUDE_PLUGIN_PROJECT_PATH_FIELD, CLAUDE_PLUGIN_SCOPE_FIELD, NONCANONICAL_SOURCE_WARNING, OUT_OF_SCOPE_RECORD_WARNING, PATHLESS_OUT_OF_SCOPE_RECORD_WARNING, UNREADABLE_SETTINGS_WARNING, UNCATALOGED_RECORD_WARNING, Operation, marketplace_plugin_name
from outcomeeng_testing.generators.installation import RecordDisposition
from outcomeeng_testing.harnesses.installation import observe_record_refresh_plan

def test_every_claude_install_record_maps_to_one_update_or_one_warning() -> None:
    observation = observe_record_refresh_plan()
    updates = [
        command
        for command in observation.plan.commands
        if command.agent is Agent.CLAUDE
        and command.operation is Operation.PLUGIN_UPDATE
    ]
    warnings = [
        warning.message
        for warning in observation.plan.warnings
        if warning.agent is Agent.CLAUDE
    ]
    unmatched_updates = list(updates)
    unmatched_warnings = list(warnings)
    templates = {
        RecordDisposition.NO_DIRECTORY_PATH: NO_DIRECTORY_PATH_WARNING,
        RecordDisposition.OUT_OF_SCOPE: OUT_OF_SCOPE_RECORD_WARNING,
        RecordDisposition.PATHLESS_OUT_OF_SCOPE: PATHLESS_OUT_OF_SCOPE_RECORD_WARNING,
        RecordDisposition.UNCATALOGED: UNCATALOGED_RECORD_WARNING,
        RecordDisposition.NONCANONICAL_SOURCE: NONCANONICAL_SOURCE_WARNING,
        RecordDisposition.UNREADABLE_SETTINGS: UNREADABLE_SETTINGS_WARNING,
    }

    for entry, disposition in observation.cases:
        plugin = marketplace_plugin_name(entry[CLAUDE_PLUGIN_ID_FIELD])
        if disposition is RecordDisposition.EXCLUDED:
            assert plugin is None, (entry, disposition)
            continue
        assert plugin is not None, (entry, disposition)
        scope = entry[CLAUDE_PLUGIN_SCOPE_FIELD]
        project_path = entry.get(CLAUDE_PLUGIN_PROJECT_PATH_FIELD)
        matching_updates = [
            command
            for command in unmatched_updates
            if command.plugin == plugin
            and command.argv[-1] == scope
            and str(command.cwd) == project_path
        ]
        if disposition is RecordDisposition.UPDATE:
            assert len(matching_updates) == 1, (entry, disposition)
            unmatched_updates.remove(matching_updates[0])
            continue
        assert matching_updates == [], (entry, disposition)
        template = templates[disposition]
        expected = template.format(
            plugin=plugin, scope=scope, project_path=project_path
        )
        assert unmatched_warnings.count(expected) == 1, (entry, disposition, warnings)
        unmatched_warnings.remove(expected)

    assert unmatched_updates == []
    assert unmatched_warnings == []
    positions = [observation.catalog.index(command.plugin) for command in updates]
    assert positions == sorted(positions)
