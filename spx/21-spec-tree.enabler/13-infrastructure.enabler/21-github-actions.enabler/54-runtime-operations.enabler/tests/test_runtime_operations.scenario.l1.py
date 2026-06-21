"""Tests verifying github-actions SKILL.md instructs the agent in the documented shape for runtime operations.

These checks parse SKILL.md prose blocks and assert on the documented step content; they do not
simulate full agent execution.
"""

from __future__ import annotations

import pathlib
import re

import pytest

MARKETPLACE_ROOT = pathlib.Path(__file__).resolve().parents[6]
SKILL_MD = (
    MARKETPLACE_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "inspect-github-actions"
    / "SKILL.md"
)


@pytest.fixture(scope="module")
def skill_md_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def _step_block(skill_md_text: str, step_name: str) -> str:
    match = re.search(
        rf'<step name="{re.escape(step_name)}">(.*?)</step>',
        skill_md_text,
        re.DOTALL,
    )
    assert match is not None, f'SKILL.md missing <step name="{step_name}"> block'
    return match.group(1)


def test_status_request_names_required_fields_in_order(skill_md_text: str) -> None:
    """SKILL.md's report_status step lists repository, branch, run id, workflow name, status, conclusion, and commit SHA in that order before narrative."""
    block = _step_block(skill_md_text, "report_status")

    expected = (
        (1, "repository"),
        (2, "branch"),
        (3, "run id"),
        (4, "workflow name"),
        (5, "status"),
        (6, "conclusion"),
        (7, "commit sha"),
    )
    positions: list[int] = []
    for n, field in expected:
        pattern = rf"{n}\.\s+{re.escape(field)}"
        match = re.search(pattern, block, re.IGNORECASE)
        assert match is not None, (
            f"report_status block missing numbered entry: {n}. {field!r}"
        )
        positions.append(match.start())

    assert positions == sorted(positions), (
        f"report_status fields out of declared order: positions={positions}"
    )


def test_failure_triage_runs_log_failed_first(skill_md_text: str) -> None:
    """SKILL.md's triage_failure step shows `--log-failed` before any unqualified `--log` and names failing job, failing step, and error excerpt as required surface elements."""
    block = _step_block(skill_md_text, "triage_failure")

    log_failed_idx = block.find("--log-failed")
    assert log_failed_idx >= 0, "triage_failure block must include --log-failed"

    unqualified_log = re.search(r"--log(?!-failed)", block)
    if unqualified_log is not None:
        assert log_failed_idx < unqualified_log.start(), (
            "triage_failure block must show --log-failed before any unqualified --log"
        )

    block_lower = block.lower()
    for required in ("failing job", "failing step", "error excerpt"):
        assert required in block_lower, (
            f"triage_failure block missing required surface element: {required!r}"
        )


def test_tty_branch_lists_accounts_and_prompts(skill_md_text: str) -> None:
    """SKILL.md's orient step handles both is_tty=true (ask_user runtime token + `gh auth switch -u <account>`) and is_tty=false (manual remediation, no prompt) branches."""
    block = _step_block(skill_md_text, "orient")
    block_lower = block.lower()

    assert re.search(r"is_tty[^\n]+true", block), (
        "orient block must explicitly handle the is_tty=true branch"
    )
    assert re.search(r"is_tty[^\n]+false", block), (
        "orient block must explicitly handle the is_tty=false branch"
    )
    assert "tool('ask_user')" in block, (
        "orient block's TTY branch must prompt the user via the ask_user runtime token"
    )
    assert "gh auth switch -u" in block, (
        "orient block must mention `gh auth switch -u <account>` for the TTY branch"
    )
    assert "available_accounts" in block, (
        "orient block must reference the available_accounts list returned by gh_access.py"
    )
    assert "manual remediation" in block_lower, (
        "orient block's non-TTY branch must mention manual remediation"
    )
