"""Scenario test for 21-base-currency.enabler (base-currency.md scenario).

L1: runs ``spx hooks session-start`` as a subprocess against real git
repositories in pytest ``tmp_path`` directories (fixtures from
``outcomeeng_testing.harnesses.git_context``) and parses its JSON document.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

from outcomeeng_testing.harnesses.git_context import worktree_against_origin
from outcomeeng_testing.harnesses.hooks import (
    directive_of_kind,
    hook_document,
    run_session_start,
)

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_behind_default_emits_base_currency_directive(tmp_path) -> None:
    behind = 2
    default_branch = "main"
    with worktree_against_origin(behind=behind, default_branch=default_branch) as repo:
        result = run_session_start(
            {"session_id": SESSION_ID, "cwd": str(repo)},
            env_file=tmp_path / "claude.env",
            project_dir=repo,
        )
    assert result.returncode == 0
    directive = directive_of_kind(hook_document(result), "base-currency")
    assert directive is not None
    assert directive["behind_count"] == behind
    assert directive["default_branch"] == f"origin/{default_branch}"
