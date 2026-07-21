"""Scenario evidence for session handoff, pickup, release, and git anchoring."""

from outcomeeng_testing.generators.sessions import generated_token
from outcomeeng_testing.harnesses.git_context import (
    accepted_git_context,
    handoff_git_env,
)
from outcomeeng_testing.harnesses.sessions import (
    accepted_session_commands,
    current_branch,
    session_commands,
)


def test_handoff_creates_todo_session_with_active_node() -> None:
    with accepted_session_commands() as commands:
        payload = commands.generated_payload()
        result = commands.handoff(payload)

        assert result.returncode == 0, result.stderr
        record = commands.created_session(result)
        assert record.todo_path.exists()
        assert payload.active_node_path in record.todo_path.read_text()


def test_pickup_moves_session_to_doing_and_emits_content() -> None:
    with accepted_session_commands() as commands:
        payload = commands.generated_payload()
        handoff_result = commands.handoff(payload)
        assert handoff_result.returncode == 0, handoff_result.stderr
        record = commands.created_session(handoff_result)

        pickup_result = commands.pickup(record)

        assert pickup_result.returncode == 0, pickup_result.stderr
        assert not record.todo_path.exists()
        assert record.doing_path.exists()
        assert payload.body in pickup_result.stdout


def test_release_moves_batch_to_todo_without_modifying_content() -> None:
    with accepted_session_commands() as commands:
        records = []
        for payload in commands.generated_payload_batch():
            handoff_result = commands.handoff(payload)
            assert handoff_result.returncode == 0, handoff_result.stderr
            record = commands.created_session(handoff_result)
            pickup_result = commands.pickup(record)
            assert pickup_result.returncode == 0, pickup_result.stderr
            records.append((record, record.doing_path.read_text()))

        release_result = commands.release(*(record for record, _ in records))

        assert release_result.returncode == 0, release_result.stderr
        for record, content in records:
            assert not record.doing_path.exists()
            assert record.todo_path.exists()
            assert record.todo_path.read_text() == content


def test_handoff_preserves_coordination_note_content() -> None:
    with accepted_session_commands() as commands:
        payload = commands.generated_payload()
        result = commands.handoff(payload)

        assert result.returncode == 0, result.stderr
        assert (
            payload.coordination_note
            in commands.created_session(result).todo_path.read_text()
        )


def test_root_branch_handoff_records_branch_name() -> None:
    with accepted_git_context() as repo, session_commands(repo) as commands:
        result = commands.handoff()

        assert result.returncode == 0, result.stderr
        show_result = commands.show(commands.created_session(result))
        assert show_result.returncode == 0, show_result.stderr
        assert commands.parse_git_ref(show_result) == current_branch(repo)


def test_detached_root_handoff_records_head_sha() -> None:
    with handoff_git_env() as env:
        env.detach_root()
        with session_commands(env.root) as commands:
            result = commands.handoff()

            assert result.returncode == 0, result.stderr
            show_result = commands.show(commands.created_session(result))
            assert show_result.returncode == 0, show_result.stderr
            assert commands.parse_git_ref(show_result) == env.head_sha()


def test_linked_tip_handoff_records_tip_sha() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff()

            assert result.returncode == 0, result.stderr
            show_result = commands.show(commands.created_session(result))
            assert show_result.returncode == 0, show_result.stderr
            assert commands.parse_git_ref(show_result) == env.origin_tip


def test_linked_branch_handoff_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_on_branch(generated_token())) as commands:
            result = commands.handoff()

            assert result.returncode != 0
            assert not commands.session_files()


def test_linked_off_tip_handoff_is_refused() -> None:
    with handoff_git_env() as env:
        with session_commands(env.linked_detached_off_tip()) as commands:
            result = commands.handoff()

            assert result.returncode != 0
            assert not commands.session_files()


def test_explicit_work_branch_is_recorded() -> None:
    with handoff_git_env() as env:
        work_branch = env.push_work_branch(generated_token())
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff(work_branch=work_branch)

            assert result.returncode == 0, result.stderr
            show_result = commands.show(commands.created_session(result))
            assert show_result.returncode == 0, show_result.stderr
            assert commands.parse_git_ref(show_result) == work_branch


def test_absent_work_branch_is_refused() -> None:
    with handoff_git_env() as env:
        absent_branch = f"{env.default_branch}-{generated_token()}"
        with session_commands(env.linked_at_origin_tip()) as commands:
            result = commands.handoff(work_branch=absent_branch)

            assert result.returncode != 0
            assert not commands.session_files()
