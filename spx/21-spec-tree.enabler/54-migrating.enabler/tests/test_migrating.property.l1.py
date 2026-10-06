from __future__ import annotations

from outcomeeng_testing.harnesses.link_conversion import (
    ConversionPass,
    exercise_generated_trees,
)


def test_converting_a_converted_tree_changes_nothing() -> None:
    def verifies(first: ConversionPass, second: ConversionPass) -> None:
        assert first.observation.exit_code == 0
        assert second.observation.exit_code == 0
        assert second.files == first.files
        assert second.observation.rewritten == ()
        assert second.observation.unconvertible == first.observation.unconvertible

    exercise_generated_trees(verifies)
