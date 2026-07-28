"""Level-1 property evidence for `spx/32-distribution.enabler/21-bump.enabler/`."""

from __future__ import annotations

from outcomeeng.distribution.bump import (
    Segment,
    Version,
    bump_version,
    changed_plugins_from_diff,
)
from outcomeeng_testing.generators.bump import distribution_relpath, distribution_roots
from outcomeeng_testing.harnesses.bump import (
    BUMP_PROPERTY_REPLAY_PATH,
    BUMP_PROPERTY_SEED,
    observe_property_failure_notes,
    run_diff_path_list_property,
    run_distribution_path_property,
    run_single_diff_path_property,
)
from outcomeeng_testing.harnesses.bump_mapping import run_segment_increment_property


def _plugins_declared_by_spec(paths: list[str]) -> frozenset[str]:
    """Derive the declared plugin set from the spec's recognized-root rule.

    The spec names a path's segments: a change under a recognized root belongs
    to the plugin named by the segment that follows the root. Reading segments
    keeps this oracle independent of the string arithmetic the source performs.
    """
    roots = [tuple(root.split("/")) for root in distribution_roots()]
    plugins: set[str] = set()
    for path in paths:
        segments = tuple(path.split("/"))
        for root in roots:
            depth = len(root)
            if segments[:depth] != root or len(segments) <= depth:
                continue
            if segments[depth]:
                plugins.add(segments[depth])
            break
    return frozenset(plugins)


def test_segment_increment_property_holds() -> None:
    def check(version: Version, segment: Segment) -> None:
        bumped = bump_version(version, segment)
        if segment is Segment.PATCH:
            assert bumped == Version(version.major, version.minor, version.patch + 1)
        elif segment is Segment.MINOR:
            assert bumped == Version(version.major, version.minor + 1, 0)
        else:
            assert bumped == Version(version.major + 1, 0, 0)

    run_segment_increment_property(check)


def test_any_path_under_a_recognized_distribution_root_extracts_that_plugin() -> None:
    def check(root: str, plugin: str, subpath: str) -> None:
        path = distribution_relpath(root, plugin, subpath)
        assert changed_plugins_from_diff([path]) == frozenset({plugin})

    run_distribution_path_property(check)


def test_function_matches_spec_oracle_over_arbitrary_diff_paths() -> None:
    def check(path: str) -> None:
        assert changed_plugins_from_diff([path]) == _plugins_declared_by_spec([path])

    run_single_diff_path_property(check)


def test_aggregation_is_the_union_of_per_path_results() -> None:
    def check(paths: list[str]) -> None:
        per_path_union: frozenset[str] = frozenset()
        for path in paths:
            per_path_union = per_path_union | changed_plugins_from_diff([path])
        assert changed_plugins_from_diff(paths) == per_path_union

    run_diff_path_list_property(check)


def test_bump_property_failure_notes_include_seed_and_replay() -> None:
    notes = observe_property_failure_notes()

    assert f"Hypothesis seed: {BUMP_PROPERTY_SEED}" in notes
    assert f"Replay path: {BUMP_PROPERTY_REPLAY_PATH}" in notes
