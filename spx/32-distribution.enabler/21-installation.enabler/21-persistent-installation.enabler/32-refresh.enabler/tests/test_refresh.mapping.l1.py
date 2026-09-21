"""Installation evidence grouped by its governing contract."""

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    Operation,
    RecordWarningReason,
    marketplace_plugin_name,
)
from outcomeeng_testing.generators.installation import RecordDisposition
from outcomeeng_testing.harnesses.installation import observe_record_refresh_plans


def test_every_claude_install_record_maps_to_one_update_or_one_warning() -> None:
    for observation in observe_record_refresh_plans():
        updates = [
            command
            for command in observation.plan.commands
            if command.agent is Agent.CLAUDE
            and command.operation is Operation.PLUGIN_UPDATE
        ]
        warnings = [
            warning
            for warning in observation.plan.warnings
            if warning.agent is Agent.CLAUDE
        ]
        unmatched_updates = list(updates)
        unmatched_warnings = list(warnings)
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
            assert isinstance(disposition, RecordWarningReason)
            record_identity = f"records {plugin} at {scope} scope"
            matching_warnings = [
                warning
                for warning in unmatched_warnings
                if warning.reason is disposition
                and record_identity in warning.message
                and (project_path is None or str(project_path) in warning.message)
            ]
            assert len(matching_warnings) == 1, (entry, disposition, warnings)
            unmatched_warnings.remove(matching_warnings[0])

        assert unmatched_updates == []
        assert unmatched_warnings == []
        positions = [observation.catalog.index(command.plugin) for command in updates]
        assert positions == sorted(positions)
