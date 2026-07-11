"""Scenario evidence for source-directive parsing."""

from outcomeeng_testing.harnesses.source_and_templating import (
    custom_jinja_control_has_no_directives,
    implementation_is_ready,
    missing_directive_argument_raises,
    parse_empty_text_has_no_directives,
    parse_include_inside_prose,
    parse_mixed_directives_in_source_order,
    parse_plain_prose_has_no_directives,
    parse_reversed_directives_in_source_order,
    parse_single_include,
    parse_single_require_skill,
    standard_jinja_block_has_no_directives,
    standard_jinja_variable_has_no_directives,
    unknown_directive_raises,
)


def test_module_is_implemented() -> None:
    assert implementation_is_ready()


def test_empty_text_returns_empty_tuple() -> None:
    assert parse_empty_text_has_no_directives()


def test_plain_prose_returns_empty_tuple() -> None:
    assert parse_plain_prose_has_no_directives()


def test_single_include_returns_one_directive() -> None:
    assert parse_single_include()


def test_include_inside_prose_is_recognized() -> None:
    assert parse_include_inside_prose()


def test_single_require_skill_returns_one_directive() -> None:
    assert parse_single_require_skill()


def test_two_directives_returned_in_source_order() -> None:
    assert parse_mixed_directives_in_source_order()


def test_reverse_text_order_is_preserved() -> None:
    assert parse_reversed_directives_in_source_order()


def test_standard_block_syntax_is_ignored() -> None:
    assert standard_jinja_block_has_no_directives()


def test_standard_variable_syntax_is_ignored() -> None:
    assert standard_jinja_variable_has_no_directives()


def test_unknown_directive_name_raises() -> None:
    assert unknown_directive_raises()


def test_directive_missing_argument_raises() -> None:
    assert missing_directive_argument_raises()


def test_conditional_block_returns_no_directives() -> None:
    assert custom_jinja_control_has_no_directives()
