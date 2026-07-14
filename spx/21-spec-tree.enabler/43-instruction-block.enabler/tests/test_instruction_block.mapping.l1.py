"""Mapping evidence for the instruction-block render model."""

from __future__ import annotations

from outcomeeng_testing.harnesses import instruction_block as harness


def test_extension_maps_to_language() -> None:
    harness.assert_extension_to_language_mapping()


def test_detected_language_set_is_the_mapped_extensions() -> None:
    harness.assert_detected_language_set_mapping()


def test_language_block_appears_iff_enabled() -> None:
    harness.assert_language_block_filter_mapping()


def test_check_maps_router_state_to_report() -> None:
    harness.assert_router_status_mapping()


def test_check_maps_shared_region_state_to_report() -> None:
    harness.assert_shared_region_status_mapping()


def test_topology_maps_to_bootstrap_outcome() -> None:
    harness.assert_bootstrap_topology_mapping()


def test_span_ratio_maps_to_wrap_decision() -> None:
    harness.assert_span_ratio_wrap_mapping()
