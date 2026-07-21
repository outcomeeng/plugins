"""Mapping evidence for pickup claim reconciliation."""

from outcomeeng_testing.harnesses.verify_session_claims import (
    branch_reference_observations,
    claim_mapping_observations,
    git_unavailable_observations,
    load_verify_session_claims_module,
    observed_state_observation,
)


def test_claim_maps_to_verdict() -> None:
    module = load_verify_session_claims_module()

    for observation in claim_mapping_observations():
        assert (
            (
                observation.relation
                in (module.ClaimRelation.MATCHES, module.ClaimRelation.OBSERVED)
                and observation.actual.verdict is module.Verdict.CONFIRMED
            )
            or (
                observation.relation is module.ClaimRelation.DIFFERS
                and observation.actual.verdict is module.Verdict.DISCREPANCY
            )
            or (
                observation.relation is module.ClaimRelation.UNAVAILABLE
                and observation.actual.verdict is module.Verdict.UNVERIFIABLE
            )
        ), (
            f"{observation.kind} with {observation.relation} emitted "
            f"{observation.actual.verdict}"
        )


def test_git_branch_reachability_maps_to_verdict() -> None:
    module = load_verify_session_claims_module()

    for observation in branch_reference_observations():
        assert (
            observation.present_on_origin
            and observation.actual.verdict is module.Verdict.CONFIRMED
        ) or (
            not observation.present_on_origin
            and observation.actual.verdict is module.Verdict.DISCREPANCY
        ), f"{observation.git_ref} emitted {observation.actual.verdict}"


def test_git_failure_statuses_map_to_unverifiable() -> None:
    module = load_verify_session_claims_module()

    for observation in git_unavailable_observations():
        assert observation.actual.verdict is module.Verdict.UNVERIFIABLE, (
            f"git exit {observation.exit_code} emitted {observation.actual.verdict}"
        )


def test_observed_claims_surface_current_values() -> None:
    observation = observed_state_observation()

    assert observation.node_values
    for value in observation.node_values:
        assert value in observation.node.evidence, (
            f"{value} is absent from the surfaced node status"
        )
    assert observation.external_state in observation.external.evidence
