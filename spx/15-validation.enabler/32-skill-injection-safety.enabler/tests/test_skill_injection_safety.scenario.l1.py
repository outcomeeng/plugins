"""Scenario evidence for SKILL.md injection-safety validation.

Spec: spx/15-validation.enabler/32-skill-injection-safety.enabler/skill-injection-safety.md

The discriminating value (the loader-executable fence token) is imported from the
source-owned module constant; the test never hardcodes the literal.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.validation.skill_injection_safety import (
    INJECTION_FENCE_TOKEN,
    main,
    scan_file,
    scan_paths,
)


def _write_skill(directory: Path, *, body: str, name: str = "SKILL.md") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def test_token_present_reports_file_and_line_and_exits_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Token placed on a known line; the expected line derives from construction.
    lines = ["# Heading", "", f"prose with {INJECTION_FENCE_TOKEN} inline", ""]
    skill = _write_skill(tmp_path, body="\n".join(lines))

    violations = scan_file(skill)
    assert [(v.path, v.line) for v in violations] == [(skill, 3)]

    exit_code = main([str(skill)])
    assert exit_code != 0
    out = capsys.readouterr().out
    assert str(skill) in out
    assert ":3" in out


def test_clean_skill_reports_no_error_and_exits_zero(tmp_path: Path) -> None:
    skill = _write_skill(tmp_path, body="# Heading\n\nplain prose, no fence\n")
    assert scan_file(skill) == []
    assert main([str(skill)]) == 0


def test_one_offender_among_many_is_named(tmp_path: Path) -> None:
    clean_a = _write_skill(tmp_path / "a", body="# A\n\nclean\n")
    offender = _write_skill(tmp_path / "b", body=f"# B\n\n{INJECTION_FENCE_TOKEN}\n")
    clean_c = _write_skill(tmp_path / "c", body="# C\n\nclean\n")

    violations = scan_paths([clean_a, offender, clean_c])
    assert [v.path for v in violations] == [offender]
    assert main([str(clean_a), str(offender), str(clean_c)]) != 0


def test_non_skill_basename_is_skipped(tmp_path: Path) -> None:
    # Contains the token but is not named SKILL.md.
    other = _write_skill(tmp_path, body=f"{INJECTION_FENCE_TOKEN}\n", name="README.md")
    assert scan_paths([other]) == []
    assert main([str(other)]) == 0
