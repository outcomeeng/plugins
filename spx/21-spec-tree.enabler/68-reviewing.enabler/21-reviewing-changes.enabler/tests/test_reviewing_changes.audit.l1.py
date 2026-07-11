from outcomeeng_testing.harnesses.reviewing_changes_audit import (
    TestComputeDiffHasNoPersistenceAddressing as _ComputeDiffHasNoPersistenceAddressing,
    TestNoParallelReviewResultRenderer as _NoParallelReviewResultRenderer,
    TestNoSecondSchemaRepresentation as _NoSecondSchemaRepresentation,
    TestScriptsAreStdlibOnly as _ScriptsAreStdlibOnly,
    render_command_projects_from_journal_events,
    scripts_use_no_direct_write_primitives,
)


def test_scripts_use_no_direct_write_primitives() -> None:
    scripts_use_no_direct_write_primitives()


def test_scripts_import_only_stdlib_and_local_modules() -> None:
    _ScriptsAreStdlibOnly().test_no_third_party_or_outcomeeng_imports()


def test_scripts_do_not_import_outcomeeng() -> None:
    _ScriptsAreStdlibOnly().test_no_outcomeeng_imports()


def test_scripts_do_not_reference_uv_at_runtime() -> None:
    _ScriptsAreStdlibOnly().test_no_runtime_uv_references()


def test_no_alternate_schema_file_exists() -> None:
    _NoSecondSchemaRepresentation().test_no_alternate_schema_file_exists()


def test_compute_diff_has_no_persistence_addressing() -> None:
    _ComputeDiffHasNoPersistenceAddressing().test_compute_diff_has_no_slug_argument()


def test_script_set_has_no_parallel_renderer() -> None:
    _NoParallelReviewResultRenderer().test_script_set_is_the_audit_parity_set()


def test_no_render_templates_directory() -> None:
    _NoParallelReviewResultRenderer().test_no_render_templates_directory()


def test_render_command_projects_from_journal_events() -> None:
    render_command_projects_from_journal_events()
