"""Level-1 property evidence for cross-cutting hygiene idempotence."""

from __future__ import annotations

from hypothesis import given

from outcomeeng.hygiene.clean import SUCCESS_EXIT_CODE, clean
from outcomeeng.hygiene.xml_spacing import fix_file
from outcomeeng_testing.generators.hygiene import (
    CleanWorkspaceCase,
    clean_workspace_cases,
    markdown_contents,
)
from outcomeeng_testing.harnesses.hygiene import (
    HYGIENE_EVIDENCE_REPLAY_PATH,
    SubprocessRunner,
    clean_workspace,
    hygiene_generated_evidence,
    markdown_file,
)


@hygiene_generated_evidence(replay_path=HYGIENE_EVIDENCE_REPLAY_PATH)
@given(content=markdown_contents())
def test_xml_spacing_is_idempotent(content: str) -> None:
    with markdown_file(content) as path:
        fix_file(path)
        first_result = path.read_bytes()

        fix_file(path)

        assert path.read_bytes() == first_result


@hygiene_generated_evidence(replay_path=HYGIENE_EVIDENCE_REPLAY_PATH)
@given(case=clean_workspace_cases())
def test_clean_is_idempotent(case: CleanWorkspaceCase) -> None:
    with clean_workspace(case) as workspace:
        runner = SubprocessRunner(workspace.root)
        first_exit_code = clean(
            runner=runner,
            repo_root=workspace.root,
            active_python_prefix=workspace.active_python_prefix,
        )
        first_result = workspace.snapshot()

        second_exit_code = clean(
            runner=runner,
            repo_root=workspace.root,
            active_python_prefix=workspace.active_python_prefix,
        )

        assert first_exit_code == SUCCESS_EXIT_CODE
        assert second_exit_code == SUCCESS_EXIT_CODE
        assert workspace.snapshot() == first_result
