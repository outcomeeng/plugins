"""Conformance evidence for post-compact continuity configuration."""

from outcomeeng_testing.harnesses.compact_continuity import (
    compact_prompt_contains_state_schema_sections,
    compact_prompt_omits_imperative_sections,
    compact_prompt_omits_skill_invocations,
    compact_prompt_uses_marker_trigger,
)


def test_compact_prompt_contains_state_schema_sections() -> None:
    assert compact_prompt_contains_state_schema_sections()


def test_compact_prompt_uses_marker_trigger() -> None:
    assert compact_prompt_uses_marker_trigger()


def test_compact_prompt_omits_imperative_sections() -> None:
    assert compact_prompt_omits_imperative_sections()


def test_compact_prompt_omits_skill_invocations() -> None:
    assert compact_prompt_omits_skill_invocations()
