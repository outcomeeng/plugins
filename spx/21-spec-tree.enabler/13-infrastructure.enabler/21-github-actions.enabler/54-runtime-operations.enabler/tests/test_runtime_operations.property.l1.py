"""Property tests for github-actions SKILL.md run-selection guidance."""

from __future__ import annotations

import pathlib
import re

import pytest

MARKETPLACE_ROOT = pathlib.Path(__file__).resolve().parents[6]
SKILL_MD = (
    MARKETPLACE_ROOT
    / "plugins"
    / "spec-tree"
    / "skills"
    / "github-actions"
    / "SKILL.md"
)


@pytest.fixture(scope="module")
def skill_md_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_run_selection_names_identifiers_and_default_rule(skill_md_text: str) -> None:
    """SKILL.md's select_run step enumerates run id, pull request, commit SHA, and branch identifier forms plus a default rule that names the active branch and HEAD."""
    match = re.search(
        r'<step name="select_run">(.*?)</step>',
        skill_md_text,
        re.DOTALL,
    )
    assert match is not None, 'SKILL.md missing <step name="select_run"> block'
    block = match.group(1)
    block_lower = block.lower()

    for identifier in ("run id", "pull request", "commit sha", "branch"):
        assert identifier in block_lower, (
            f"select_run block missing identifier type: {identifier!r}"
        )

    assert "default" in block_lower, (
        "select_run block must name the default selection rule explicitly"
    )
    assert "active branch" in block_lower, (
        "select_run block must reference the active branch in the default rule"
    )
    assert "head" in block_lower, (
        "select_run block must reference HEAD in the default rule"
    )
