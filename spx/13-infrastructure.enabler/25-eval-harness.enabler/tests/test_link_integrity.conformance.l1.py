"""Conformance tests for the evidence-link-integrity walker."""

from __future__ import annotations

from outcomeeng_testing.harnesses.link_integrity import assert_link_integrity_contract


def test_evidence_link_integrity_contract() -> None:
    assert_link_integrity_contract()
