"""Scenario evidence for session handoff, pickup, release, and git anchoring."""

from outcomeeng_testing.harnesses.sessions import (
    absent_work_branch_is_refused,
    detached_root_handoff_records_head,
    explicit_work_branch_is_recorded,
    handoff_creates_session_file,
    handoff_preserves_active_node,
    handoff_preserves_issue_content,
    handoff_preserves_plan_content,
    handoff_records_current_branch,
    linked_branch_handoff_is_refused,
    linked_off_tip_handoff_is_refused,
    linked_tip_handoff_records_tip,
    pickup_emits_session_body,
    pickup_moves_to_active_queue,
    pickup_removes_initial_file,
    release_batch_returns_to_initial_queue,
    release_preserves_content,
    release_removes_active_file,
    release_returns_to_initial_queue,
    root_branch_handoff_records_branch,
)


def test_file_appears_in_todo() -> None:
    assert handoff_creates_session_file()


def test_session_file_contains_active_node_path() -> None:
    assert handoff_preserves_active_node()


def test_session_file_records_current_git_ref() -> None:
    assert handoff_records_current_branch()


def test_pickup_removes_from_todo() -> None:
    assert pickup_removes_initial_file()


def test_pickup_places_in_doing() -> None:
    assert pickup_moves_to_active_queue()


def test_pickup_emits_session_content_to_stdout() -> None:
    assert pickup_emits_session_body()


def test_release_removes_from_doing() -> None:
    assert release_removes_active_file()


def test_release_places_back_in_todo() -> None:
    assert release_returns_to_initial_queue()


def test_release_does_not_modify_content() -> None:
    assert release_preserves_content()


def test_release_multiple_ids_in_single_invocation() -> None:
    assert release_batch_returns_to_initial_queue()


def test_plan_md_excerpt_preserved() -> None:
    assert handoff_preserves_plan_content()


def test_issues_md_excerpt_preserved() -> None:
    assert handoff_preserves_issue_content()


def test_root_checkout_on_branch_records_branch_name() -> None:
    assert root_branch_handoff_records_branch()


def test_root_checkout_detached_head_records_head_sha() -> None:
    assert detached_root_handoff_records_head()


def test_linked_worktree_at_origin_tip_records_tip_sha() -> None:
    assert linked_tip_handoff_records_tip()


def test_linked_worktree_on_branch_is_refused() -> None:
    assert linked_branch_handoff_is_refused()


def test_linked_worktree_detached_off_tip_is_refused() -> None:
    assert linked_off_tip_handoff_is_refused()


def test_explicit_work_branch_ref_records_branch_name() -> None:
    assert explicit_work_branch_is_recorded()


def test_explicit_work_branch_ref_absent_from_origin_is_refused() -> None:
    assert absent_work_branch_is_refused()
