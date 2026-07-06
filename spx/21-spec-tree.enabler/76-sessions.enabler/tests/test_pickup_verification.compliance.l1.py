"""Compliance evidence for pickup claim verification."""

from outcomeeng_testing.harnesses.verify_session_claims import (
    default_runner_launch_failure_emits_unverifiable,
    external_calls_go_through_the_runner,
    invalid_session_metadata_is_unverifiable,
    malformed_session_metadata_fields_are_unverifiable,
    metadata_loading_does_not_require_local_session_file_body,
    node_status_evidence_keeps_target_node_scalar_fields_only,
    script_imports_are_stdlib_only,
    verification_is_read_only_and_uses_spec_status,
    verify_accepts_injected_runner,
    wrong_shape_session_metadata_is_unverifiable,
)


def test_verify_accepts_injected_runner() -> None:
    assert verify_accepts_injected_runner()


def test_script_imports_are_stdlib_only() -> None:
    assert script_imports_are_stdlib_only()


def test_external_calls_go_through_the_runner() -> None:
    assert external_calls_go_through_the_runner()


def test_default_runner_launch_failure_emits_unverifiable() -> None:
    assert default_runner_launch_failure_emits_unverifiable()


def test_verification_is_read_only_and_uses_spec_status() -> None:
    assert verification_is_read_only_and_uses_spec_status()


def test_node_status_evidence_keeps_target_node_scalar_fields_only() -> None:
    assert node_status_evidence_keeps_target_node_scalar_fields_only()


def test_invalid_session_metadata_is_unverifiable() -> None:
    assert invalid_session_metadata_is_unverifiable()


def test_wrong_shape_session_metadata_is_unverifiable() -> None:
    assert wrong_shape_session_metadata_is_unverifiable()


def test_malformed_session_metadata_fields_are_unverifiable() -> None:
    assert malformed_session_metadata_fields_are_unverifiable()


def test_metadata_loading_does_not_require_local_session_file_body() -> None:
    assert metadata_loading_does_not_require_local_session_file_body()
