"""Scenario evidence for SKILL.md injection-safety validation.

Spec: spx/15-validation.enabler/32-skill-injection-safety.enabler/skill-injection-safety.md

The discriminating values (the loader-executable fence token, the inline injection
markers, and the path pieces that make a command read sister-skill content) are
imported from the source-owned module; the test never hardcodes the literals.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.validation.skill_injection_safety import (
    INJECTION_FENCE_TOKEN,
    PARENT_DIRECTORY_SEGMENT,
    SKILL_FILENAME,
    ViolationKind,
    main,
    scan_file,
    scan_paths,
)
from outcomeeng_testing.harnesses.skill_injection_safety import (
    inline_injection,
    write_skill,
)


def test_token_present_reports_file_and_line_and_exits_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Token placed on a known line; the expected line derives from construction.
    lines = ["# Heading", "", f"prose with {INJECTION_FENCE_TOKEN} inline", ""]
    skill = write_skill(tmp_path, body="\n".join(lines))

    violations = scan_file(skill)
    assert [(v.path, v.line) for v in violations] == [(skill, 3)]

    exit_code = main([str(skill)])
    assert exit_code != 0
    out = capsys.readouterr().out
    assert str(skill) in out
    assert ":3" in out


def test_clean_skill_reports_no_error_and_exits_zero(tmp_path: Path) -> None:
    skill = write_skill(tmp_path, body="# Heading\n\nplain prose, no fence\n")
    assert scan_file(skill) == []
    assert main([str(skill)]) == 0


def test_one_offender_among_many_is_named(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    clean_a = write_skill(tmp_path / "a", body="# A\n\nclean\n")
    offender = write_skill(tmp_path / "b", body=f"# B\n\n{INJECTION_FENCE_TOKEN}\n")
    clean_c = write_skill(tmp_path / "c", body="# C\n\nclean\n")

    violations = scan_paths([clean_a, offender, clean_c])
    assert [v.path for v in violations] == [offender]

    assert main([str(clean_a), str(offender), str(clean_c)]) != 0
    reported = capsys.readouterr().out.splitlines()
    assert [line.split(":", 1)[0] for line in reported] == [str(offender)]


def test_non_skill_basename_is_skipped(tmp_path: Path) -> None:
    # Contains the token but is not named SKILL.md.
    other = write_skill(tmp_path, body=f"{INJECTION_FENCE_TOKEN}\n", name="README.md")
    assert scan_paths([other]) == []
    assert main([str(other)]) == 0


@pytest.mark.parametrize(
    "command",
    [
        f"cat {PARENT_DIRECTORY_SEGMENT}sibling/{SKILL_FILENAME}",
        f"cat {PARENT_DIRECTORY_SEGMENT}sibling/references/topic.md",
        f"cat {SKILL_FILENAME}",
    ],
)
def test_sister_skill_injection_reports_file_and_line_and_exits_nonzero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
) -> None:
    lines = ["# Heading", "", f"Context: {inline_injection(command)}", ""]
    skill = write_skill(tmp_path, body="\n".join(lines))

    violations = scan_file(skill)
    assert [(v.path, v.line, v.kind) for v in violations] == [
        (skill, 3, ViolationKind.SISTER_SKILL_INJECTION)
    ]

    assert main([str(skill)]) != 0
    out = capsys.readouterr().out
    assert f"{skill}:3" in out


def test_own_skill_injection_is_accepted(tmp_path: Path) -> None:
    body = f"# Heading\n\nBranch: {inline_injection('git branch --show-current')}\n"
    skill = write_skill(tmp_path, body=body)
    assert scan_file(skill) == []
    assert main([str(skill)]) == 0
