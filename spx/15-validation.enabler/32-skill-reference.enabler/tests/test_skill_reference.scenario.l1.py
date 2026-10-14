"""Level 1 scenario evidence for skill-reference validation.

Each test is one interaction declared by an assertion of
[skill-reference.md](../skill-reference.md).
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.skill_reference import (
    build_marketplace,
    run_validator,
    write_file,
)


def test_shipped_references_report_nothing_and_exit_zero(tmp_path: Path) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget", "author-widget"]})
    content = write_file(
        tmp_path,
        "src/plugins/alpha/notes.md",
        "Run alpha:audit-widget first.\nThen invoke /author-widget on the result.\n",
    )

    run = run_validator(tmp_path, [content])

    assert run.lines == ()
    assert run.exit_code == 0


def test_unshipped_reference_reports_file_line_and_reference(tmp_path: Path) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    content = write_file(
        tmp_path,
        "src/plugins/alpha/notes.md",
        "Run alpha:audit-widget first.\n\nThen run alpha:audit-gadget.\n",
    )

    run = run_validator(tmp_path, [content])

    assert run.exit_code != 0
    (report,) = run.lines
    assert str(content) in report
    assert ":3:" in report
    assert "alpha:audit-gadget" in report


def test_unmatched_placeholder_and_alternation_member_report_expansion(
    tmp_path: Path,
) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    content = write_file(
        tmp_path,
        "src/plugins/alpha/notes.md",
        "Use /review-{type} when asked.\nThen use /audit-{widget|gadget} as well.\n",
    )

    run = run_validator(tmp_path, [content])

    assert run.exit_code != 0
    placeholder_report, alternation_report = run.lines
    assert str(content) in placeholder_report
    assert ":1:" in placeholder_report
    assert "/review-{type}" in placeholder_report
    assert str(content) in alternation_report
    assert ":2:" in alternation_report
    assert "/audit-{widget|gadget}" in alternation_report
    assert "audit-gadget" in alternation_report
