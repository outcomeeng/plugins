"""Mapping evidence for pickup claim reconciliation."""

from outcomeeng_testing.harnesses.verify_session_claims import (
    branch_reference_evidence,
    claim_mapping_evidence,
    load_verify_session_claims_module,
    observed_state_evidence,
)


def test_claim_maps_to_verdict() -> None:
    module = load_verify_session_claims_module()

    for observation in claim_mapping_evidence():
        assert (
            (
                observation.relation
                in (module.ClaimRelation.MATCHES, module.ClaimRelation.OBSERVED)
                and observation.verdict is module.Verdict.CONFIRMED
            )
            or (
                observation.relation is module.ClaimRelation.DIFFERS
                and observation.verdict is module.Verdict.DISCREPANCY
            )
            or (
                observation.relation is module.ClaimRelation.UNAVAILABLE
                and observation.verdict is module.Verdict.UNVERIFIABLE
            )
        ), (
            f"{observation.kind} with {observation.relation} emitted "
            f"{observation.verdict}"
        )


def test_git_branch_reachability_maps_to_verdict() -> None:
    module = load_verify_session_claims_module()

    for observation in branch_reference_evidence():
        assert (
            observation.present_on_origin
            and observation.verdict is module.Verdict.CONFIRMED
        ) or (
            not observation.present_on_origin
            and observation.verdict is module.Verdict.DISCREPANCY
        ), f"{observation.git_ref} emitted {observation.verdict}"


def test_observed_claims_surface_current_values() -> None:
    observation = observed_state_evidence()

    assert observation.node_state in observation.node_evidence
    assert observation.external_state in observation.external_evidence
