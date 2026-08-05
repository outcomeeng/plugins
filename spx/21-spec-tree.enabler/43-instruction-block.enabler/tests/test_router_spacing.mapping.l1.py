"""Mapping evidence for canonical router marker-to-body spacing."""

from __future__ import annotations

from outcomeeng_testing.harnesses import instruction_block as harness


def test_canonical_router_spacing_for_all_harness_language_mappings() -> None:
    cases = harness.canonical_router_spacing_declarations()
    observations = harness.canonical_router_spacing_observations()

    assert len(observations) == len(cases)
    for case, observation in zip(cases, observations, strict=True):
        assert observation.rendered.startswith(observation.marker_and_separator), case
        body = observation.rendered.removeprefix(observation.marker_and_separator)
        assert not body.startswith(observation.unexpected_additional_separator), case
