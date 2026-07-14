"""Compliance evidence for router marker-to-body spacing."""

from __future__ import annotations

from outcomeeng_testing.harnesses import instruction_block as harness


def test_rendered_router_has_one_blank_line_before_body() -> None:
    assert harness.canonical_router_spacing_is_valid()
