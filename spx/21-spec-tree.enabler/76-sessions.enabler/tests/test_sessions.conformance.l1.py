"""Conformance evidence for post-compact continuity configuration."""

from outcomeeng_testing.harnesses.compact_continuity import compact_prompt_is_undefined


def test_compact_prompt_is_undefined() -> None:
    assert compact_prompt_is_undefined()
