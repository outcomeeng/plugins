"""Scenario evidence for recursive and conditional rendering."""

from outcomeeng_testing.harnesses.source_and_templating import (
    bound_target_variable_renders_each_target,
    cyclic_includes_raise,
    implementation_is_ready,
    nested_include_expands,
    nested_require_skill_expands,
    raw_directive_ships_literally,
)


def test_module_is_implemented() -> None:
    assert implementation_is_ready()


def test_include_nested_in_included_body_is_expanded() -> None:
    assert nested_include_expands()


def test_require_skill_nested_in_included_body_is_expanded() -> None:
    assert nested_require_skill_expands()


def test_mutually_referential_includes_raise() -> None:
    assert cyclic_includes_raise()


def test_bound_variable_is_substituted() -> None:
    assert bound_target_variable_renders_each_target()


def test_directive_inside_raw_block_ships_literally() -> None:
    assert raw_directive_ships_literally()
