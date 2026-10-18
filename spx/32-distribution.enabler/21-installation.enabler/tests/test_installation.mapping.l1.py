"""Finite catalog-to-agent mapping evidence for repository installation."""

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import (
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    OUT_OF_SCOPE_RECORD_WARNING,
    Operation,
    PATHLESS_LISTING_ENTRY_WARNING,
    PATHLESS_OUT_OF_SCOPE_RECORD_WARNING,
    ReportField,
    SPEC_TREE_PLUGIN,
    SourceAction,
    UNCATALOGED_RECORD_WARNING,
    claude_registered_marketplace,
    marketplace_plugin_name,
)
from outcomeeng_testing.generators.installation import (
    RecordDisposition,
    RegistryShape,
    UNCATALOGED_PLUGIN,
    catalog_plugin_names_from_bytes,
    generated_persistent_catalog_selections,
)
from outcomeeng_testing.harnesses.installation import (
    observe_committed_declarations,
    observe_persistent_catalog_subset_plans,
    observe_record_refresh_plan,
    observe_registry_shape_plan,
    observe_repository_plan,
)


def test_each_mode_maps_its_selection_to_catalog_order() -> None:
    isolated = observe_repository_plan()
    assert isolated.plan.claude_plugins == catalog_plugin_names_from_bytes(
        isolated.claude_catalog
    )
    assert isolated.plan.codex_plugins == catalog_plugin_names_from_bytes(
        isolated.codex_catalog
    )
    observations = observe_persistent_catalog_subset_plans()
    assert tuple(observation.agent for observation in observations) == tuple(Target)
    for observation in observations:
        assert tuple(mapping.selected for mapping in observation.mappings) == (
            generated_persistent_catalog_selections(observation.catalog)
        )
        for mapping in observation.mappings:
            assert UNCATALOGED_PLUGIN not in observation.catalog
            assert UNCATALOGED_PLUGIN not in mapping.planned
            if not mapping.selected:
                assert mapping.planned == (SPEC_TREE_PLUGIN,)
            else:
                assert set(mapping.planned) == set(mapping.selected)
                positions = [
                    observation.catalog.index(plugin) for plugin in mapping.planned
                ]
                assert positions == sorted(set(positions))
            if observation.agent is Target.CLAUDE and mapping.selected:
                assert mapping.installs == ()
                assert mapping.enables == ()
                assert mapping.updates == mapping.planned
            else:
                assert mapping.installs == mapping.planned
                assert mapping.enables == (
                    mapping.planned if observation.agent is Target.CLAUDE else ()
                )
                assert mapping.updates == ()


def test_every_claude_install_record_maps_to_its_refresh_disposition() -> None:
    observation = observe_record_refresh_plan()
    marketplace = observe_committed_declarations().marketplace
    assert observation.marketplace == marketplace
    updates = [
        command
        for command in observation.plan.commands
        if command.agent is Target.CLAUDE
        and command.operation is Operation.PLUGIN_UPDATE
    ]
    warnings = [
        warning.message
        for warning in observation.plan.warnings
        if warning.agent is Target.CLAUDE
    ]
    unmatched_updates = list(updates)
    unmatched_rewrites = list(observation.plan.rewrite_records)
    unmatched_warnings = list(warnings)
    templates = {
        RecordDisposition.OUT_OF_SCOPE: OUT_OF_SCOPE_RECORD_WARNING,
        RecordDisposition.PATHLESS_OUT_OF_SCOPE: PATHLESS_OUT_OF_SCOPE_RECORD_WARNING,
        RecordDisposition.PATHLESS_DEFECT: PATHLESS_LISTING_ENTRY_WARNING,
        RecordDisposition.UNCATALOGED: UNCATALOGED_RECORD_WARNING,
    }

    for entry, disposition in observation.cases:
        plugin = marketplace_plugin_name(entry[CLAUDE_PLUGIN_ID_FIELD], marketplace)
        if disposition is RecordDisposition.EXCLUDED:
            assert plugin is None, (entry, disposition)
            continue
        assert plugin is not None, (entry, disposition)
        scope = entry[CLAUDE_PLUGIN_SCOPE_FIELD]
        project_path = entry.get(CLAUDE_PLUGIN_PROJECT_PATH_FIELD)
        matching_updates = [
            command
            for command in unmatched_updates
            if command.plugin == plugin and command.argv[-1] == scope
        ]
        matching_rewrites = [
            record
            for record in unmatched_rewrites
            if record.plugin == plugin
            and record.scope == scope
            and str(record.project_path) == project_path
        ]
        if disposition is RecordDisposition.INVOCATION_NATIVE:
            assert len(matching_updates) == 1, (entry, disposition)
            assert matching_updates[0].cwd == observation.checkout
            assert matching_rewrites == [], (entry, disposition)
            unmatched_updates.remove(matching_updates[0])
            continue
        if disposition in {
            RecordDisposition.FILE_REWRITE,
            RecordDisposition.MISSING_DIRECTORY,
        }:
            assert len(matching_rewrites) == 1, (entry, disposition)
            unmatched_rewrites.remove(matching_rewrites[0])
            continue
        assert matching_rewrites == [], (entry, disposition)
        expected = templates[disposition].format(
            plugin=plugin, scope=scope, project_path=project_path
        )
        assert unmatched_warnings.count(expected) == 1, (entry, disposition, warnings)
        unmatched_warnings.remove(expected)

    assert unmatched_updates == []
    assert unmatched_rewrites == []
    assert unmatched_warnings == []
    assert all(command.cwd == observation.checkout for command in observation.attempted)
    assert observation.exit_code == 0


def test_each_registry_entry_shape_maps_to_the_source_the_run_refreshes_from() -> None:
    observation = observe_registry_shape_plan()
    committed = observe_committed_declarations()
    marketplace = committed.marketplace
    assert observation.marketplace == marketplace
    declared_source = committed.declared_claude_source

    for payload, shape, expected_source, expected_action in observation.rows:
        registered = claude_registered_marketplace(payload, marketplace)
        plan = observation.plans[shape]
        document = observation.documents[shape]
        assert document[ReportField.SOURCE] == (
            declared_source if expected_source is None else expected_source
        ), shape
        assert document[ReportField.MARKETPLACE] == marketplace
        source_operations = [
            command
            for command in plan.commands
            if command.agent is Target.CLAUDE
            and command.operation
            in {Operation.MARKETPLACE_ADD, Operation.MARKETPLACE_REFRESH}
        ]
        assert len(source_operations) == 1, shape
        if expected_action is SourceAction.ADD:
            assert registered is None, shape
            assert source_operations[0].operation is Operation.MARKETPLACE_ADD
            assert declared_source in source_operations[0].argv, shape
        else:
            assert registered is not None, shape
            assert registered.source == expected_source, shape
            assert source_operations[0].operation is Operation.MARKETPLACE_REFRESH
            assert source_operations[0].argv[-1] == marketplace
            assert expected_source not in source_operations[0].argv, shape
    assert {shape for _, shape, _, _ in observation.rows} == set(RegistryShape)
