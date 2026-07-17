"""Scenario evidence for session handoff, pickup, release, and git anchoring.

The real ``spx`` binary, real git repositories, and isolated filesystem state
provide ``l1`` behavior. ``outcomeeng_testing.harnesses.sessions`` owns command
orchestration, payload construction, parsing, and reusable scenario inputs.
"""

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)
from outcomeeng_testing.harnesses.sessions import (
    ABSENT_WORK_BRANCH,
    ACTIVE_NODE,
    ACTIVE_NODE_BODY,
    DOING_QUEUE,
    HANDOFF_BASE_ERROR,
    ISSUES_BODY,
    ISSUES_EXCERPT,
    PLAN_BODY,
    PLAN_EXCERPT,
    SESSION_BODY,
    SINGLE_RESULT_COUNT,
    SPECIFIC_CONTENT_BODY,
    SUCCESS_EXIT,
    TODO_QUEUE,
    WORK_BRANCH_NOT_ON_ORIGIN_ERROR,
    current_branch,
    session_commands,
)


def test_file_appears_in_todo() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        result = commands.handoff(ACTIVE_NODE_BODY)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert len(commands.queue_files(TODO_QUEUE)) == SINGLE_RESULT_COUNT


def test_session_file_contains_active_node_path() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        result = commands.handoff(ACTIVE_NODE_BODY)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert ACTIVE_NODE in commands.queue_files(TODO_QUEUE)[0].read_text()


def test_session_file_records_current_git_ref() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        result = commands.handoff(ACTIVE_NODE_BODY)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert commands.git_ref(commands.session_file(result.stdout)) == current_branch(
            repo
        )


def test_pickup_removes_from_todo() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        session_id = commands.handoff_id(commands.handoff().stdout)

        result = commands.pickup(session_id)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert not commands.session_path(TODO_QUEUE, session_id).exists()


def test_pickup_places_in_doing() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        session_id = commands.handoff_id(commands.handoff().stdout)

        result = commands.pickup(session_id)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert commands.session_path(DOING_QUEUE, session_id).exists()


def test_pickup_emits_session_content_to_stdout() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        session_id = commands.handoff_id(commands.handoff(ACTIVE_NODE_BODY).stdout)

        result = commands.pickup(session_id)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert ACTIVE_NODE in result.stdout


def test_release_removes_from_doing() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        session_id = commands.create_and_pickup()

        result = commands.release(session_id)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert not commands.session_path(DOING_QUEUE, session_id).exists()


def test_release_places_back_in_todo() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        session_id = commands.create_and_pickup()

        result = commands.release(session_id)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert commands.session_path(TODO_QUEUE, session_id).exists()


def test_release_does_not_modify_content() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        session_id = commands.create_and_pickup(SPECIFIC_CONTENT_BODY)
        content_in_doing = commands.session_path(DOING_QUEUE, session_id).read_text()

        result = commands.release(session_id)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert (
            commands.session_path(TODO_QUEUE, session_id).read_text()
            == content_in_doing
        )


def test_release_multiple_ids_in_single_invocation() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        session_ids = commands.create_picked_up_batch()

        result = commands.release(*session_ids)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        for session_id in session_ids:
            assert not commands.session_path(DOING_QUEUE, session_id).exists()
            assert commands.session_path(TODO_QUEUE, session_id).exists()


def test_plan_md_excerpt_preserved() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        result = commands.handoff(PLAN_BODY)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert PLAN_EXCERPT in commands.queue_files(TODO_QUEUE)[0].read_text()


def test_issues_md_excerpt_preserved() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        result = commands.handoff(ISSUES_BODY)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert ISSUES_EXCERPT in commands.queue_files(TODO_QUEUE)[0].read_text()


def test_root_checkout_on_branch_records_branch_name() -> None:
    with handoff_git_env() as env, session_commands(env.root) as commands:
        result = commands.handoff(SESSION_BODY)

        assert result.returncode == SUCCESS_EXIT, result.stderr
        assert (
            commands.git_ref(commands.session_file(result.stdout)) == env.default_branch
        )


def test_root_checkout_detached_head_records_head_sha() -> None:
    with handoff_git_env() as env:
        env.detach_root()
        with session_commands(env.root) as commands:
            result = commands.handoff(SESSION_BODY)

            assert result.returncode == SUCCESS_EXIT, result.stderr
            assert (
                commands.git_ref(commands.session_file(result.stdout)) == env.head_sha()
            )


def test_linked_worktree_at_origin_tip_records_tip_sha() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff(SESSION_BODY)

            assert result.returncode == SUCCESS_EXIT, result.stderr
            assert (
                commands.git_ref(commands.session_file(result.stdout)) == env.origin_tip
            )


def test_linked_worktree_on_branch_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_on_branch()) as commands:
            result = commands.handoff(SESSION_BODY)

            assert result.returncode != SUCCESS_EXIT
            assert HANDOFF_BASE_ERROR in result.stderr
            assert not commands.queue_files(TODO_QUEUE)


def test_linked_worktree_detached_off_tip_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_detached_off_tip()) as commands:
            result = commands.handoff(SESSION_BODY)

            assert result.returncode != SUCCESS_EXIT
            assert HANDOFF_BASE_ERROR in result.stderr
            assert not commands.queue_files(TODO_QUEUE)


def test_explicit_work_branch_ref_records_branch_name() -> None:
    with handoff_git_env() as env:
        work_branch = env.push_work_branch()
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff(SESSION_BODY, git_ref=work_branch)

            assert result.returncode == SUCCESS_EXIT, result.stderr
            assert commands.git_ref(commands.session_file(result.stdout)) == work_branch


def test_explicit_work_branch_ref_absent_from_origin_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff(SESSION_BODY, git_ref=ABSENT_WORK_BRANCH)

            assert result.returncode != SUCCESS_EXIT
            assert WORK_BRANCH_NOT_ON_ORIGIN_ERROR in result.stderr
            assert not commands.queue_files(TODO_QUEUE)
