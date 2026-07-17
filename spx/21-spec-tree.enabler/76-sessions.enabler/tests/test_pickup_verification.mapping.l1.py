"""Mapping evidence for pickup claim reconciliation."""

from types import ModuleType

from outcomeeng_testing.harnesses.verify_session_claims import (
    branch_reference_evidence,
    claim_mapping_evidence,
    load_verify_session_claims_module,
    observed_state_evidence,
)


def _expected_verdict(module: ModuleType, relation: object) -> object:
    if relation in (module.ClaimRelation.MATCHES, module.ClaimRelation.OBSERVED):
        return module.Verdict.CONFIRMED
    if relation is module.ClaimRelation.DIFFERS:
        return module.Verdict.DISCREPANCY
    if relation is module.ClaimRelation.UNAVAILABLE:
        return module.Verdict.UNVERIFIABLE
    raise AssertionError(f"unmapped claim relation: {relation}")


def test_claim_maps_to_verdict() -> None:
    module = load_verify_session_claims_module()

    for observation in claim_mapping_evidence():
        assert observation.verdict is _expected_verdict(module, observation.relation), (
            f"{observation.kind} with {observation.relation} emitted "
            f"{observation.verdict}"
        )


def test_git_branch_reachability_maps_to_verdict() -> None:
    module = load_verify_session_claims_module()

    for observation in branch_reference_evidence():
        expected = (
            module.Verdict.CONFIRMED
            if observation.present_on_origin
            else module.Verdict.DISCREPANCY
        )
        assert observation.verdict is expected, (
            f"{observation.git_ref} emitted {observation.verdict}"
        )


def test_observed_claims_surface_current_values() -> None:
    observation = observed_state_evidence()

    assert observation.node_state in observation.node_evidence
    assert observation.external_state in observation.external_evidence
