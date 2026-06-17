"""Compliance tests for 21-understanding-directive.enabler (understanding-directive.md compliance).

L1: the real `session-start.py` hook is run as a subprocess against real
filesystem I/O in pytest tmp_path directories, with no test doubles.

Assertion covered:
  - The hook detects a spec-tree repository by the presence of spx/*.product.md,
    never from .spx/ state or other heuristics.

The `/spec-tree:understand` directive token is asserted inline here; its
source-ownership is tracked cross-hook in spx/21-spec-tree.enabler/ISSUES.md item 20.
"""

from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "cccccccc-dddd-eeee-ffff-000000000000"


def test_spx_state_without_product_spec_does_not_trigger(tmp_path):
    # .spx/ operational state present, but no spx/*.product.md: detection must
    # not key on .spx/, so no directive is emitted.
    (tmp_path / ".spx" / "sessions").mkdir(parents=True)
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert "/spec-tree:understand" not in result.stdout


def test_product_spec_triggers_detection(tmp_path):
    spx = tmp_path / "spx"
    spx.mkdir()
    (spx / "demo.product.md").write_text("# Demo product\n", encoding="utf-8")
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert "/spec-tree:understand" in result.stdout
