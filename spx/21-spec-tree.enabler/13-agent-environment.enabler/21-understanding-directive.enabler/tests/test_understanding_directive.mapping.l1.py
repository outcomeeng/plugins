"""Mapping tests for 21-understanding-directive.enabler (understanding-directive.md mapping).

L1: the real `session-start.py` hook is run as a subprocess against real
filesystem I/O in pytest tmp_path directories, with no test doubles.

Assertion covered:
  - A project directory maps to the understanding-directive output: a directory
    containing spx/*.product.md maps to a directive naming /spec-tree:understand;
    a directory without one maps to no directive.
"""

import pytest

from outcomeeng_testing.harnesses.hooks import run_session_start

SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


@pytest.mark.parametrize("has_product_spec", [True, False])
def test_product_spec_presence_maps_to_directive(has_product_spec, tmp_path):
    if has_product_spec:
        spx = tmp_path / "spx"
        spx.mkdir()
        (spx / "demo.product.md").write_text("# Demo product\n", encoding="utf-8")
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    # Directive token asserted inline; source-ownership tracked cross-hook in
    # spx/21-spec-tree.enabler/ISSUES.md item 20.
    assert ("/spec-tree:understand" in result.stdout) is has_product_spec
