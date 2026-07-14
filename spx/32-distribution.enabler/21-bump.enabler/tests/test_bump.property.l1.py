"""Level-1 property evidence for `spx/32-distribution.enabler/21-bump.enabler/`."""

from __future__ import annotations

from outcomeeng_testing.harnesses.bump import (
    any_path_under_recognized_distribution_root_extracts_that_plugin,
    bump_property_failure_notes_include_seed_and_replay,
    changed_plugin_aggregation_is_union_of_per_path_results,
    changed_plugins_match_spec_oracle_over_arbitrary_diff_paths,
)
from outcomeeng_testing.harnesses.bump_mapping import segment_increment_property_holds


def test_segment_increment_property_holds() -> None:
    assert segment_increment_property_holds()


def test_any_path_under_a_recognized_distribution_root_extracts_that_plugin() -> None:
    assert any_path_under_recognized_distribution_root_extracts_that_plugin()


def test_function_matches_spec_oracle_over_arbitrary_diff_paths() -> None:
    assert changed_plugins_match_spec_oracle_over_arbitrary_diff_paths()


def test_aggregation_is_the_union_of_per_path_results() -> None:
    assert changed_plugin_aggregation_is_union_of_per_path_results()


def test_bump_property_failure_notes_include_seed_and_replay() -> None:
    assert bump_property_failure_notes_include_seed_and_replay()
