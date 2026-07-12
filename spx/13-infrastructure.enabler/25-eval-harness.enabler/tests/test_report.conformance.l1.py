"""Binding-free conformance wrappers for eval reports."""

from outcomeeng_testing.evals.assert_report import (
    assert_serialize_result_carries_schema_version_and_suite_summary,
    assert_serialize_result_defaults_to_concrete_model,
    assert_serialize_result_preserves_case_expectations,
    assert_serialize_result_includes_trial_transcripts,
    assert_serialize_result_is_json_round_trippable,
    assert_serialize_result_aggregates_cost_summary_across_trials,
    assert_cost_summary_aggregates_cache_tokens_across_trials,
    assert_serialize_result_carries_per_trial_metadata,
    assert_cost_summary_skips_trials_without_metadata,
    assert_cost_summary_counts_cache_only_metadata_trial,
    assert_write_json_report_writes_file_and_returns_path,
    assert_write_run_reports_emits_html_and_sidecar_json,
    assert_write_run_reports_embeds_json_payload_in_script_tag,
    assert_write_run_reports_renders_no_closing_script_in_body,
    assert_trial_stability_for_k1_reports_zero_or_one_pass_rate_per_case,
    assert_trial_stability_for_k_greater_than_1_computes_mean,
    assert_trial_stability_stddev_is_none_with_single_case,
    assert_outcome_carries_trial_pass_count_and_rate_in_json,
)


def test_serialize_result_carries_schema_version_and_suite_summary() -> None:
    assert_serialize_result_carries_schema_version_and_suite_summary()


def test_serialize_result_defaults_to_concrete_model() -> None:
    assert_serialize_result_defaults_to_concrete_model()


def test_serialize_result_preserves_case_expectations() -> None:
    assert_serialize_result_preserves_case_expectations()


def test_serialize_result_includes_trial_transcripts() -> None:
    assert_serialize_result_includes_trial_transcripts()


def test_serialize_result_is_json_round_trippable() -> None:
    assert_serialize_result_is_json_round_trippable()


def test_serialize_result_aggregates_cost_summary_across_trials() -> None:
    assert_serialize_result_aggregates_cost_summary_across_trials()


def test_cost_summary_aggregates_cache_tokens_across_trials() -> None:
    assert_cost_summary_aggregates_cache_tokens_across_trials()


def test_serialize_result_carries_per_trial_metadata() -> None:
    assert_serialize_result_carries_per_trial_metadata()


def test_cost_summary_skips_trials_without_metadata() -> None:
    assert_cost_summary_skips_trials_without_metadata()


def test_cost_summary_counts_cache_only_metadata_trial() -> None:
    assert_cost_summary_counts_cache_only_metadata_trial()


def test_write_json_report_writes_file_and_returns_path() -> None:
    assert_write_json_report_writes_file_and_returns_path()


def test_write_run_reports_emits_html_and_sidecar_json() -> None:
    assert_write_run_reports_emits_html_and_sidecar_json()


def test_write_run_reports_embeds_json_payload_in_script_tag() -> None:
    assert_write_run_reports_embeds_json_payload_in_script_tag()


def test_write_run_reports_renders_no_closing_script_in_body() -> None:
    assert_write_run_reports_renders_no_closing_script_in_body()


def test_trial_stability_for_k1_reports_zero_or_one_pass_rate_per_case() -> None:
    assert_trial_stability_for_k1_reports_zero_or_one_pass_rate_per_case()


def test_trial_stability_for_k_greater_than_1_computes_mean() -> None:
    assert_trial_stability_for_k_greater_than_1_computes_mean()


def test_trial_stability_stddev_is_none_with_single_case() -> None:
    assert_trial_stability_stddev_is_none_with_single_case()


def test_outcome_carries_trial_pass_count_and_rate_in_json() -> None:
    assert_outcome_carries_trial_pass_count_and_rate_in_json()
