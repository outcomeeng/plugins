"""Compliance evidence for review-changes scripts."""

from outcomeeng_testing.harnesses.reviewing_changes import (
    review_contract_modules,
    review_render_observation,
    review_script_compliance_observation,
    violating_review_script_fixtures_detected,
)


def test_scripts_use_no_direct_write_primitives() -> None:
    assert not review_script_compliance_observation().direct_writes


def test_violating_script_fixtures_are_rejected() -> None:
    assert all(violating_review_script_fixtures_detected())


def test_scripts_import_only_stdlib_and_local_modules() -> None:
    assert not review_script_compliance_observation().non_stdlib_imports


def test_scripts_do_not_import_outcomeeng() -> None:
    assert not review_script_compliance_observation().product_toolchain_imports


def test_scripts_do_not_reference_uv_at_runtime() -> None:
    assert not review_script_compliance_observation().runtime_uv_references


def test_no_alternate_schema_file_exists() -> None:
    assert not review_script_compliance_observation().alternate_schema_paths


def test_compute_diff_has_no_persistence_addressing() -> None:
    assert not review_script_compliance_observation().persistence_arguments


def test_script_set_has_no_parallel_renderer() -> None:
    observation = review_script_compliance_observation()

    assert not observation.unexpected_scripts
    assert not observation.parallel_scripts


def test_no_render_templates_directory() -> None:
    assert review_script_compliance_observation().render_directory_exists is False


def test_render_command_projects_from_journal_events() -> None:
    observation = review_render_observation()
    contracts = review_contract_modules()

    assert observation.rendered[contracts.journal_emit.RENDER_SURFACE_FIELD] == (
        contracts.journal_projection.render_surface(list(observation.events))
    )
    assert observation.rendered[contracts.journal_emit.RENDER_OVERALL_FIELD] == str(
        contracts.journal_projection.compute_overall(list(observation.events))
    )
