"""Mapping tests for deterministic merge-gate policy helpers."""

from __future__ import annotations

from outcomeeng_testing.harnesses.merging_policy import (
    assert_auditor_verdict_mapping_contract,
    assert_delivery_mapping_contract,
    assert_required_check_mapping_contract,
    assert_review_check_mapping_contract,
)


def test_required_check_status_and_conclusion_mapping() -> None:
    assert assert_required_check_mapping_contract()


def test_review_check_status_and_conclusion_mapping() -> None:
    assert assert_review_check_mapping_contract()


def test_delivery_phase_mapping() -> None:
    assert assert_delivery_mapping_contract()


def test_auditor_verdict_mapping() -> None:
    assert assert_auditor_verdict_mapping_contract()
