"""Compliance test for 21-understanding-directive.enabler (understanding-directive.md compliance).

L1: detect a spec-tree repository by the presence of ``spx/*.product.md``, never
from ``.spx/`` state. Asserts on the parsed JSON descriptor.

Excluded until ``@outcomeeng/spx`` publishes ``spx hooks session-start``
(``spx/EXCLUDE``).
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.hooks import (
    directive_of_kind,
    hook_document,
    make_spec_tree,
    run_session_start,
)

SESSION_ID = "cccccccc-dddd-eeee-ffff-000000000000"


def test_spx_state_without_product_spec_does_not_trigger(tmp_path: Path) -> None:
    # `.spx/` operational state present, but no `spx/*.product.md`: detection must
    # not key on `.spx/`, so no understanding directive is emitted.
    (tmp_path / ".spx" / "sessions").mkdir(parents=True)
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert directive_of_kind(hook_document(result), "understanding") is None


def test_product_spec_triggers_detection(tmp_path: Path) -> None:
    make_spec_tree(tmp_path)
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert directive_of_kind(hook_document(result), "understanding") is not None
