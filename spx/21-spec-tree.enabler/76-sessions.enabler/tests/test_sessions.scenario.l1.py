"""Scenario evidence for session handoff, pickup, release, and git anchoring.

The real ``spx`` binary, real git repositories, inert whole-payload fixtures,
and isolated filesystem state provide the ``l1`` behavior and oracles.
"""

from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)
from outcomeeng_testing.harnesses.sessions import (
    active_node_handoff_payload,
    basic_handoff_payload,
    current_branch,
    issues_handoff_payload,
    plan_handoff_payload,
    session_commands,
    specific_content_handoff_payload,
)


def test_file_appears_in_todo() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.created_session(commands.handoff())

        assert record.initial_path.exists()


def test_session_file_contains_active_node_path() -> None:
    payload = active_node_handoff_payload()
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.created_session(commands.handoff(payload))

        assert payload.body in record.initial_path.read_text()


def test_session_file_records_current_git_ref() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.created_session(commands.handoff())

        assert commands.git_ref(record) == current_branch(repo)


def test_pickup_removes_from_todo() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.created_session(commands.handoff())

        result = commands.pickup(record)

        assert commands.succeeded(result), result.stderr
        assert not record.initial_path.exists()


def test_pickup_places_in_doing() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.created_session(commands.handoff())

        result = commands.pickup(record)

        assert commands.succeeded(result), result.stderr
        assert commands.locate(record).parent != record.initial_path.parent


def test_pickup_emits_session_content_to_stdout() -> None:
    payload = active_node_handoff_payload()
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.created_session(commands.handoff(payload))

        result = commands.pickup(record)

        assert commands.succeeded(result), result.stderr
        assert payload.body in result.stdout


def test_release_removes_from_doing() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.create_and_pickup()
        active_path = commands.locate(record)

        result = commands.release(record)

        assert commands.succeeded(result), result.stderr
        assert not active_path.exists()


def test_release_places_back_in_todo() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.create_and_pickup()

        result = commands.release(record)

        assert commands.succeeded(result), result.stderr
        assert commands.locate(record).parent == record.initial_path.parent


def test_release_does_not_modify_content() -> None:
    payload = specific_content_handoff_payload()
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.create_and_pickup(payload)
        content_in_active_queue = commands.locate(record).read_text()

        result = commands.release(record)

        assert commands.succeeded(result), result.stderr
        assert commands.locate(record).read_text() == content_in_active_queue


def test_release_multiple_ids_in_single_invocation() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        records = commands.create_picked_up_batch()
        active_paths = tuple(commands.locate(record) for record in records)

        result = commands.release(*records)

        assert commands.succeeded(result), result.stderr
        assert all(not path.exists() for path in active_paths)
        assert all(
            commands.locate(record).parent == record.initial_path.parent
            for record in records
        )


def test_plan_md_excerpt_preserved() -> None:
    payload = plan_handoff_payload()
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.created_session(commands.handoff(payload))

        assert payload.body in record.initial_path.read_text()


def test_issues_md_excerpt_preserved() -> None:
    payload = issues_handoff_payload()
    with accepted_git_context() as repo, session_commands(repo) as commands:
        record = commands.created_session(commands.handoff(payload))

        assert payload.body in record.initial_path.read_text()


def test_root_checkout_on_branch_records_branch_name() -> None:
    with handoff_git_env() as env, session_commands(env.root) as commands:
        record = commands.created_session(commands.handoff(basic_handoff_payload()))

        assert commands.git_ref(record) == env.default_branch


def test_root_checkout_detached_head_records_head_sha() -> None:
    with handoff_git_env() as env:
        env.detach_root()
        with session_commands(env.root) as commands:
            record = commands.created_session(commands.handoff())

            assert commands.git_ref(record) == env.head_sha()


def test_linked_worktree_at_origin_tip_records_tip_sha() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_at_origin_tip()) as commands:
            record = commands.created_session(commands.handoff())

            assert commands.git_ref(record) == env.origin_tip


def test_linked_worktree_on_branch_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_on_branch()) as commands:
            result = commands.handoff()

            assert not commands.succeeded(result)
            assert result.stderr
            assert not commands.session_files()


def test_linked_worktree_detached_off_tip_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_detached_off_tip()) as commands:
            result = commands.handoff()

            assert not commands.succeeded(result)
            assert result.stderr
            assert not commands.session_files()


def test_explicit_work_branch_ref_records_branch_name() -> None:
    with handoff_git_env() as env:
        work_branch = env.push_work_branch()
        with session_commands(env.linked_at_origin_tip()) as commands:
            record = commands.created_session(commands.handoff(work_branch=work_branch))

            assert commands.git_ref(record) == work_branch


def test_explicit_work_branch_ref_absent_from_origin_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff(work_branch=env.head_sha())

            assert not commands.succeeded(result)
            assert result.stderr
            assert not commands.session_files()
