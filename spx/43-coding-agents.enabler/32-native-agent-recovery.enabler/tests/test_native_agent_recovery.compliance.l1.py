from outcomeeng_testing.harnesses.native_agent_recovery import (
    observe_continuation_boundary,
    observe_correlation_verification,
    observe_launch_settlement,
    observe_native_launch_transport,
    observe_pane_read_barrier,
    observe_path_identity,
    observe_prepare_command_line,
    observe_reassessment_settlement,
)


def test_prepare_emits_a_versioned_durable_manifest() -> None:
    observed = observe_prepare_command_line()
    assert observed.exit_code == 0
    assert observed.rendered_status == observed.prepared_status


def test_native_launch_carries_only_the_exact_resume_command() -> None:
    observed = observe_native_launch_transport()
    assert observed.delivery_texts == observed.expected_resume_commands
    assert observed.deliveries_carrying_boundary == []
    assert observed.deliveries_using_latest_selector == []
    assert observed.claude_command_tail == observed.prepared_claude_locator
    assert observed.codex_command_head == observed.expected_codex_head


def test_only_a_submitted_send_settles_a_native_launch() -> None:
    observed = observe_launch_settlement()
    assert observed.submitted_status == observed.resumed_status
    assert observed.prefilled_status == observed.invalid_schema_status
    assert observed.non_recovery_plan_status == observed.invalid_schema_status


def test_verification_accepts_only_exact_correlation_evidence() -> None:
    observed = observe_correlation_verification()
    assert observed.exact_status == observed.verified_status
    assert observed.verified_count == observed.candidate_count
    assert observed.mismatched_status == observed.correlation_incomplete_status
    assert observed.operator_confirmed_status == observed.correlation_incomplete_status
    assert observed.unexpected_agent_pane_ids == observed.unprepared_pane_ids


def test_reassessment_requires_a_complete_stable_screen_barrier() -> None:
    observed = observe_pane_read_barrier()
    assert observed.incomplete_barrier_status == observed.invalid_schema_status
    assert observed.failed_read_status == observed.command_failed_status
    assert observed.failed_read_deliveries == []
    assert observed.complete_barrier_status == observed.reassessment_ready_status
    assert observed.preserved_reads == observed.supplied_reads


def test_every_continuation_instruction_carries_its_boundary() -> None:
    observed = observe_continuation_boundary()
    assert observed.delivery_texts != []
    assert observed.deliveries_missing_boundary == []
    assert observed.deliveries_carrying_launch_prefix == []


def test_settled_reassessment_is_not_planned_again() -> None:
    observed = observe_reassessment_settlement()
    assert observed.settled_status == observed.reassessment_sent_status
    assert observed.repeated_status == observed.already_current_status
    assert observed.repeated_deliveries == []


def test_prowl_path_identities_are_preserved_verbatim() -> None:
    observed = observe_path_identity()
    assert observed.parsed_worktree_path == observed.supplied_worktree_path
    assert observed.relative_path_status == observed.invalid_schema_status
