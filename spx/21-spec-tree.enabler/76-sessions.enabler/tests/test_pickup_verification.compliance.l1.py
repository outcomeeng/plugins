"""Compliance evidence for pickup claim verification.

Each assertion calls one behavior-level harness entrypoint. Source contracts,
runner setup, generated payloads, diagnostics, and AST inspection remain behind
the imported infrastructure boundary.
"""

from outcomeeng_testing.harnesses.verify_session_claims import (
    default_runner_failure_is_unverifiable,
    external_calls_go_through_runner,
    metadata_loading_uses_structured_session_api,
    node_status_keeps_source_scalar_fields_only,
    script_imports_are_stdlib_only,
    verification_is_read_only_and_uses_source_commands,
    verify_accepts_injected_runner,
)


def test_verify_accepts_injected_runner() -> None:
    assert verify_accepts_injected_runner()


def test_script_imports_are_stdlib_only() -> None:
    assert script_imports_are_stdlib_only()


def test_external_calls_go_through_the_runner() -> None:
    assert external_calls_go_through_runner()


def test_default_runner_launch_failure_emits_unverifiable() -> None:
    assert default_runner_failure_is_unverifiable()


def test_verification_is_read_only_and_uses_source_commands() -> None:
    assert verification_is_read_only_and_uses_source_commands()


def test_node_status_evidence_keeps_target_node_scalar_fields_only() -> None:
    assert node_status_keeps_source_scalar_fields_only()


def test_metadata_loading_does_not_require_local_session_file_body() -> None:
    assert metadata_loading_uses_structured_session_api()
