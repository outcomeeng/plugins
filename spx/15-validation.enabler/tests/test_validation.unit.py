"""Unit tests for SKILL.md frontmatter validation.

Tests the validate-skill-frontmatter.py script against the assertions
in spx/15-validation.enabler/validation.md.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from outcomeeng.scripts.validate_skill_frontmatter import (
    STANDARD_FIELDS,
    get_valid_fields,
    main,
    validate_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_skill(tmp_path: Path, content: str, filename: str = "SKILL.md") -> Path:
    p = tmp_path / filename
    p.write_text(textwrap.dedent(content))
    return p


# ---------------------------------------------------------------------------
# Scenario: standard Agent Skills fields are accepted
# ---------------------------------------------------------------------------


def test_standard_fields_accepted(tmp_path: Path) -> None:
    skill = _write_skill(
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
    errors = validate_file(skill, STANDARD_FIELDS)
    assert errors == []


# ---------------------------------------------------------------------------
# Scenario: unknown field produces an error naming the field
# ---------------------------------------------------------------------------


def test_unknown_field_produces_error(tmp_path: Path) -> None:
    skill = _write_skill(
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
    errors = validate_file(skill, STANDARD_FIELDS)
    assert len(errors) == 1
    assert "foo-bar" in errors[0]


# ---------------------------------------------------------------------------
# Scenario: no frontmatter produces no errors
# ---------------------------------------------------------------------------


def test_no_frontmatter_no_errors(tmp_path: Path) -> None:
    skill = _write_skill(
        tmp_path,
        """\
        # Just markdown
        No frontmatter here.
        """,
    )
    errors = validate_file(skill, STANDARD_FIELDS)
    assert errors == []


# ---------------------------------------------------------------------------
# Scenario: non-SKILL.md files are skipped by main()
# ---------------------------------------------------------------------------


def test_non_skill_file_skipped(tmp_path: Path) -> None:
    _write_skill(
        tmp_path,
        """\
        ---
        name: test
        description: test
        totally-bogus: yes
        ---
        """,
        filename="README.md",
    )
    # Pass the non-SKILL.md file to main() — it should be filtered out,
    # producing exit code 0 (no errors) despite the bogus field.
    exit_code = main([str(tmp_path / "README.md")], valid_fields=STANDARD_FIELDS)
    assert exit_code == 0


# ---------------------------------------------------------------------------
# Scenario: fallback to standard fields when binary unavailable
# ---------------------------------------------------------------------------


def test_fallback_when_binary_missing() -> None:
    valid = get_valid_fields(binary_finder=lambda: None)
    assert valid == STANDARD_FIELDS


# ---------------------------------------------------------------------------
# Scenario: fallback to standard fields when extraction fails
# ---------------------------------------------------------------------------


def test_fallback_when_extraction_fails() -> None:
    valid = get_valid_fields(field_extractor=lambda _: None)
    assert valid == STANDARD_FIELDS
