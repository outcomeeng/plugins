"""Scenario evidence for the complete review-changes script chain."""

from __future__ import annotations

from outcomeeng_testing.harnesses.reviewing_changes import (
    clean_review_chain_observation,
    compute_diff_scenario_observation,
    malformed_runner_finding_observation,
    review_chain_with_finding_observation,
    review_contract_modules,
    review_runner_coverage_observation,
    review_runner_lifecycle_observation,
    review_runner_rename_observation,
)


def test_chain_streams_and_renders_review_run() -> None:
    observation = review_chain_with_finding_observation()
    contracts = review_contract_modules()
    journal_emit = contracts.journal_emit
    projection = contracts.journal_projection

    assert observation.diff_result.returncode == 0, observation.diff_result.stderr
    assert observation.changed_file in observation.diff_result.stdout
    assert observation.metadata_result.returncode == 0
    assert observation.rendered[journal_emit.RENDER_SURFACE_FIELD] == (
        projection.render_surface(list(observation.events))
    )
    assert observation.rendered[journal_emit.RENDER_OVERALL_FIELD] == str(
        projection.compute_overall(list(observation.events))
    )


def test_clean_review_streams_a_zero_count() -> None:
    observation = clean_review_chain_observation()
    journal_emit = review_contract_modules().journal_emit

    assert observation.rendered[journal_emit.RENDER_BLOCKING_FIELD] == str(
        len(observation.findings)
    )
    assert observation.rendered[journal_emit.RENDER_DEBT_FIELD] == str(
        len(observation.findings)
    )


def test_runner_preserves_journal_lifecycle() -> None:
    observation = review_runner_lifecycle_observation()

    assert observation.start_contract_holds
    assert observation.namespace_is_preserved
    assert observation.finish_returns_raw_token
    assert observation.scratch_state_is_removed
    assert observation.journal_protocol_holds
    assert observation.finding_identity_is_preserved
    assert observation.terminal_rollup_holds


def test_runner_rejects_malformed_finding_before_append() -> None:
    observation = malformed_runner_finding_observation()
    projection = review_contract_modules().journal_projection

    assert observation.returncode != 0
    assert observation.missing_field in observation.stderr
    assert observation.event_types == (projection.SCOPE_ENTERED,)


def test_runner_rejects_incomplete_scope_coverage() -> None:
    observation = review_runner_coverage_observation()

    assert observation.finish_is_rejected
    assert observation.missing_scope_is_named
    assert observation.only_scope_entered_is_recorded
    assert observation.journal_remains_open


def test_runner_requires_rename_source_and_destination() -> None:
    observation = review_runner_rename_observation()

    assert observation.both_paths_are_required
    assert observation.destination_alone_is_rejected
    assert observation.source_is_named_as_missing
    assert observation.both_paths_allow_finish


def test_compute_diff_scenarios() -> None:
    observation = compute_diff_scenario_observation()

    assert observation.explicit_base_selects_committed_diff
    assert observation.all_worktree_sections_are_included
    assert observation.bundle_paths_match_contract
    assert observation.bundle_summary_matches_content
    assert observation.bundle_manifest_identity_matches_source
    assert observation.bundle_section_ranges_match_content
    assert observation.invalid_bundle_destinations_are_rejected
    assert observation.origin_head_supplies_default_base
    assert observation.missing_base_sources_are_named
    assert observation.explicit_head_selects_alternate_diff
    assert observation.literal_head_is_the_default
    assert observation.stale_local_base_does_not_widen_diff
