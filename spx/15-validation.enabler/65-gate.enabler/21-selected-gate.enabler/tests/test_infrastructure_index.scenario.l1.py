"""Scenario evidence for transitive reach in the static import index."""

from __future__ import annotations

from outcomeeng_testing.harnesses.infrastructure_index import (
    synthetic_repository,
    transitive_layout,
)


def test_generator_reached_through_harness_reaches_the_importing_test() -> None:
    with synthetic_repository() as repo:
        layout = transitive_layout(repo)

    assert layout.harness in layout.index.dependents(layout.generator)
    assert layout.index.reaching_tests(layout.generator) == (layout.test,)
