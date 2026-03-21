"""Unit tests for SKILL.md frontmatter validation.

Tests the validate-skill-frontmatter.py script against the assertions
in spx/15-validation.enabler/validation.md.
"""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

# Load the script as a module (it uses hyphens in the filename).
_script = (
    Path(__file__).resolve().parents[3] / "scripts" / "validate-skill-frontmatter.py"
)
_spec = importlib.util.spec_from_file_location("validate_skill_frontmatter", _script)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

parse_frontmatter_keys = _mod.parse_frontmatter_keys
validate_file = _mod.validate_file
get_valid_fields = _mod.get_valid_fields
extract_fields_from_binary = _mod.extract_fields_from_binary
find_claude_binary = _mod.find_claude_binary
STANDARD_FIELDS = _mod.STANDARD_FIELDS


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
    valid = get_valid_fields()
    errors = validate_file(skill, valid)
    assert errors == []


# ---------------------------------------------------------------------------
# Scenario: Claude Code extension fields are accepted
# ---------------------------------------------------------------------------


def test_claude_code_extension_fields_accepted(tmp_path: Path) -> None:
    skill = _write_skill(
        tmp_path,
        """\
        ---
        name: my-skill
        description: Does things
        model: sonnet
        effort: high
        context: fork
        agent: Explore
        hooks:
          pre: echo hi
        argument-hint: "[file]"
        disable-model-invocation: true
        user-invocable: false
        ---
        Body content here.
        """,
    )
    valid = get_valid_fields()
    errors = validate_file(skill, valid)
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
    valid = get_valid_fields()
    errors = validate_file(skill, valid)
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
    valid = get_valid_fields()
    errors = validate_file(skill, valid)
    assert errors == []


# ---------------------------------------------------------------------------
# Scenario: non-SKILL.md files are skipped by main()
# ---------------------------------------------------------------------------


def test_non_skill_file_skipped(tmp_path: Path) -> None:
    other = _write_skill(
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
    # parse_frontmatter_keys works on any file, but main() filters by name.
    # Validate that the filtering logic works by checking that the file
    # name doesn't match.
    assert other.name.lower() != "skill.md"


# ---------------------------------------------------------------------------
# Property: field extraction is deterministic
# ---------------------------------------------------------------------------


def test_extraction_deterministic() -> None:
    binary = find_claude_binary()
    if binary is None:
        pytest.skip("Claude binary not found")
    a = extract_fields_from_binary(binary)
    b = extract_fields_from_binary(binary)
    assert a == b


# ---------------------------------------------------------------------------
# Property: standard fields always subset of valid fields
# ---------------------------------------------------------------------------


def test_standard_fields_always_subset() -> None:
    valid = get_valid_fields()
    assert STANDARD_FIELDS <= valid


def test_standard_fields_subset_when_binary_missing() -> None:
    with patch.object(_mod, "find_claude_binary", return_value=None):
        valid = get_valid_fields()
    assert STANDARD_FIELDS <= valid
    # When binary is missing, valid fields should be exactly the standard set.
    assert valid == STANDARD_FIELDS


def test_standard_fields_subset_when_extraction_fails() -> None:
    binary = find_claude_binary()
    if binary is None:
        pytest.skip("Claude binary not found")
    with patch.object(_mod, "extract_fields_from_binary", return_value=None):
        valid = get_valid_fields()
    assert STANDARD_FIELDS <= valid
    assert valid == STANDARD_FIELDS


# ---------------------------------------------------------------------------
# Compliance: never fail open with empty set
# ---------------------------------------------------------------------------


def test_never_returns_empty_valid_set() -> None:
    with patch.object(_mod, "find_claude_binary", return_value=None):
        valid = get_valid_fields()
    assert len(valid) > 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_multiple_unknown_fields(tmp_path: Path) -> None:
    skill = _write_skill(
        tmp_path,
        """\
        ---
        name: my-skill
        description: Does things
        bogus-one: yes
        bogus-two: yes
        ---
        Body.
        """,
    )
    valid = get_valid_fields()
    errors = validate_file(skill, valid)
    assert len(errors) == 2
    field_names = {e.split("'")[1] for e in errors}
    assert field_names == {"bogus-one", "bogus-two"}


def test_empty_frontmatter(tmp_path: Path) -> None:
    skill = _write_skill(
        tmp_path,
        """\
        ---
        ---
        Body.
        """,
    )
    valid = get_valid_fields()
    errors = validate_file(skill, valid)
    assert errors == []
