"""Mapping evidence for pickup claim reconciliation.

The finite claim/relation domain comes from the shipped verifier. The harness
arranges each source-owned pair through generated inputs and real git state.
"""

from outcomeeng_testing.harnesses.verify_session_claims import (
    branch_reference_evidence,
    claim_mapping_evidence,
    observed_state_is_surfaced,
)


def test_claim_maps_to_verdict() -> None:
    for evidence in claim_mapping_evidence():
        assert evidence.actual is evidence.expected, (
            evidence.kind,
            evidence.relation,
        )


def test_git_branch_reachability_maps_to_verdict() -> None:
    for evidence in branch_reference_evidence():
        assert evidence.actual is evidence.expected, evidence.relation


def test_observed_claims_surface_current_values() -> None:
    assert observed_state_is_surfaced()
