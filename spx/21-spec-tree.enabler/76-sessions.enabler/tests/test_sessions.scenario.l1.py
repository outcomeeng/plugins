"""Scenario evidence for session handoff, pickup, release, and git anchoring."""

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)
from outcomeeng_testing.harnesses.sessions import (
    accepted_session_commands,
    active_node_handoff_payload,
    basic_handoff_payload,
    current_branch,
    issues_handoff_payload,
    plan_handoff_payload,
    session_commands,
    specific_content_handoff_payload,
)


def test_file_appears_in_todo() -> None:
    with accepted_session_commands() as commands:
        result = commands.handoff()

        assert result.returncode == 0, result.stderr
        assert commands.created_session(result).todo_path.exists()


def test_session_file_contains_active_node_path() -> None:
    with accepted_session_commands() as commands:
        payload = active_node_handoff_payload()
        result = commands.handoff(payload)

        assert result.returncode == 0, result.stderr
        assert payload.body in commands.created_session(result).todo_path.read_text()


def test_session_file_records_current_git_ref() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        result = commands.handoff()

        assert result.returncode == 0, result.stderr
        show_result = commands.show(commands.created_session(result))
        assert show_result.returncode == 0, show_result.stderr
        assert commands.parse_git_ref(show_result) == current_branch(repo)


def test_pickup_removes_from_todo() -> None:
    with accepted_session_commands() as commands:
        handoff_result = commands.handoff()
        assert handoff_result.returncode == 0, handoff_result.stderr
        record = commands.created_session(handoff_result)

        pickup_result = commands.pickup(record)

        assert pickup_result.returncode == 0, pickup_result.stderr
        assert not record.todo_path.exists()


def test_pickup_places_in_doing() -> None:
    with accepted_session_commands() as commands:
        handoff_result = commands.handoff()
        assert handoff_result.returncode == 0, handoff_result.stderr
        record = commands.created_session(handoff_result)

        pickup_result = commands.pickup(record)

        assert pickup_result.returncode == 0, pickup_result.stderr
        assert record.doing_path.exists()


def test_pickup_emits_session_content_to_stdout() -> None:
    with accepted_session_commands() as commands:
        payload = active_node_handoff_payload()
        handoff_result = commands.handoff(payload)
        assert handoff_result.returncode == 0, handoff_result.stderr

        pickup_result = commands.pickup(commands.created_session(handoff_result))

        assert pickup_result.returncode == 0, pickup_result.stderr
        assert payload.body in pickup_result.stdout


def test_release_removes_from_doing() -> None:
    with accepted_session_commands() as commands:
        handoff_result = commands.handoff()
        assert handoff_result.returncode == 0, handoff_result.stderr
        record = commands.created_session(handoff_result)
        pickup_result = commands.pickup(record)
        assert pickup_result.returncode == 0, pickup_result.stderr

        release_result = commands.release(record)

        assert release_result.returncode == 0, release_result.stderr
        assert not record.doing_path.exists()


def test_release_places_back_in_todo() -> None:
    with accepted_session_commands() as commands:
        handoff_result = commands.handoff()
        assert handoff_result.returncode == 0, handoff_result.stderr
        record = commands.created_session(handoff_result)
        pickup_result = commands.pickup(record)
        assert pickup_result.returncode == 0, pickup_result.stderr

        release_result = commands.release(record)

        assert release_result.returncode == 0, release_result.stderr
        assert record.todo_path.exists()


def test_release_does_not_modify_content() -> None:
    with accepted_session_commands() as commands:
        handoff_result = commands.handoff(specific_content_handoff_payload())
        assert handoff_result.returncode == 0, handoff_result.stderr
        record = commands.created_session(handoff_result)
        pickup_result = commands.pickup(record)
        assert pickup_result.returncode == 0, pickup_result.stderr
        content_before_release = record.doing_path.read_text()

        release_result = commands.release(record)

        assert release_result.returncode == 0, release_result.stderr
        assert record.todo_path.read_text() == content_before_release


def test_release_multiple_ids_in_single_invocation() -> None:
    with accepted_session_commands() as commands:
        records = []
        for payload in (basic_handoff_payload(), specific_content_handoff_payload()):
            handoff_result = commands.handoff(payload)
            assert handoff_result.returncode == 0, handoff_result.stderr
            record = commands.created_session(handoff_result)
            pickup_result = commands.pickup(record)
            assert pickup_result.returncode == 0, pickup_result.stderr
            records.append(record)

        release_result = commands.release(*records)

        assert release_result.returncode == 0, release_result.stderr
        assert all(not record.doing_path.exists() for record in records)
        assert all(record.todo_path.exists() for record in records)


def test_plan_md_excerpt_preserved() -> None:
    with accepted_session_commands() as commands:
        payload = plan_handoff_payload()
        result = commands.handoff(payload)

        assert result.returncode == 0, result.stderr
        assert payload.body in commands.created_session(result).todo_path.read_text()


def test_issues_md_excerpt_preserved() -> None:
    with accepted_session_commands() as commands:
        payload = issues_handoff_payload()
        result = commands.handoff(payload)

        assert result.returncode == 0, result.stderr
        assert payload.body in commands.created_session(result).todo_path.read_text()


def test_root_checkout_on_branch_records_branch_name() -> None:
    with handoff_git_env() as env, session_commands(env.root) as commands:
        result = commands.handoff()
        assert result.returncode == 0, result.stderr
        show_result = commands.show(commands.created_session(result))

        assert show_result.returncode == 0, show_result.stderr
        assert commands.parse_git_ref(show_result) == env.default_branch


def test_root_checkout_detached_head_records_head_sha() -> None:
    with handoff_git_env() as env:
        env.detach_root()
        with session_commands(env.root) as commands:
            result = commands.handoff()
            assert result.returncode == 0, result.stderr
            show_result = commands.show(commands.created_session(result))

            assert show_result.returncode == 0, show_result.stderr
            assert commands.parse_git_ref(show_result) == env.head_sha()


def test_linked_worktree_at_origin_tip_records_tip_sha() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff()
            assert result.returncode == 0, result.stderr
            show_result = commands.show(commands.created_session(result))

            assert show_result.returncode == 0, show_result.stderr
            assert commands.parse_git_ref(show_result) == env.origin_tip


def test_linked_worktree_on_branch_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_on_branch()) as commands:
            result = commands.handoff()

            assert result.returncode != 0
            assert "SessionHandoffBaseError" in result.stderr
            assert not commands.session_files()


def test_linked_worktree_detached_off_tip_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_detached_off_tip()) as commands:
            result = commands.handoff()

            assert result.returncode != 0
            assert "SessionHandoffBaseError" in result.stderr
            assert not commands.session_files()


def test_explicit_work_branch_ref_records_branch_name() -> None:
    with handoff_git_env() as env:
        work_branch = env.push_work_branch()
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff(work_branch=work_branch)
            assert result.returncode == 0, result.stderr
            show_result = commands.show(commands.created_session(result))

            assert show_result.returncode == 0, show_result.stderr
            assert commands.parse_git_ref(show_result) == work_branch


def test_explicit_work_branch_ref_absent_from_origin_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff(work_branch=env.head_sha())

            assert result.returncode != 0
            assert "SessionWorkBranchNotOnOriginError" in result.stderr
            assert not commands.session_files()
