"""Mapping evidence for canonical router marker-to-body spacing."""

from __future__ import annotations

from outcomeeng_testing.harnesses import instruction_block as harness


def test_canonical_router_spacing_for_all_harness_language_mappings() -> None:
    cases = harness.canonical_router_spacing_declarations()
    observations = harness.canonical_router_spacing_observations()

    assert len(observations) == len(cases)
    for case, observation in zip(cases, observations, strict=True):
        # "Exactly one blank line" is read off the rendered block rather than recomposed from
        # the separator the renderer used, so widening that separator fails here instead of
        # moving the expectation with it: one separator line short and the second element
        # carries body text, one line long and the remainder opens on another newline.
        marker_line, separator_line, body = observation.rendered.split("\n", 2)
        assert marker_line == observation.marker, case
        assert separator_line == "", case
        assert not body.startswith("\n"), case
        assert body != "", case
