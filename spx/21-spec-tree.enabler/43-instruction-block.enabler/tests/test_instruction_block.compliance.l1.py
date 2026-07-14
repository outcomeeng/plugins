"""Compliance evidence for the instruction-block render model.

The ALWAYS/NEVER rules of ``instruction-block.md`` with deterministic test evidence: both root
files are written together, the router is first, generation reads the ``dist/`` templates, the
writer is bound through the ``just`` recipes and
the lefthook pre-commit hook, the drift gate reports a missing root path and overwrites router
drift, the refresh workflow regenerates and opens a PR only on drift while verifying its pinned
tooling, no product-specific string enters the router, a former command-slot fence is ordinary
content, a reconcile never blends bodies, the retired session tokens never render, an unresolved
build macro is rejected, and retired ``spx/`` instruction files are removed. Real repository
config (``justfile``, ``lefthook.yml``, the workflow) is read through harness helpers.
"""

from outcomeeng_testing.harnesses import instruction_block as harness


def test_generation_writes_both_root_files() -> None:
    harness.assert_generation_writes_both_root_files()


def test_router_is_first() -> None:
    harness.assert_router_is_first()


def test_generation_reads_dist_templates() -> None:
    harness.assert_generation_reads_dist_templates()


def test_justfile_binds_build_and_check_recipes() -> None:
    harness.assert_justfile_binds_instruction_recipes()


def test_lefthook_regenerates_through_build_instructions() -> None:
    harness.assert_lefthook_regenerates_through_build_instructions()


def test_drift_gate_reports_a_missing_root_instruction_file() -> None:
    harness.assert_drift_gate_reports_missing_root_instruction_file()


def test_drift_gate_marks_untracked_root_file_intent_to_add() -> None:
    harness.assert_drift_gate_marks_untracked_root_files()


def test_drift_gate_skips_missing_obsolete_spx_file() -> None:
    harness.assert_drift_gate_skips_missing_obsolete_spx_file()


def test_refresh_pr_step_exits_cleanly_without_drift() -> None:
    harness.assert_refresh_pr_step_exits_cleanly_without_drift()


def test_refresh_pr_step_stages_obsolete_deletions() -> None:
    harness.assert_refresh_pr_step_stages_obsolete_deletions()


def test_regenerate_overwrites_router_drift() -> None:
    harness.assert_regenerate_overwrites_router_drift()


def test_refresh_workflow_regenerates_and_opens_pr() -> None:
    harness.assert_refresh_workflow_regenerates_and_opens_pr()


def test_refresh_workflow_checks_out_main() -> None:
    harness.assert_refresh_workflow_checks_out_main()


def test_refresh_workflow_verifies_just_download() -> None:
    harness.assert_refresh_workflow_verifies_just_download()


def test_refresh_workflow_installs_dprint() -> None:
    harness.assert_refresh_workflow_installs_dprint()


def test_render_passes_brace_token_through_unchanged() -> None:
    harness.assert_render_preserves_brace_token()


def test_former_command_slot_fence_is_ordinary_content() -> None:
    harness.assert_former_command_slot_fence_is_ordinary_content()


def test_reconcile_replaces_the_losing_region_whole() -> None:
    harness.assert_reconcile_replaces_losing_region_whole()


def test_rendered_router_omits_retired_session_tokens() -> None:
    harness.assert_rendered_router_omits_retired_session_tokens()


def test_foundation_policy_guard_rejects_missing_requirement() -> None:
    harness.assert_foundation_policy_guard_rejects_missing_requirement()


def test_foundation_policy_guard_rejects_forbidden_router_token() -> None:
    harness.assert_foundation_policy_guard_rejects_forbidden_router_token()


def test_unresolved_build_macro_is_rejected() -> None:
    harness.assert_unresolved_build_macro_is_rejected()


def test_obsolete_spx_instruction_files_are_removed() -> None:
    harness.assert_obsolete_spx_instruction_files_are_removed()
