"""Finite catalog-to-agent mapping evidence for repository installation."""

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import (
    Operation,
    ReportField,
    SPEC_TREE_PLUGIN,
    SourceAction,
    claude_registered_marketplace,
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
    project_record_dispositions,
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
    assert observation.marketplace == observe_committed_declarations().marketplace
    projection = project_record_dispositions(observation)
    for row in projection.rows:
        counts = (len(row.updates), len(row.rewrites), row.warning_count)
        if row.disposition is RecordDisposition.EXCLUDED:
            assert row.plugin is None, row
        elif row.disposition is RecordDisposition.INVOCATION_NATIVE:
            assert counts == (1, 0, 0), row
        elif row.disposition in {
            RecordDisposition.FILE_REWRITE,
            RecordDisposition.MISSING_DIRECTORY,
        }:
            assert counts == (0, 1, 0), row
        else:
            assert counts == (0, 0, 1), row
    assert projection.unmatched_updates == ()
    assert projection.unmatched_rewrites == ()
    assert projection.unmatched_warnings == ()
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
