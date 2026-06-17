"""Mapping test for 21-understanding-directive.enabler (understanding-directive.md mapping).

L1: a project directory maps to the understanding directive — present when an
``spx/*.product.md`` product spec exists, absent otherwise. Asserts on the parsed
JSON descriptor, never by scanning stdout.

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

SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def test_product_spec_maps_to_understanding_directive(tmp_path: Path) -> None:
    make_spec_tree(tmp_path)
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert directive_of_kind(hook_document(result), "understanding") is not None


def test_no_product_spec_maps_to_no_understanding_directive(tmp_path: Path) -> None:
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    assert directive_of_kind(hook_document(result), "understanding") is None
