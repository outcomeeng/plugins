"""Scenario evidence for source-directive parsing."""

from outcomeeng_testing.harnesses.source_and_templating import (
    custom_jinja_control_has_no_directives,
    implementation_is_ready,
    missing_directive_argument_raises,
    standard_jinja_block_has_no_directives,
    standard_jinja_variable_has_no_directives,
    unknown_directive_raises,
)


def test_module_is_implemented() -> None:
    assert implementation_is_ready()


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
