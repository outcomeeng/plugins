"""Mapping assertions backed by the review-journal contract harness."""

from outcomeeng_testing.harnesses.review_journal_emit_contract import (  # noqa: F401
    test_adapter_maps_review_severity_to_projection,
    test_adapter_terminal_event_carries_core_run_state_identity,
    test_adapter_terminal_event_carries_pull_request_identity,
    test_config_digest_changes_with_review_prompt,
    test_config_digest_ignores_root_review_policy,
    test_finding_reported_cli_maps_conforming_finding_to_event,
    test_finding_reported_cli_maps_malformed_finding_to_error_with_no_event,
    test_metadata_cli_emits_env_derived_run_identity,
    test_metadata_cli_reports_git_failure_without_traceback,
    test_metadata_config_digest_ignores_root_review_policy,
    test_metadata_for_worktree_records_pull_request_target,
    test_metadata_for_worktree_uses_env_branch_in_detached_checkout,
    test_metadata_scope_hash_includes_changed_file_set,
    test_metadata_scope_hash_includes_full_review_input,
    test_metadata_scope_uses_computed_review_manifest,
    test_render_events_counts_review_findings_by_render_class,
    test_run_completed_cli_reads_prefix_and_sets_completion_time,
    test_scope_advanced_cli_names_the_unit,
    test_scope_entered_cli_emits_identity_event,
    test_terminal_event_rejects_missing_base_identity,
)
