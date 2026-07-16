"""Mapping evidence for the review consumer's run-journal adapter.

Covers the reviewing-changes assertions that the streaming review records the
run on ``spx journal --type review`` through the shared projection's per-event
builders — a finding maps onto a finding-reported event and the terminal
run-completed event carries the reviewed diff's identity — and that the
per-finding parse (``journal_emit.py finding-reported``) is the live validity
gate before any journal append.
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.reviewing_changes import (
    missing_terminal_base_identity_is_rejected,
    review_config_digest_contract_holds,
    review_event_cli_contract_holds,
    review_metadata_contract_holds,
    review_render_count_mapping_holds,
    review_severity_projection_contract_holds,
    review_terminal_branch_identity_contract_holds,
    review_terminal_pull_request_identity_contract_holds,
)


def test_adapter_maps_review_severity_to_projection() -> None:
    assert review_severity_projection_contract_holds()


def test_adapter_terminal_event_carries_core_run_state_identity() -> None:
    assert review_terminal_branch_identity_contract_holds()


def test_adapter_terminal_event_carries_pull_request_identity() -> None:
    assert review_terminal_pull_request_identity_contract_holds()


def test_render_events_counts_review_findings_by_render_class() -> None:
    assert review_render_count_mapping_holds()


def test_terminal_event_rejects_missing_base_identity() -> None:
    assert missing_terminal_base_identity_is_rejected()


def test_config_digest_mapping() -> None:
    assert review_config_digest_contract_holds()


def test_metadata_mapping() -> None:
    assert review_metadata_contract_holds()


def test_event_cli_mapping() -> None:
    assert review_event_cli_contract_holds()
