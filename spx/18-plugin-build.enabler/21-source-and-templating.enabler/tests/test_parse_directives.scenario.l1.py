"""Scenarios for parse_directives.

Verifies that parse_directives recognizes the build's directive vocabulary
in source-text form, returns directives in source order, ignores standard
Jinja2 syntax, and raises DirectiveSyntaxError on malformed directives.
"""

from __future__ import annotations

import pytest

from outcomeeng.scripts.build_plugins import (
    BLOCK_DELIMITER_END,
    BLOCK_DELIMITER_START,
    IMPLEMENTED,
    DirectiveSyntaxError,
    IncludeDirective,
    RequireSkillDirective,
    parse_directives,
)

if not IMPLEMENTED:
    pytest.skip(
        "outcomeeng.scripts.build_plugins is a stub — see spx/EXCLUDE",
        allow_module_level=True,
    )

EMPTY_TEXT = ""
PLAIN_PROSE = "# Heading\n\nJust prose, no directives."

INCLUDE_PATH = "samplelang/code-standards/fragment.md"
INCLUDE_DIRECTIVE_TEXT = (
    f"{BLOCK_DELIMITER_START} include '{INCLUDE_PATH}' {BLOCK_DELIMITER_END}"
)

SKILL_REF = "develop:standardizing-skills"
REQUIRE_SKILL_DIRECTIVE_TEXT = (
    f"{BLOCK_DELIMITER_START} require_skill '{SKILL_REF}' {BLOCK_DELIMITER_END}"
)

STANDARD_JINJA_BLOCK = "Code: {% if user %} ... {% endif %}"
STANDARD_JINJA_VARIABLE = "Variable: {{ user.name }}"

UNKNOWN_DIRECTIVE_TEXT = (
    f"{BLOCK_DELIMITER_START} unknown_directive 'arg' {BLOCK_DELIMITER_END}"
)


class TestParsesEmptyAndPlainText:
    """parse_directives returns an empty tuple when there are no directives."""

    def test_empty_text_returns_empty_tuple(self) -> None:
        assert parse_directives(EMPTY_TEXT) == ()

    def test_plain_prose_returns_empty_tuple(self) -> None:
        assert parse_directives(PLAIN_PROSE) == ()


class TestParsesIncludeDirective:
    """parse_directives recognizes include directives."""

    def test_single_include_returns_one_directive(self) -> None:
        result = parse_directives(INCLUDE_DIRECTIVE_TEXT)
        assert result == (IncludeDirective(path=INCLUDE_PATH),)

    def test_include_inside_prose_is_recognized(self) -> None:
        text = f"Before.\n{INCLUDE_DIRECTIVE_TEXT}\nAfter."
        result = parse_directives(text)
        assert result == (IncludeDirective(path=INCLUDE_PATH),)


class TestParsesRequireSkillDirective:
    """parse_directives recognizes require_skill directives."""

    def test_single_require_skill_returns_one_directive(self) -> None:
        result = parse_directives(REQUIRE_SKILL_DIRECTIVE_TEXT)
        assert result == (RequireSkillDirective(skill_ref=SKILL_REF),)


class TestParsesMultipleDirectivesInSourceOrder:
    """parse_directives preserves source order across mixed directive types."""

    def test_two_directives_returned_in_source_order(self) -> None:
        text = f"{INCLUDE_DIRECTIVE_TEXT}\n{REQUIRE_SKILL_DIRECTIVE_TEXT}"
        result = parse_directives(text)
        assert result == (
            IncludeDirective(path=INCLUDE_PATH),
            RequireSkillDirective(skill_ref=SKILL_REF),
        )

    def test_directives_in_reverse_text_order_returned_in_text_order(self) -> None:
        text = f"{REQUIRE_SKILL_DIRECTIVE_TEXT}\n{INCLUDE_DIRECTIVE_TEXT}"
        result = parse_directives(text)
        assert result == (
            RequireSkillDirective(skill_ref=SKILL_REF),
            IncludeDirective(path=INCLUDE_PATH),
        )


class TestIgnoresStandardJinjaSyntax:
    """Standard Jinja2 delimiters in content are not directives."""

    def test_standard_block_syntax_not_treated_as_directive(self) -> None:
        assert parse_directives(STANDARD_JINJA_BLOCK) == ()

    def test_standard_variable_syntax_not_treated_as_directive(self) -> None:
        assert parse_directives(STANDARD_JINJA_VARIABLE) == ()


class TestRaisesOnMalformedDirective:
    """parse_directives raises DirectiveSyntaxError when delimiters wrap an unknown name."""

    def test_unknown_directive_name_raises(self) -> None:
        with pytest.raises(DirectiveSyntaxError):
            parse_directives(UNKNOWN_DIRECTIVE_TEXT)
