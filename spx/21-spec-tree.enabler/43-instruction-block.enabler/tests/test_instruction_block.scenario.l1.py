"""Scenario evidence for the instruction-block render model.

The harness owns temporary repositories, stream capture, and scenario setup. Each executed test
is a zero-argument assertion wrapper around one governed harness entrypoint.
"""

from outcomeeng_testing.harnesses import instruction_block_scenarios as scenarios


def test_write_produces_both_files_language_and_harness_filtered() -> None:
    scenarios.assert_write_produces_both_files_language_and_harness_filtered()


def test_write_preserves_shared_region_and_independent_prose() -> None:
    scenarios.assert_write_preserves_shared_region_and_independent_prose()


def test_router_marker_format() -> None:
    scenarios.assert_router_marker_format()


def test_both_files_identical_except_harness_spans() -> None:
    scenarios.assert_both_files_identical_except_harness_spans()


def test_newer_template_adds_section_preserving_shared_region() -> None:
    scenarios.assert_newer_template_adds_section_preserving_shared_region()


def test_template_symlink_is_rejected() -> None:
    scenarios.assert_template_symlink_is_rejected()


def test_cli_rejects_missing_repo_root() -> None:
    scenarios.assert_cli_rejects_missing_repo_root()


def test_cli_rejects_non_directory_repo_root() -> None:
    scenarios.assert_cli_rejects_non_directory_repo_root()


def test_cli_rejects_missing_template() -> None:
    scenarios.assert_cli_rejects_missing_template()


def test_cli_rejects_directory_template() -> None:
    scenarios.assert_cli_rejects_directory_template()


def test_cli_rejects_root_symlink_escaping_repo() -> None:
    scenarios.assert_cli_rejects_root_symlink_escaping_repo()


def test_cli_rejects_spx_symlink_during_language_detection() -> None:
    scenarios.assert_cli_rejects_spx_symlink_during_language_detection()


def test_cli_detects_languages_from_test_extensions() -> None:
    scenarios.assert_cli_detects_languages_from_test_extensions()


def test_cli_write_without_repo_root_exits() -> None:
    scenarios.assert_cli_write_without_repo_root_exits()


def test_cli_check_reports_absent_when_one_file_missing() -> None:
    scenarios.assert_cli_check_reports_absent_when_one_file_missing()


def test_cli_check_treats_language_order_as_set() -> None:
    scenarios.assert_cli_check_treats_language_order_as_set()


def test_cli_check_marks_router_not_first_as_stale() -> None:
    scenarios.assert_cli_check_marks_router_not_first_as_stale()


def test_unparseable_version_is_stale() -> None:
    scenarios.assert_unparseable_version_is_stale()


def test_symlinked_root_file_becomes_regular_file() -> None:
    scenarios.assert_symlinked_root_file_becomes_regular_file()


def test_markerless_generated_body_is_replaced() -> None:
    scenarios.assert_markerless_generated_body_is_replaced()


def test_legacy_marker_block_reported_stale_and_replaced() -> None:
    scenarios.assert_legacy_marker_block_reported_stale_and_replaced()


def test_quoted_router_marker_in_prose_is_preserved() -> None:
    scenarios.assert_quoted_router_marker_in_prose_is_preserved()


def test_quoted_router_closing_marker_after_block_is_preserved() -> None:
    scenarios.assert_quoted_router_closing_marker_after_block_is_preserved()


def test_quoted_shared_fence_in_prose_is_not_a_region() -> None:
    scenarios.assert_quoted_shared_fence_in_prose_is_not_a_region()


def test_malformed_shared_fence_is_reported_stale() -> None:
    scenarios.assert_malformed_shared_fence_is_reported_stale()


def test_bootstrap_refuses_a_malformed_seed_fence() -> None:
    scenarios.assert_bootstrap_refuses_a_malformed_seed_fence()


def test_duplicate_shared_region_name_is_malformed() -> None:
    scenarios.assert_duplicate_shared_region_name_is_malformed()


def test_blank_run_in_independent_content_preserved() -> None:
    scenarios.assert_blank_run_in_independent_content_preserved()


def test_bootstrap_preserves_lines_when_common_span_ends_mid_line() -> None:
    scenarios.assert_bootstrap_preserves_lines_when_common_span_ends_mid_line()


def test_bootstrap_finds_whole_line_block_over_longer_straddling_match() -> None:
    scenarios.assert_bootstrap_finds_whole_line_block_over_longer_straddling_match()


def test_bootstrap_snaps_span_to_line_boundaries_in_both_files() -> None:
    scenarios.assert_bootstrap_snaps_span_to_line_boundaries_in_both_files()


def test_diverged_shared_region_reconciles_to_more_recent_side() -> None:
    scenarios.assert_diverged_shared_region_reconciles_to_more_recent_side()


def test_reconcile_replaces_losing_region_whole_without_blending() -> None:
    scenarios.assert_reconcile_replaces_losing_region_whole_without_blending()


def test_reconcile_uses_region_recency_not_whole_file_recency() -> None:
    scenarios.assert_reconcile_uses_region_recency_not_whole_file_recency()


def test_region_line_range_covers_content_lines_only() -> None:
    scenarios.assert_region_line_range_covers_content_lines_only()


def test_recency_tie_is_reported_ambiguous() -> None:
    scenarios.assert_recency_tie_is_reported_ambiguous()


def test_one_sided_shared_region_is_reported_ambiguous() -> None:
    scenarios.assert_one_sided_shared_region_is_reported_ambiguous()


def test_reconcile_reports_malformed_fence_as_ambiguous() -> None:
    scenarios.assert_reconcile_reports_malformed_fence_as_ambiguous()


def test_reconcile_skips_a_malformed_duplicate_name() -> None:
    scenarios.assert_reconcile_skips_a_malformed_duplicate_name()


def test_cli_reconcile_requires_repo_root() -> None:
    scenarios.assert_cli_reconcile_requires_repo_root()


def test_cli_reconcile_from_applies_operator_tie_break() -> None:
    scenarios.assert_cli_reconcile_from_applies_operator_tie_break()


def test_cli_reconcile_reports_no_change_when_regions_agree() -> None:
    scenarios.assert_cli_reconcile_reports_no_change_when_regions_agree()


def test_reconcile_makes_no_change_to_a_dirty_file() -> None:
    scenarios.assert_reconcile_makes_no_change_to_a_dirty_file()
