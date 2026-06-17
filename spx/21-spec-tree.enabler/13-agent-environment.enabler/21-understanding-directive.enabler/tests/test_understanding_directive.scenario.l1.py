"""Scenario test for 21-understanding-directive.enabler (understanding-directive.md scenario).

L1: runs ``spx hooks session-start`` as a subprocess against real filesystem I/O in
pytest ``tmp_path`` directories and parses its JSON document — asserting on the
descriptor key values, never by scanning stdout for substrings.

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

SESSION_ID = "11111111-2222-3333-4444-555555555555"


def test_product_spec_yields_understanding_directive(tmp_path: Path) -> None:
    make_spec_tree(tmp_path)
    result = run_session_start(
        {"session_id": SESSION_ID, "cwd": str(tmp_path)},
        env_file=tmp_path / "claude.env",
        project_dir=tmp_path,
    )
    assert result.returncode == 0
    document = hook_document(result)
    assert directive_of_kind(document, "understanding") is not None
