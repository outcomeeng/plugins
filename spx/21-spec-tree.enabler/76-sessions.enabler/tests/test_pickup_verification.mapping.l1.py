"""Mapping evidence for pickup claim reconciliation."""

from outcomeeng_testing.harnesses.verify_session_claims import (
    branch_reference_mappings_hold,
    claim_mappings_hold,
    observed_state_is_surfaced,
)


def test_claim_maps_to_verdict() -> None:
    assert claim_mappings_hold()


def test_git_branch_reachability_maps_to_verdict() -> None:
    assert branch_reference_mappings_hold()


def test_observed_claims_surface_current_values() -> None:
    assert observed_state_is_surfaced()
