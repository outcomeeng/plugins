from __future__ import annotations

from outcomeeng_testing.harnesses.audit_verification_run_contract import (
    observe_implementation_audit_lifecycle,
)


def test_minimum_spx_release_accepts_implementation_audit_lifecycle() -> None:
    observation = observe_implementation_audit_lifecycle()

    assert observation.run_token
    assert observation.scope_sequences
    assert None not in observation.scope_sequences
    assert observation.finding_sequences
    assert None not in observation.finding_sequences
    assert None not in observation.sealed_projection
