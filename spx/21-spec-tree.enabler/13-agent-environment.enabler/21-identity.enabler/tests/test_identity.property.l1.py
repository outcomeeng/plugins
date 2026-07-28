"""Property evidence for SessionStart identity export."""

from hypothesis import given

from outcomeeng.validation.hook_contract import session_start_payload
from outcomeeng_testing.generators.hooks import session_ids
from outcomeeng_testing.harnesses.hooks import (
    hook_generated_evidence,
    run_session_start,
    session_start_workspace,
)


@hook_generated_evidence
@given(session_id=session_ids())
def test_uuid_session_ids_are_exported_exactly(session_id: str) -> None:
    with session_start_workspace() as (project_dir, env_file):
        result = run_session_start(
            session_start_payload(
                session_id=session_id,
                current_working_directory=project_dir,
            ),
            env_file=env_file,
            project_dir=project_dir,
        )
        assert result.returncode == 0
        assert f"export CLAUDE_SESSION_ID={session_id}" in env_file.read_text(
            encoding="utf-8"
        )
