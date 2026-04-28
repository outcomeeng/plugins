"""Level 1 scenario tests for SKILL.md frontmatter validation.

Tests the validate_skill_frontmatter.py wrapper and the vendored
quick_validate.py against the assertions in
[skill-frontmatter.md](../skill-frontmatter.md).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from outcomeeng.scripts.validate_skill_frontmatter import (
    main,
    validate_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_skill(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "SKILL.md"
    p.write_text(textwrap.dedent(content))
    return p


# ---------------------------------------------------------------------------
# Scenario: standard Agent Skills fields are accepted
# ---------------------------------------------------------------------------


def test_standard_fields_accepted(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        """\
        ---
        name: my-skill
        description: Does things
        license: MIT
        compatibility: Claude Code
        metadata:
          author: test
        allowed-tools: Read Grep
        ---
        Body content here.
        """,
    )
    errors = validate_file(tmp_path / "SKILL.md")
    assert errors == []


# ---------------------------------------------------------------------------
# Scenario: Claude Code-specific field is accepted
# ---------------------------------------------------------------------------


def test_claude_code_field_accepted(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        """\
        ---
        name: my-skill
        description: Does things
        disable-model-invocation: true
        ---
        Body.
        """,
    )
    errors = validate_file(tmp_path / "SKILL.md")
    assert errors == []


# ---------------------------------------------------------------------------
# Scenario: unknown field produces an error naming the field
# ---------------------------------------------------------------------------


def test_unknown_field_produces_error(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        """\
        ---
        name: my-skill
        description: Does things
        foo-bar: invalid
        ---
        Body.
        """,
    )
    errors = validate_file(tmp_path / "SKILL.md")
    assert len(errors) == 1
    assert "foo-bar" in errors[0]


# ---------------------------------------------------------------------------
# Scenario: non-kebab-case name produces an error
# ---------------------------------------------------------------------------


def test_bad_name_format_produces_error(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        """\
        ---
        name: My Skill
        description: Does things
        ---
        Body.
        """,
    )
    errors = validate_file(tmp_path / "SKILL.md")
    assert len(errors) == 1
    assert "My Skill" in errors[0]


# ---------------------------------------------------------------------------
# Scenario: angle brackets in description produce an error
# ---------------------------------------------------------------------------


def test_angle_brackets_in_description_produces_error(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        """\
        ---
        name: my-skill
        description: Use <tags> for things
        ---
        Body.
        """,
    )
    errors = validate_file(tmp_path / "SKILL.md")
    assert len(errors) == 1
    assert "angle bracket" in errors[0].lower()


# ---------------------------------------------------------------------------
# Scenario: no frontmatter produces an error
# ---------------------------------------------------------------------------


def test_no_frontmatter_produces_error(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        """\
        # Just markdown
        No frontmatter here.
        """,
    )
    errors = validate_file(tmp_path / "SKILL.md")
    assert len(errors) == 1
    assert "frontmatter" in errors[0].lower()


# ---------------------------------------------------------------------------
# Scenario: non-SKILL.md files are skipped by main()
# ---------------------------------------------------------------------------


def test_non_skill_file_skipped(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        textwrap.dedent("""\
        ---
        name: test
        description: test
        totally-bogus: yes
        ---
        """),
    )
    exit_code = main([str(readme)])
    assert exit_code == 0
