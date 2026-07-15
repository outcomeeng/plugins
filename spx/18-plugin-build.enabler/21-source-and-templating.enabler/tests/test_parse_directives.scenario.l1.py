"""Scenario evidence for source-directive parsing."""

from outcomeeng_testing.harnesses.source_and_templating import (
    custom_jinja_controls_have_no_directives,
    implementation_is_ready,
    missing_directive_argument_raises,
    unknown_directive_raises,
)


def test_module_is_implemented() -> None:
    assert implementation_is_ready()


def test_unknown_directive_name_raises() -> None:
    assert unknown_directive_raises()


def test_directive_missing_argument_raises() -> None:
    assert missing_directive_argument_raises()


def test_jinja_control_blocks_return_no_directives() -> None:
    assert custom_jinja_controls_have_no_directives()
