"""Scenario evidence: the reference-portability validator's report and exit behavior.

Spec: spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md

The validator reads a file from disk and, on a non-portable reference, reports the file,
line, and reference and exits non-zero; on portable-only content it reports nothing and
exits zero. The discriminating reference comes from the source-owned detector under test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.validation.reference_portability import main, scan_file


def test_violation_is_reported_with_file_line_and_reference_and_exits_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "# Heading\n\nRead spx/13-plugin-and-runtime-conventions.adr.md first.\n",
        encoding="utf-8",
    )

    violations = scan_file(skill)
    assert len(violations) == 1
    assert violations[0].line == 3
    assert violations[0].reference.startswith("spx/13-")

    exit_code = main([str(skill)])
    assert exit_code != 0
    out = capsys.readouterr().out
    assert str(skill) in out
    assert ":3" in out


def test_portable_content_reports_nothing_and_exits_zero(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "# Heading\n\nRead spx/{node-path}/{slug}.md via ${CLAUDE_SKILL_DIR}.\n",
        encoding="utf-8",
    )
    assert scan_file(skill) == []
    assert main([str(skill)]) == 0
