"""Mapping evidence for canonical router marker-to-body spacing."""

from __future__ import annotations

from outcomeeng_testing.harnesses import instruction_block as harness


def test_canonical_router_spacing_for_all_harness_language_mappings() -> None:
    observations = harness.canonical_router_spacing_observations()
    assert observations
    for observation in observations:
        assert observation.rendered.startswith(observation.marker_and_separator)
        assert not observation.rendered.removeprefix(
            observation.marker_and_separator
        ).startswith(observation.unexpected_additional_separator)
