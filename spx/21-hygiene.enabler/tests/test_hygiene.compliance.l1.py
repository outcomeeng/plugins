"""Level-1 compliance evidence for cross-cutting hygiene target safety."""

from __future__ import annotations

from hypothesis import given

from outcomeeng.hygiene.clean import SUCCESS_EXIT_CODE, clean
from outcomeeng.hygiene.xml_spacing import fix_file
from outcomeeng_testing.generators.hygiene import (
    CleanWorkspaceCase,
    XmlSpacingWorkspaceCase,
    clean_workspace_cases,
    xml_spacing_workspace_cases,
)
from outcomeeng_testing.harnesses.hygiene import (
    HYGIENE_EVIDENCE_REPLAY_PATH,
    SubprocessRunner,
    clean_workspace,
    hygiene_generated_evidence,
    xml_spacing_workspace,
)


@hygiene_generated_evidence(replay_path=HYGIENE_EVIDENCE_REPLAY_PATH)
@given(case=clean_workspace_cases())
def test_clean_removes_only_ignored_paths(case: CleanWorkspaceCase) -> None:
    with clean_workspace(case) as workspace:
        tracked_before = workspace.tracked_bytes()
        untracked_before = workspace.untracked_bytes()

        exit_code = clean(
            runner=SubprocessRunner(workspace.root),
            repo_root=workspace.root,
            active_python_prefix=workspace.active_python_prefix,
        )

        assert exit_code == SUCCESS_EXIT_CODE
        assert workspace.tracked_bytes() == tracked_before
        assert workspace.untracked_bytes() == untracked_before
        assert all(not path.exists() for path in workspace.ignored_paths)


@hygiene_generated_evidence(replay_path=HYGIENE_EVIDENCE_REPLAY_PATH)
@given(case=xml_spacing_workspace_cases())
def test_xml_spacing_preserves_non_target_bytes(
    case: XmlSpacingWorkspaceCase,
) -> None:
    with xml_spacing_workspace(case) as workspace:
        non_target_before = workspace.non_target_path.read_bytes()

        fix_file(workspace.target_path)

        assert workspace.non_target_path.read_bytes() == non_target_before
