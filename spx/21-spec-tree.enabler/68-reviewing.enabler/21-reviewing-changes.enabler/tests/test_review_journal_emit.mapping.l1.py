"""Mapping evidence for the review consumer's run-journal adapter.

Covers the reviewing-changes assertions that the streaming review records the
run on ``spx journal --type review`` through the shared projection's per-event
builders — a finding maps onto a finding-reported event and the terminal
run-completed event carries the reviewed diff's identity — and that the
per-finding parse (``journal_emit.py finding-reported``) is the live validity
gate before any journal append.
"""

from __future__ import annotations

import pytest
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_COMPLETION_TIME,
    REVIEW_EVENT_TIME,
    review_contract_modules,
    review_config_digest_observation,
    review_event_cli_observation,
    review_finding,
    review_metadata_observation,
    review_run_metadata,
    review_severity_projection_observation,
    streamed_review_events,
)


def test_adapter_maps_review_severity_to_projection() -> None:
    observation = review_severity_projection_observation()

    assert observation.actual_severities == observation.expected_severities
    assert observation.actual_outcomes == observation.expected_outcomes


def test_adapter_terminal_event_carries_core_run_state_identity() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    metadata = review_run_metadata()
    event = je.run_completed_event(
        metadata,
        [],
        completed_at=REVIEW_COMPLETION_TIME,
        now=REVIEW_EVENT_TIME,
        attempt=1,
    )
    data = event["data"]

    assert event["type"] == jp.RUN_COMPLETED
    assert data[jp.RUN_STATE_BRANCH_NAME] == metadata.branch_name
    assert data[jp.RUN_STATE_BRANCH_SLUG] == metadata.branch_slug
    assert data[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.BRANCH
    assert data[jp.RUN_STATE_HEAD_SHA] == metadata.head_sha
    assert data[jp.RUN_STATE_BASE_REF] == metadata.base_ref
    assert data[jp.RUN_STATE_BASE_SHA] == metadata.base_sha
    assert data[jp.RUN_STATE_CONFIG_DIGEST] == metadata.config_digest
    assert data[jp.RUN_STATE_PARTICIPANTS] == list(metadata.participants)
    assert data[jp.RUN_STATE_SCOPE] == dict(metadata.scope)
    assert data[jp.RUN_STATE_STARTED_AT] == metadata.started_at
    # The run-completed event carries the real completion time, not the
    # provisional start-time the start-of-run metadata bakes in.
    assert data[jp.RUN_STATE_COMPLETED_AT] == REVIEW_COMPLETION_TIME
    assert data[jp.RUN_STATE_STATUS] == jp.JournalRunStatus.APPROVED


def test_adapter_terminal_event_carries_pull_request_identity() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    metadata = review_run_metadata(pull_request=True)
    event = je.run_completed_event(
        metadata,
        [],
        completed_at=REVIEW_COMPLETION_TIME,
        now=REVIEW_EVENT_TIME,
        attempt=1,
    )
    data = event["data"]

    assert data[jp.RUN_STATE_TARGET_KIND] == jp.JournalTargetKind.PULL_REQUEST
    assert data[jp.RUN_STATE_PULL_REQUEST_NUMBER] == metadata.pull_request_number


def test_render_events_counts_review_findings_by_render_class() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    review_result = contracts.review_result
    events = streamed_review_events(
        review_run_metadata(),
        (
            review_finding(severity=review_result.Severity.BLOCKING),
            review_finding(severity=review_result.Severity.DEBT),
        ),
    )
    rendered = je.render_events(events)

    assert rendered[je.RENDER_BLOCKING_FIELD] == "1"
    assert rendered[je.RENDER_DEBT_FIELD] == "1"
    assert rendered[je.RENDER_COUNT_LINE_FIELD] == "BLOCKING: 1, DEBT: 1"
    assert rendered[je.RENDER_OVERALL_FIELD] == str(jp.Outcome.REJECTED)
    assert rendered[je.RENDER_SURFACE_FIELD] == jp.render_surface(events)


def test_terminal_event_rejects_missing_base_identity() -> None:
    contracts = review_contract_modules()
    je = contracts.journal_emit
    jp = contracts.journal_projection
    metadata = review_run_metadata(missing_base_identity=True)

    with pytest.raises(ValueError, match=jp.RUN_STATE_BASE_SHA):
        je.run_completed_event(
            metadata,
            [],
            completed_at=REVIEW_COMPLETION_TIME,
            now=REVIEW_EVENT_TIME,
            attempt=1,
        )


def test_config_digest_mapping() -> None:
    observation = review_config_digest_observation()

    assert observation.prompt_change_changes_digest
    assert observation.runner_and_adapter_share_digest
    assert observation.root_policy_change_preserves_digest
    assert observation.metadata_ignores_root_policy


def test_metadata_mapping() -> None:
    observation = review_metadata_observation()

    assert observation.changed_file_set_changes_scope_hash
    assert observation.manifest_scope_matches_source_bundle
    assert observation.pull_request_identity_matches_environment
    assert observation.detached_branch_identity_matches_environment
    assert observation.changed_review_input_changes_scope_hash
    assert observation.metadata_cli_emits_source_identity
    assert observation.git_failure_is_reported_without_traceback


def test_event_cli_mapping() -> None:
    observation = review_event_cli_observation()

    assert observation.scope_entered_matches_contract
    assert observation.scope_advanced_matches_contract
    assert observation.conforming_finding_maps_to_event
    assert observation.malformed_finding_emits_only_error
    assert observation.completed_event_rolls_up_prefix
