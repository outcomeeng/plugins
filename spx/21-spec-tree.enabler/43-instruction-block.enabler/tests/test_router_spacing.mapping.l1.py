"""Mapping evidence for canonical router marker-to-body spacing."""

from __future__ import annotations

from outcomeeng_testing.harnesses import instruction_block as harness


def test_canonical_router_spacing_for_all_harness_language_mappings() -> None:
    assert (
        harness.canonical_router_spacing_evidence_run().executed
        == harness.canonical_router_spacing_declarations()
    )
