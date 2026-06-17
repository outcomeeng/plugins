"""Scenario tests for 21-understanding-directive.enabler (understanding-directive.md scenario).

L1: the real `session-start.py` hook is run as a subprocess against real
filesystem I/O in pytest tmp_path directories, with no test doubles.

Assertion covered:
  - A project directory containing a product spec yields a stdout directive
    naming /spec-tree:understand and /spec-tree:contextualize.
"""

from pathlib import Path

from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def _make_spec_tree(root: Path) -> None:
    spx = root / "spx"
    spx.mkdir()
    (spx / "demo.product.md").write_text("# Demo product\n", encoding="utf-8")


def test_spec_tree_repo_emits_understanding_directive(tmp_path):
    _make_spec_tree(tmp_path)
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    # Directive marker and command tokens asserted inline; their source-ownership
    # is tracked cross-hook in spx/21-spec-tree.enabler/ISSUES.md item 20.
    assert '<SPEC-TREE_SESSION_START foundation="load"/>' in result.stdout
    assert "/spec-tree:understand" in result.stdout
    assert "/spec-tree:contextualize" in result.stdout
    # The directive points at the mechanical PreToolUse gate as the enforcement,
    # not at itself — SessionStart stdout alone is out-prioritized after compaction.
    assert "PreToolUse" in result.stdout
