"""Scenario evidence for ``spx/21-spec-tree.enabler/76-sessions.enabler``."""

from outcomeeng_testing.harnesses.session_scenarios import (
    archive_moves_todo_session_to_archive,
    explicit_work_branch_ref_absent_from_origin_is_refused,
    explicit_work_branch_ref_records_branch_name,
    handoff_preserves_incorporated_session_reference,
    handoff_file_appears_in_todo,
    handoff_preserves_full_body_payload,
    issues_md_excerpt_preserved,
    linked_worktree_at_origin_tip_records_tip_sha,
    linked_worktree_detached_off_tip_is_refused,
    linked_worktree_on_branch_is_refused,
    pickup_emits_session_content_to_stdout,
    pickup_places_in_doing,
    pickup_removes_from_todo,
    plan_md_excerpt_preserved,
    release_does_not_modify_content,
    release_multiple_ids_in_single_invocation,
    release_places_back_in_todo,
    release_removes_from_doing,
    root_checkout_detached_head_records_head_sha,
    root_checkout_on_branch_records_branch_name,
    session_file_contains_active_node_path,
    session_file_records_current_git_ref,
)


def test_handoff_file_appears_in_todo() -> None:
    assert handoff_file_appears_in_todo()


def test_session_file_contains_active_node_path() -> None:
    assert session_file_contains_active_node_path()


def test_session_file_records_current_git_ref() -> None:
    assert session_file_records_current_git_ref()


def test_handoff_preserves_full_body_payload() -> None:
    assert handoff_preserves_full_body_payload()


def test_pickup_removes_from_todo() -> None:
    assert pickup_removes_from_todo()


def test_pickup_places_in_doing() -> None:
    assert pickup_places_in_doing()


def test_pickup_emits_session_content_to_stdout() -> None:
    assert pickup_emits_session_content_to_stdout()


def test_release_removes_from_doing() -> None:
    assert release_removes_from_doing()


def test_release_places_back_in_todo() -> None:
    assert release_places_back_in_todo()


def test_release_does_not_modify_content() -> None:
    assert release_does_not_modify_content()


def test_release_multiple_ids_in_single_invocation() -> None:
    assert release_multiple_ids_in_single_invocation()


def test_archive_moves_todo_session_to_archive() -> None:
    assert archive_moves_todo_session_to_archive()


def test_handoff_preserves_incorporated_session_reference() -> None:
    assert handoff_preserves_incorporated_session_reference()


def test_plan_md_excerpt_preserved() -> None:
    assert plan_md_excerpt_preserved()


def test_issues_md_excerpt_preserved() -> None:
    assert issues_md_excerpt_preserved()


def test_root_checkout_on_branch_records_branch_name() -> None:
    assert root_checkout_on_branch_records_branch_name()


def test_root_checkout_detached_head_records_head_sha() -> None:
    assert root_checkout_detached_head_records_head_sha()


def test_linked_worktree_at_origin_tip_records_tip_sha() -> None:
    assert linked_worktree_at_origin_tip_records_tip_sha()


def test_linked_worktree_on_branch_is_refused() -> None:
    assert linked_worktree_on_branch_is_refused()


def test_linked_worktree_detached_off_tip_is_refused() -> None:
    assert linked_worktree_detached_off_tip_is_refused()


def test_explicit_work_branch_ref_records_branch_name() -> None:
    assert explicit_work_branch_ref_records_branch_name()


def test_explicit_work_branch_ref_absent_from_origin_is_refused() -> None:
    assert explicit_work_branch_ref_absent_from_origin_is_refused()
