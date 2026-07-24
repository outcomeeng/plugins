from __future__ import annotations

from itertools import pairwise

from outcomeeng.validation.implementation_audit_contract import (
    expected_verification_projection,
)
from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    observe_implementation_audit_lifecycle,
    observe_mismatched_terminal_status_finish,
)


def test_verification_run_evidence_sequences_are_monotonic() -> None:
    observation = observe_implementation_audit_lifecycle()

    sequences = observation.scope_sequences
    assert sequences
    assert all(isinstance(sequence, int) for sequence in sequences)
    assert all(current == previous + 1 for previous, current in pairwise(sequences))
    assert observation.finding_sequences == (sequences[-1] + 1,)


def test_verification_run_seals_the_authoritative_finding_count() -> None:
    observation = observe_implementation_audit_lifecycle()

    assert observation.sealed_projection == expected_verification_projection(
        observation.run_token,
        finding_count=observation.recorded_finding_count,
        terminal_status=observation.terminal_status,
    )


def test_verification_run_counts_one_rule_across_subjects() -> None:
    observation = observe_implementation_audit_lifecycle(findings_per_subject=True)

    distinct_subjects = set(observation.subject_paths)
    assert len(distinct_subjects) > 1
    assert len(distinct_subjects) == observation.recorded_finding_count
    assert observation.sealed_projection == expected_verification_projection(
        observation.run_token,
        finding_count=len(distinct_subjects),
        terminal_status=observation.terminal_status,
    )


def test_verification_run_rejects_approval_after_a_blocking_finding() -> None:
    exit_status = observe_mismatched_terminal_status_finish()

    assert exit_status is not None
    assert exit_status != 0
