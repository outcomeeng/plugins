from outcomeeng_testing.harnesses.native_agent_recovery import (
    native_agent_recovery_compliance_evidence,
)


def test_native_agent_recovery_compliance() -> None:
    assert (
        native_agent_recovery_compliance_evidence().sends
        == native_agent_recovery_compliance_evidence().expected_sends
    )
    assert (
        native_agent_recovery_compliance_evidence().recovery_input
        == native_agent_recovery_compliance_evidence().expected_recovery_input
    )
    assert native_agent_recovery_compliance_evidence().command_violation_count == 0
    assert (
        native_agent_recovery_compliance_evidence().detected_violating_call_count
        == native_agent_recovery_compliance_evidence().violating_call_count
    )
    assert (
        native_agent_recovery_compliance_evidence().failure_status
        == native_agent_recovery_compliance_evidence().expected_failure_status
    )
    assert (
        native_agent_recovery_compliance_evidence().failure_send_count
        == native_agent_recovery_compliance_evidence().expected_failure_send_count
    )
    assert (
        native_agent_recovery_compliance_evidence().verification_status
        == native_agent_recovery_compliance_evidence().expected_verification_status
    )
    assert (
        native_agent_recovery_compliance_evidence().verified_count
        == native_agent_recovery_compliance_evidence().expected_verified_count
    )
    assert (
        native_agent_recovery_compliance_evidence().correlation_field_sets
        == native_agent_recovery_compliance_evidence().expected_correlation_field_sets
    )
    assert (
        native_agent_recovery_compliance_evidence().correlation_identities
        == native_agent_recovery_compliance_evidence().expected_correlation_identities
    )
    assert native_agent_recovery_compliance_evidence().verification_send_count == 0
    assert (
        native_agent_recovery_compliance_evidence().recover_cli_exit
        == native_agent_recovery_compliance_evidence().expected_recover_cli_exit
    )
    assert (
        native_agent_recovery_compliance_evidence().recover_cli_status
        == native_agent_recovery_compliance_evidence().expected_recover_cli_status
    )
    assert (
        native_agent_recovery_compliance_evidence().recover_cli_command_violation_count
        == 0
    )
    assert (
        native_agent_recovery_compliance_evidence().verify_cli_exit
        == native_agent_recovery_compliance_evidence().expected_verify_cli_exit
    )
    assert (
        native_agent_recovery_compliance_evidence().verify_cli_status
        == native_agent_recovery_compliance_evidence().expected_verify_cli_status
    )
    assert (
        native_agent_recovery_compliance_evidence().verify_cli_command_violation_count
        == 0
    )
    assert native_agent_recovery_compliance_evidence().parser_has_state is False
    assert (
        native_agent_recovery_compliance_evidence().verbatim_worktree_path
        == native_agent_recovery_compliance_evidence().expected_verbatim_worktree_path
    )
    assert (
        native_agent_recovery_compliance_evidence().verbatim_repository_root
        == native_agent_recovery_compliance_evidence().expected_verbatim_repository_root
    )
    assert (
        native_agent_recovery_compliance_evidence().verbatim_cwd
        == native_agent_recovery_compliance_evidence().expected_verbatim_cwd
    )
    assert (
        native_agent_recovery_compliance_evidence().non_absolute_path_status
        == native_agent_recovery_compliance_evidence().expected_non_absolute_path_status
    )
